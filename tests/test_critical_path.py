import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
from src.lib.db_executor import DBExecutor
from src.lib.sql_processor import SQLProcessor
from src.lib.ollama_client import OllamaClient

def test_db_executor_success():
    """Prueba que el motor de base de datos puede ejecutar y parsear SQL simple."""
    # SQLite en memoria por defecto
    executor = DBExecutor("sqlite:///:memory:")
    # Creamos una tabla e insertamos datos
    executor.execute_to_df("CREATE TABLE tests (id INTEGER, val TEXT);")
    executor.execute_to_df("INSERT INTO tests VALUES (1, 'Hola');")
    
    # Probamos leer los datos
    df = executor.execute_to_df("SELECT * FROM tests;")
    assert len(df) == 1
    assert df.iloc[0]["val"] == "Hola"

def test_db_executor_syntax_error():
    """Prueba que los errores de sintaxis lanzan excepciones de SQLAlchemy capturables."""
    import sqlalchemy
    executor = DBExecutor("sqlite:///:memory:")
    with pytest.raises(sqlalchemy.exc.OperationalError):
        executor.execute_to_df("SELECT * FROM tabla_inexistente WHERE x = 1;")

@patch("requests.post")
def test_ollama_client_handles_404(mock_post):
    """Asegura que un 404 por falta de modelo devuelve el mensaje detallado."""
    mock_post.return_value = MagicMock(status_code=404, text='{"error":"model no existe"}')
    client = OllamaClient()
    
    with pytest.raises(Exception) as exc_info:
        client.call_generate("Hola")
    
    assert "HTTP Error 404" in str(exc_info.value)

    assert "model no existe" in str(exc_info.value)

def test_mermaid_generation_critical():
    """Prueba la generación de grafos ER que usa la interfaz."""
    schema = {
        "User": {
            "columns": [{"name": "id", "type": "INT"}, {"name": "name", "type": "TEXT"}],
            "primary_key": ["id"],
            "foreign_keys": []
        }
    }
    mermaid = SQLProcessor.schema_to_mermaid(schema)
    assert "User {" in mermaid
    assert "INT id PK" in mermaid
