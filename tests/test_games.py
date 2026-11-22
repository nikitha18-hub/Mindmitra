from app import create_app


def test_game_session_saved():
    app = create_app()
    app.config["TESTING"] = True
    client = app.test_client()
    response = client.post(
        "/api/games/picture-match/session",
        json={"score": 100, "difficulty": 2},
    )
    assert response.status_code == 201
    assert response.get_json()["score"] == 100