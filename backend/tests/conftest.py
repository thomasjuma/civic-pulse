from agents.tracing import set_tracing_disabled


def pytest_configure() -> None:
    set_tracing_disabled(True)
