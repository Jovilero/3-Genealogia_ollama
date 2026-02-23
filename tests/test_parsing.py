import pytest
from src.main import parse_schema_local

def test_parse_schema_local_basic():
    sql = """
    CREATE TABLE users (
        id INT PRIMARY KEY,
        name VARCHAR(100)
    );
    """
    schema = parse_schema_local(sql)
    assert "users" in schema
    assert schema["users"]["primary_key"] == ["id"]
    assert len(schema["users"]["columns"]) == 2
    assert schema["users"]["columns"][0]["name"] == "id"

def test_parse_schema_local_with_fk():
    sql = """
    CREATE TABLE orders (
        order_id INT PRIMARY KEY,
        user_id INT,
        FOREIGN KEY (user_id) REFERENCES users(id)
    );
    """
    schema = parse_schema_local(sql)
    assert "orders" in schema
    assert len(schema["orders"]["foreign_keys"]) == 1
    fk = schema["orders"]["foreign_keys"][0]
    assert fk["columns"] == ["user_id"]
    assert fk["ref_table"] == "users"
    assert fk["ref_columns"] == ["id"]

def test_parse_schema_local_empty():
    assert parse_schema_local("") == {}
