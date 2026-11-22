import pytest

from app import create_app


@pytest.fixture()
def client():
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


@pytest.mark.parametrize(
    ("path", "status"),
    [
        ("/", 200),
        ("/login", 200),
        ("/patient", 200),
        ("/dashboard", 200),
        ("/caregiver", 200),
        ("/games", 200),
        ("/memory-map", 200),
        ("/memory-library", 200),
        ("/reminders", 200),
        ("/impact", 200),
    ],
)
def test_page_routes(client, path, status):
    response = client.get(path)
    assert response.status_code == status


def test_index_extends_shared_layout(client):
    response = client.get("/")
    page = response.get_data(as_text=True)

    assert "Skip to main content" in page
    assert "Calm Mode" in page
    assert "Patient Mode" in page