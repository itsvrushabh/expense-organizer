import asyncio
from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import categories, currencies, expenses
from services.currency_service import start_currency_sync_worker
import storage

logger = logging.getLogger("expense_backend.main")


@asynccontextmanager
async def lifespan(application: FastAPI):
    # Initialize database, views, and functions
    await storage.init_db()

    # Start 24-hour background currency exchange auto-sync task
    sync_task = asyncio.create_task(start_currency_sync_worker())

    yield

    # Cancel background sync worker cleanly on shutdown
    sync_task.cancel()
    try:
        await sync_task
    except asyncio.CancelledError:
        pass

    # Close DB connection pool
    await storage.close_db()


def create_app() -> FastAPI:
    application = FastAPI(title="Expense Organizer", version="1.0.0", lifespan=lifespan)

    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.include_router(expenses.router)
    application.include_router(currencies.router)
    application.include_router(categories.router)

    @application.get("/health")
    async def health():
        return {
            "status": "healthy",
            "database": "postgresql" if storage.is_db_connected() else "in_memory",
        }

    @application.get("/")
    async def root():
        return {
            "message": "Expense Organizer API",
            "version": "2.0.0",
            "endpoints": {
                "health": "GET /health",
                "currencies": "GET /currencies",
                "refresh_currencies": "POST /currencies/refresh",
                "categories": "GET /categories",
                "create_category": "POST /categories",
                "add_expense": "POST /expenses",
                "all_expenses": "GET /expenses",
                "combined_summary": "GET /expenses/summary",
                "day_expenses": "GET /expenses/day/{date}",
                "week_expenses": "GET /expenses/week/{year}/{week}",
                "week_date_expenses": "GET /expenses/week/date/{date}",
                "month_expenses": "GET /expenses/month/{year}/{month}",
                "year_expenses": "GET /expenses/year/{year}",
                "category_expenses": "GET /expenses/category/{category}",
                "update_expense": "PUT /expenses/{id}",
                "delete_expense": "DELETE /expenses/{id}",
            },
        }

    return application


app = create_app()

if __name__ == "__main__":
    import os
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
