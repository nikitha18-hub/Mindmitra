from werkzeug.security import check_password_hash, generate_password_hash

from app import create_app
from app.database import get_db


def test_password_hashing(tmp_path):
    app = create_app(f"sqlite:///{tmp_path/'test.db'}")
    app.config["TESTING"] = True
    with app.app_context():
        connection = get_db(app)
        password_hash = generate_password_hash("correct")
        connection.execute(
            "INSERT INTO users (name, username, password_hash, role) VALUES (?, ?, ?, ?)",
            ("Test Patient", "patient", password_hash, "patient"),
        )
        connection.commit()
        user = connection.execute(
            "SELECT * FROM users WHERE username = 'patient'"
        ).fetchone()
        assert check_password_hash(user["password_hash"], "correct")
        assert not check_password_hash(user["password_hash"], "wrong")
        connection.close()
