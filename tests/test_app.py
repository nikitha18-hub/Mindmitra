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
        ("/register", 200),
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


def test_health_endpoint(client):
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.get_json()["status"] == "ok"


def test_production_requires_secret(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.delenv("SECRET_KEY", raising=False)
    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        create_app()


def test_caregiver_api_requires_role_without_session():
    app = create_app()
    app.config["TESTING"] = False
    test_client = app.test_client()
    with test_client.session_transaction() as user_session:
        user_session["csrf_token"] = "test-token"
    response = test_client.post(
        "/api/mindmap/nodes",
        json={"label": "Garden", "patient_id": 1},
        headers={"X-CSRF-Token": "test-token"},
    )
    assert response.status_code == 403


def test_login_accepts_demo_caregiver(tmp_path):
    app = create_app(f"sqlite:///{tmp_path/'auth.db'}")
    app.config["TESTING"] = False
    test_client = app.test_client()
    with test_client.session_transaction() as user_session:
        user_session["csrf_token"] = "test-token"
    from seed_demo import seed_demo
    with app.app_context():
        seed_demo(app)
    response = test_client.post(
        "/login",
        data={
            "username": "meera",
            "password": "demo",
            "csrf_token": "test-token",
        },
    )
    assert response.status_code == 302


def test_registration_creates_patient(tmp_path):
    app = create_app(f"sqlite:///{tmp_path/'registration.db'}")
    app.config["TESTING"] = False
    test_client = app.test_client()
    with test_client.session_transaction() as user_session:
        user_session["csrf_token"] = "test-token"
    response = test_client.post(
        "/register",
        data={
            "name": "Test Patient",
            "username": "testpatient",
            "password": "securepass",
            "csrf_token": "test-token",
        },
    )
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/patient")