import main


def test_app_metadata():
    assert main.app.title == "Expense Organizer"
    assert main.app.version == "1.0.0"
