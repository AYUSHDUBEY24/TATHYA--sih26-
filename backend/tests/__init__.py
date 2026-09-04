"""Backend test package.

Declared so pytest imports ``tests.conftest`` / ``tests.test_documents`` under
the canonical package names, ensuring exactly one module instance (and thus one
in-memory SQLAlchemy engine) is shared across fixtures and test helpers.
"""