import pytest
import sqlite3
from werkzeug.security import generate_password_hash

from app import create_app
from app.database import get_db


@pytest.fixture()
def client(tmp_path):
    app = create_app(f"sqlite:///{tmp_path/'mindmap.db'}")
    app.config.update(TESTING=True)
    with app.app_context():
        connection = get_db(app)
        connection.execute(
            "INSERT INTO users (name, username, password_hash, role) VALUES (?, ?, ?, ?)",
            ("Asha", "asha", generate_password_hash("demo"), "patient"),
        )
        connection.commit()
        connection.close()
    return app.test_client()


def test_mindmap_create_read_delete(client):
    created = client.post("/api/mindmap/nodes", json={
        "patient_id": 1,
        "label": "Garden",
        "category": "Places",
        "description": "Jasmine and evening light.",
    })
    assert created.status_code == 201
    node_id = created.get_json()["id"]

    read = client.get("/api/mindmap/1")
    assert read.status_code == 200
    assert "Garden" in [node["label"] for node in read.get_json()["nodes"]]

    deleted = client.delete(f"/api/mindmap/nodes/{node_id}")
    assert deleted.status_code == 200