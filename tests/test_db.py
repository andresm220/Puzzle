import pytest
from unittest.mock import patch, MagicMock


def test_get_driver_raises_without_env(monkeypatch):
    monkeypatch.delenv("NEO4J_URI", raising=False)
    monkeypatch.delenv("NEO4J_USER", raising=False)
    monkeypatch.delenv("NEO4J_USERNAME", raising=False)
    monkeypatch.delenv("NEO4J_PASSWORD", raising=False)
    import importlib
    import db
    with patch("db.load_dotenv"):
        with patch("db.os.getenv", return_value=None):
            importlib.reload(db)
            with pytest.raises(RuntimeError, match="NEO4J_URI"):
                db.get_driver()


def test_get_driver_returns_driver(monkeypatch):
    monkeypatch.setenv("NEO4J_URI", "bolt://localhost")
    monkeypatch.setenv("NEO4J_USER", "neo4j")
    monkeypatch.setenv("NEO4J_PASSWORD", "test")
    import importlib
    import db
    with patch("db.load_dotenv"):
        importlib.reload(db)
        with patch("db.GraphDatabase.driver") as mock_driver:
            mock_driver.return_value = MagicMock()
            result = db.get_driver()
            assert result is not None
            mock_driver.assert_called_once_with("bolt://localhost", auth=("neo4j", "test"))
