import io

from app import create_app


def test_upload_rejects_bad_extension():
    app = create_app()
    app.config["TESTING"] = True
    client = app.test_client()
    response = client.post(
        "/api/upload",
        data={"file": (io.BytesIO(b"not-an-image"), "document.txt")},
        content_type="multipart/form-data",
    )
    assert response.status_code == 400