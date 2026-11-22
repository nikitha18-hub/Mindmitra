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


def test_mindmap_update_persists(client):
    created = client.post("/api/mindmap/nodes", json={
        "patient_id": 1,
        "label": "Old Name",
        "category": "Family",
        "description": "Old description.",
    })
    assert created.status_code == 201
    node_id = created.get_json()["id"]

    updated = client.put(f"/api/mindmap/nodes/{node_id}", json={
        "label": "Meera",
        "category": "Family",
        "description": "Updated description.",
    })
    assert updated.status_code == 200

    read = client.get("/api/mindmap/1")
    node = next(item for item in read.get_json()["nodes"] if item["id"] == node_id)
    assert node["label"] == "Meera"
    assert node["description"] == "Updated description."


def test_mindmap_edge_create_delete(client):
    first = client.post("/api/mindmap/nodes", json={
        "patient_id": 1, "label": "Garden", "category": "Places",
    })
    second = client.post("/api/mindmap/nodes", json={
        "patient_id": 1, "label": "Meera", "category": "Family",
    })
    edge = client.post("/api/mindmap/edges", json={
        "patient_id": 1,
        "source": first.get_json()["id"],
        "target": second.get_json()["id"],
    })
    assert edge.status_code == 201
    deleted = client.delete(f"/api/mindmap/edges/{edge.get_json()['id']}")
    assert deleted.status_code == 200