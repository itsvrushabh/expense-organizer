from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import expenses


def create_app() -> FastAPI:
    application = FastAPI(title="Expense Organizer", version="1.0.0")

    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.include_router(expenses.router)

    @application.get("/")
    async def root():
        return {
            "message": "Expense Organizer API",
            "endpoints": {
                "add_expense": "POST /expenses",
                "all_expenses": "GET /expenses",
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
