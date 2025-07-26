import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def test_create_initial_state_sets_level(monkeypatch):
    for var in [
        "SLACK_BOT_TOKEN",
        "SLACK_SIGNING_SECRET",
        "SERPAPI_KEY",
        "GEMINI_API_KEY",
        "GOOGLE_SHEET_ID",
    ]:
        monkeypatch.setenv(var, "x")

    class DummyApp:
        def __init__(self, *a, **k):
            pass

        def event(self, *a, **k):
            def wrapper(func):
                return func
            return wrapper

        def action(self, *a, **k):
            def wrapper(func):
                return func
            return wrapper

    monkeypatch.setattr("slack_bolt.App", DummyApp)
    monkeypatch.setattr(
        "slack_bolt.adapter.google_cloud_functions.SlackRequestHandler",
        lambda app: object(),
    )
    monkeypatch.setattr("handlers.actions.register_actions", lambda app: None)

    import importlib
    monkeypatch.setattr("users.load_user_levels", lambda: {"U1": "C-Level"})
    main = importlib.import_module("main")
    importlib.reload(main)
    state = main.create_initial_state("U1")
    assert state["level"] == "C-Level"
    assert state["data"] == {}
    assert state["step"] == 0
