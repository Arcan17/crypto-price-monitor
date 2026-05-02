import os


def pytest_configure(config):
    """Override DATABASE_URL before Django loads settings, so tests use SQLite locally."""
    os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
