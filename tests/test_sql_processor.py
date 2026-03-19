import pytest
from src.lib.sql_processor import SQLProcessor

def test_parse_schema_local_simple():
    sql = """
    CREATE TABLE Personas (
        id INT PRIMARY KEY,
        nombre VARCHAR(100),
        edad INT,
        CONSTRAINT pk_personas PRIMARY KEY (id)
    );
    """
    schema = SQLProcessor.parse_schema_local(sql)
    assert "Personas" in schema
    table = schema["Personas"]
    # columns should include id, nombre, edad
    col_names = {c["name"] for c in table["columns"]}
    assert {"id", "nombre", "edad"}.issubset(col_names)
    # primary_key should include id
    assert "id" in table["primary_key"]

def test_schema_to_mermaid():
    schema = {
        "Users": {
            "columns": [{"name": "id", "type": "INT"}, {"name": "name", "type": "VARCHAR"}],
            "primary_key": ["id"],
            "foreign_keys": []
        },
        "Posts": {
            "columns": [{"name": "id", "type": "INT"}, {"name": "user_id", "type": "INT"}],
            "primary_key": ["id"],
            "foreign_keys": [{"columns": ["user_id"], "ref_table": "Users", "ref_columns": ["id"]}]
        }
    }
    mermaid_str = SQLProcessor.schema_to_mermaid(schema)
    
    assert "erDiagram" in mermaid_str
    assert "Users {" in mermaid_str
    assert "Posts {" in mermaid_str
    assert "Users ||--o{ Posts : \"user_id\"" in mermaid_str
    assert "INT id PK" in mermaid_str
    assert "INT user_id FK" in mermaid_str
