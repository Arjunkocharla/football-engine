from football_engine.main import app


def test_app_boots() -> None:
    assert app.title == "football-engine"
