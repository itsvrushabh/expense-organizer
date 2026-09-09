import re
from pathlib import Path

from main import app


def test_openapi_schema_contract_contains_core_models():
    """
    Contract test ensuring FastAPI generates all necessary OpenAPI schemas
    matching frontend and mobile expectations.
    """
    schema = app.openapi()
    schemas = schema.get("components", {}).get("schemas", {})

    assert "Expense" in schemas
    assert "ExpenseCreate" in schemas
    assert "ExpenseSummary" in schemas
    assert "Category" in schemas
    assert "Currency" in schemas

    # Verify Expense properties
    expense_props = schemas["Expense"].get("properties", {})
    for required_prop in ["id", "description", "amount", "category", "date"]:
        assert required_prop in expense_props, (
            f"Missing required property {required_prop} in Expense schema"
        )

    # Verify Category properties
    cat_props = schemas["Category"].get("properties", {})
    for required_prop in ["id", "name", "icon", "color", "is_active"]:
        assert required_prop in cat_props, (
            f"Missing required property {required_prop} in Category schema"
        )

    # Verify Currency properties
    curr_props = schemas["Currency"].get("properties", {})
    for required_prop in ["code", "name", "symbol", "exchange_rate"]:
        assert required_prop in curr_props, (
            f"Missing required property {required_prop} in Currency schema"
        )


def test_frontend_types_contract_sync():
    """
    Verifies that frontend/src/types.ts contains all fields present in backend OpenAPI schema.
    """
    schema = app.openapi()
    schemas = schema.get("components", {}).get("schemas", {})
    types_file = Path(__file__).resolve().parent.parent.parent / "frontend" / "src" / "types.ts"
    assert types_file.exists(), f"Frontend types.ts not found at {types_file}"

    types_content = types_file.read_text()

    # Verify Expense fields in frontend
    expense_props = schemas["Expense"].get("properties", {})
    for prop in expense_props.keys():
        assert re.search(rf"\b{prop}\??\s*:", types_content), (
            f"Field '{prop}' from backend Expense schema is missing in frontend/src/types.ts"
        )

    # Verify Category fields in frontend
    category_props = schemas["Category"].get("properties", {})
    for prop in category_props.keys():
        assert re.search(rf"\b{prop}\??\s*:", types_content), (
            f"Field '{prop}' from backend Category schema is missing in frontend/src/types.ts"
        )


def test_mobile_models_contract_sync():
    """
    Verifies that mobile/lib/models/expense.dart contains core backend fields.
    """
    mobile_expense_file = (
        Path(__file__).resolve().parent.parent.parent / "mobile" / "lib" / "models" / "expense.dart"
    )
    assert mobile_expense_file.exists(), f"Mobile expense.dart not found at {mobile_expense_file}"

    content = mobile_expense_file.read_text()
    for field in ["id", "description", "amount", "category", "date"]:
        assert re.search(rf"final\s+\w+\s+{field}\b", content), (
            f"Field '{field}' is missing in mobile/lib/models/expense.dart"
        )
