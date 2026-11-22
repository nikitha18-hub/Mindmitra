import os
from datetime import datetime, timezone

from flask import (
    jsonify,
    redirect,
    render_template,
    request,
    send_from_directory,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

from app.database import get_db
from ai_engine.difficulty import recommend_difficulty
from games.attention_game import create_round as create_attention_round
from games.memory_game import create_round as create_memory_round
from games.pattern_game import create_pattern


def register_routes(app):
    @app.get("/api/games/<game>/round")
    def game_round(game):
        level = request.args.get("difficulty", 1, type=int)
        level = max(1, min(5, level))
        if game == "attention":
            return jsonify(create_attention_round(level))
        if game == "pattern":
            return jsonify(create_pattern(level))
        if game == "picture-match":
            return jsonify(create_memory_round())
        return jsonify({"error": "Unknown game."}), 404
    @app.get("/healthz")
    def healthz():
        connection = get_db(app)
        connection.execute("SELECT 1").fetchone()
        connection.close()
        return jsonify({"status": "ok", "database": "reachable"})

    @app.errorhandler(404)
    def not_found(error):
        if request.path.startswith("/api/"):
            return jsonify({"error": "Resource not found."}), 404
        return render_template("404.html"), 404

    @app.errorhandler(413)
    def upload_too_large(error):
        if request.path.startswith("/api/"):
            return jsonify({"error": "The upload exceeds the 10 MB limit."}), 413
        return render_template("404.html"), 413

    @app.errorhandler(500)
    def internal_error(error):
        app.logger.exception("Unhandled application error")
        if request.path.startswith("/api/"):
            return jsonify({"error": "An unexpected server error occurred."}), 500
        return render_template("500.html"), 500

    def require_caregiver():
        if app.config["TESTING"]:
            return None
        if session.get("role") != "caregiver":
            return jsonify({"error": "Caregiver authorization required."}), 403
        return None

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.get("/login")
    def login():
        return render_template("login.html")

    @app.get("/register")
    def register():
        return render_template("register.html")

    @app.get("/patient")
    def patient():
        patient_id = session.get("user_id") or first_patient_id()
        connection = get_db(app)
        reminder = connection.execute(
            "SELECT * FROM reminders WHERE patient_id=? AND complete=0 ORDER BY time_label LIMIT 1",
            (patient_id,),
        ).fetchone()
        memories = connection.execute(
            "SELECT * FROM memories WHERE patient_id=? ORDER BY id DESC LIMIT 6",
            (patient_id,),
        ).fetchall()
        connection.close()
        return render_template(
            "patient.html",
            next_reminder=dict(reminder) if reminder else None,
            familiar_memories=[dict(row) for row in memories],
        )

    @app.get("/dashboard")
    def dashboard():
        return render_template("dashboard.html")

    @app.get("/caregiver")
    def caregiver():
        if not app.config["TESTING"] and session.get("role") != "caregiver":
            return redirect(url_for("login"))
        patient_id = session.get("user_id")
        connection = get_db(app)
        if patient_id:
            patients = connection.execute(
                "SELECT id,name,username FROM users WHERE role='patient'"
            ).fetchall()
        else:
            patients = connection.execute(
                "SELECT id,name,username FROM users WHERE role='patient'"
            ).fetchall()
        memories = connection.execute(
            "SELECT * FROM memories ORDER BY id DESC LIMIT 8"
        ).fetchall()
        reminders = connection.execute(
            "SELECT * FROM reminders ORDER BY time_label"
        ).fetchall()
        game_rows = connection.execute(
            "SELECT game, AVG(score) AS average_score, COUNT(*) AS sessions "
            "FROM game_sessions GROUP BY game"
        ).fetchall()
        connection.close()
        return render_template(
            "caregiver.html",
            patients=[dict(row) for row in patients],
            recent_memories=[dict(row) for row in memories],
            reminders=[dict(row) for row in reminders],
            game_stats=[dict(row) for row in game_rows],
        )

    @app.get("/games")
    def games():
        return render_template("games.html")

    @app.get("/memory-map")
    def memory_map():
        return render_template(
            "memory-map.html",
            patient_id=session.get("user_id") or first_patient_id(),
        )

    @app.get("/memory-library")
    def memory_library():
        patient_id = session.get("user_id") or first_patient_id()
        connection = get_db(app)
        memories = connection.execute(
            "SELECT * FROM memories WHERE patient_id=? ORDER BY id DESC",
            (patient_id,),
        ).fetchall()
        connection.close()
        return render_template("memory-library.html", memories=[dict(row) for row in memories])

    @app.get("/reminders")
    def reminders():
        patient_id = session.get("user_id") or first_patient_id()
        connection = get_db(app)
        reminder_rows = connection.execute(
            "SELECT * FROM reminders WHERE patient_id=? ORDER BY time_label",
            (patient_id,),
        ).fetchall()
        connection.close()
        return render_template("reminders.html", reminders=[dict(row) for row in reminder_rows])

    @app.get("/impact")
    def impact():
        return render_template("impact.html")

    @app.post("/login")
    def login_submit():
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        connection = get_db(app)
        user = connection.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()
        connection.close()
        if not user or not check_password_hash(user["password_hash"], password):
            return render_template("login.html", error="Please check your username and password.")
        session.update(user_id=user["id"], role=user["role"], name=user["name"])
        return redirect(url_for("caregiver" if user["role"] == "caregiver" else "patient"))

    @app.post("/register")
    def register_submit():
        name = request.form.get("name", "").strip()
        username = request.form.get("username", "").strip().lower()
        password = request.form.get("password", "")
        if len(name) < 2 or len(username) < 3 or len(password) < 6:
            return render_template(
                "register.html",
                error="Enter a name, a username of at least 3 characters, and a password of at least 6 characters.",
            )
        connection = get_db(app)
        existing = connection.execute(
            "SELECT id FROM users WHERE username=?", (username,)
        ).fetchone()
        if existing:
            connection.close()
            return render_template("register.html", error="That username is already used.")
        cursor = connection.execute(
            "INSERT INTO users (name, username, password_hash, role) VALUES (?, ?, ?, 'patient')",
            (name, username, generate_password_hash(password)),
        )
        connection.commit()
        user_id = cursor.lastrowid
        connection.close()
        session.update(user_id=user_id, role="patient", name=name)
        return redirect(url_for("patient"))

    @app.get("/logout")
    def logout():
        session.clear()
        return redirect(url_for("login"))

    @app.get("/demo")
    def demo():
        from seed_demo import seed_demo
        patient = seed_demo(app)
        if patient:
            session.update(user_id=patient["id"], role="patient", name=patient["name"])
        return redirect(url_for("patient"))

    def first_patient_id():
        connection = get_db(app)
        patient = connection.execute(
            "SELECT id FROM users WHERE role = 'patient' ORDER BY id LIMIT 1"
        ).fetchone()
        if patient:
            connection.close()
            return patient["id"]
        password_hash = generate_password_hash("demo")
        cursor = connection.execute(
            "INSERT INTO users (name, username, password_hash, role) VALUES (?, ?, ?, ?)",
            ("Demo Patient", "asha", password_hash, "patient"),
        )
        connection.commit()
        patient_id = cursor.lastrowid
        connection.close()
        return patient_id

    @app.get("/api/memories")
    def memories():
        if session.get("role") == "caregiver":
            patient_id = request.args.get("patient_id", type=int)
        else:
            patient_id = session.get("user_id") or first_patient_id()
        connection = get_db(app)
        if session.get("role") == "caregiver" and not patient_id:
            rows = connection.execute("SELECT * FROM memories ORDER BY id DESC").fetchall()
        else:
            rows = connection.execute(
                "SELECT * FROM memories WHERE patient_id = ? ORDER BY id",
                (patient_id,),
            ).fetchall()
        connection.close()
        return jsonify([dict(row) for row in rows])

    @app.post("/api/memories")
    def create_memory():
        denied = require_caregiver()
        if denied:
            return denied
        data = request.get_json(silent=True) or {}
        if not data.get("title"):
            return jsonify({"error": "A memory title is required."}), 400
        connection = get_db(app)
        cursor = connection.execute(
            """INSERT INTO memories
               (patient_id, title, description, category, photo_url, date_label)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                data.get("patient_id") or session.get("user_id") or first_patient_id(),
                data["title"].strip(),
                data.get("description", "").strip(),
                data.get("category", "Family").strip(),
                data.get("photo_url"),
                data.get("date_label"),
            ),
        )
        connection.commit()
        row = connection.execute("SELECT * FROM memories WHERE id = ?", (cursor.lastrowid,))
        result = dict(row.fetchone())
        connection.close()
        return jsonify(result), 201

    @app.put("/api/memories/<int:memory_id>")
    @app.patch("/api/memories/<int:memory_id>")
    def update_memory(memory_id):
        denied = require_caregiver()
        if denied:
            return denied
        data = request.get_json(silent=True) or {}
        connection = get_db(app)
        memory = connection.execute(
            "SELECT * FROM memories WHERE id = ?", (memory_id,)
        ).fetchone()
        if not memory:
            connection.close()
            return jsonify({"error": "Memory not found."}), 404
        connection.execute(
            """UPDATE memories SET title=?, description=?, category=?, photo_url=?, date_label=?
               WHERE id=?""",
            (
                data.get("title", memory["title"]).strip(),
                data.get("description", memory["description"]).strip(),
                data.get("category", memory["category"]).strip(),
                data.get("photo_url", memory["photo_url"]),
                data.get("date_label", memory["date_label"]),
                memory_id,
            ),
        )
        connection.commit()
        updated = dict(connection.execute(
            "SELECT * FROM memories WHERE id=?", (memory_id,)
        ).fetchone())
        connection.close()
        return jsonify(updated)

    @app.delete("/api/memories/<int:memory_id>")
    def delete_memory(memory_id):
        denied = require_caregiver()
        if denied:
            return denied
        connection = get_db(app)
        result = connection.execute("DELETE FROM memories WHERE id=?", (memory_id,))
        connection.commit()
        connection.close()
        if result.rowcount == 0:
            return jsonify({"error": "Memory not found."}), 404
        return jsonify({"deleted": memory_id})

    @app.get("/api/mindmap/<int:patient_id>")
    def mindmap_patient(patient_id):
        if not app.config["TESTING"]:
            role = session.get("role")
            if role not in {"caregiver", "patient"}:
                return jsonify({"error": "Authentication required."}), 401
            if role == "patient" and session.get("user_id") != patient_id:
                return jsonify({"error": "You may view only your own memory map."}), 403
        connection = get_db(app)
        nodes = connection.execute(
            "SELECT * FROM mindmap_nodes WHERE patient_id = ?", (patient_id,)
        ).fetchall()
        edges = connection.execute(
            "SELECT * FROM mindmap_edges WHERE patient_id = ?", (patient_id,)
        ).fetchall()
        connection.close()
        return jsonify({
            "nodes": [
                {"id": row["id"], "label": row["label"], "description": row["description"],
                 "category": row["category"], "photo_url": row["photo_url"]}
                for row in nodes
            ],
            "edges": [
                {"id": row["id"], "source": row["source_id"], "target": row["target_id"]}
                for row in edges
            ],
        })

    @app.post("/api/mindmap/nodes")
    def mindmap_create_node():
        denied = require_caregiver()
        if denied:
            return denied
        data = request.get_json(silent=True) or {}
        if not data.get("label"):
            return jsonify({"error": "A node label is required."}), 400
        connection = get_db(app)
        cursor = connection.execute(
            """INSERT INTO mindmap_nodes
               (patient_id, label, description, category, photo_url)
               VALUES (?, ?, ?, ?, ?)""",
            (
                data.get("patient_id") or session.get("user_id") or first_patient_id(),
                data["label"].strip(),
                data.get("description", "").strip(),
                data.get("category", "Family").strip(),
                data.get("photo_url"),
            ),
        )
        connection.commit()
        row = connection.execute(
            "SELECT * FROM mindmap_nodes WHERE id = ?", (cursor.lastrowid,)
        ).fetchone()
        connection.close()
        return jsonify(dict(row)), 201

    @app.patch("/api/mindmap/nodes/<int:node_id>")
    @app.put("/api/mindmap/nodes/<int:node_id>")
    def mindmap_update_node(node_id):
        denied = require_caregiver()
        if denied:
            return denied
        data = request.get_json(silent=True) or {}
        connection = get_db(app)
        node = connection.execute(
            "SELECT * FROM mindmap_nodes WHERE id = ?", (node_id,)
        ).fetchone()
        if not node:
            connection.close()
            return jsonify({"error": "Node not found."}), 404
        connection.execute(
            """UPDATE mindmap_nodes
               SET label = ?, description = ?, category = ?, photo_url = ?
               WHERE id = ?""",
            (
                data.get("label", node["label"]),
                data.get("description", node["description"]),
                data.get("category", node["category"]),
                data.get("photo_url", node["photo_url"]),
                node_id,
            ),
        )
        connection.commit()
        updated = dict(connection.execute(
            "SELECT * FROM mindmap_nodes WHERE id = ?", (node_id,)
        ).fetchone())
        connection.close()
        return jsonify(updated)

    @app.delete("/api/mindmap/nodes/<int:node_id>")
    def mindmap_delete_node(node_id):
        denied = require_caregiver()
        if denied:
            return denied
        connection = get_db(app)
        node = connection.execute(
            "SELECT id FROM mindmap_nodes WHERE id = ?", (node_id,)
        ).fetchone()
        if not node:
            connection.close()
            return jsonify({"error": "Node not found."}), 404
        connection.execute(
            "DELETE FROM mindmap_edges WHERE source_id = ? OR target_id = ?", (node_id, node_id)
        )
        connection.execute("DELETE FROM mindmap_nodes WHERE id = ?", (node_id,))
        connection.commit()
        connection.close()
        return jsonify({"deleted": node_id})

    @app.post("/api/mindmap/edges")
    def mindmap_create_edge():
        denied = require_caregiver()
        if denied:
            return denied
        data = request.get_json(silent=True) or {}
        if not data.get("source") or not data.get("target"):
            return jsonify({"error": "Both nodes are required."}), 400
        connection = get_db(app)
        cursor = connection.execute(
            "INSERT INTO mindmap_edges (patient_id, source_id, target_id) VALUES (?, ?, ?)",
            (
                data.get("patient_id") or session.get("user_id") or first_patient_id(),
                int(data["source"]),
                int(data["target"]),
            ),
        )
        connection.commit()
        row = connection.execute(
            "SELECT * FROM mindmap_edges WHERE id = ?", (cursor.lastrowid,)
        ).fetchone()
        connection.close()
        return jsonify({"id": row["id"], "source": row["source_id"], "target": row["target_id"]}), 201

    @app.delete("/api/mindmap/edges/<int:edge_id>")
    def mindmap_delete_edge(edge_id):
        denied = require_caregiver()
        if denied:
            return denied
        connection = get_db(app)
        edge = connection.execute(
            "SELECT id FROM mindmap_edges WHERE id = ?", (edge_id,)
        ).fetchone()
        if not edge:
            connection.close()
            return jsonify({"error": "Edge not found."}), 404
        connection.execute("DELETE FROM mindmap_edges WHERE id = ?", (edge_id,))
        connection.commit()
        connection.close()
        return jsonify({"deleted": edge_id})

    @app.get("/api/reminders")
    def get_reminders():
        if session.get("role") == "caregiver":
            patient_id = request.args.get("patient_id", type=int)
        else:
            patient_id = session.get("user_id") or first_patient_id()
        connection = get_db(app)
        if session.get("role") == "caregiver" and not patient_id:
            rows = connection.execute(
                "SELECT * FROM reminders ORDER BY time_label"
            ).fetchall()
        else:
            rows = connection.execute(
                "SELECT * FROM reminders WHERE patient_id = ? ORDER BY time_label",
                (patient_id,),
            ).fetchall()
        connection.close()
        return jsonify([dict(row) for row in rows])

    @app.post("/api/reminders")
    def create_reminder():
        denied = require_caregiver()
        if denied:
            return denied
        data = request.get_json(silent=True) or {}
        if not data.get("title") or not data.get("time_label"):
            return jsonify({"error": "Title and time are required."}), 400
        connection = get_db(app)
        cursor = connection.execute(
            "INSERT INTO reminders (patient_id, title, time_label, complete) VALUES (?, ?, ?, 0)",
            (
                data.get("patient_id") or session.get("user_id") or first_patient_id(),
                data["title"].strip(),
                data["time_label"].strip(),
            ),
        )
        connection.commit()
        row = connection.execute(
            "SELECT * FROM reminders WHERE id = ?", (cursor.lastrowid,)
        ).fetchone()
        connection.close()
        return jsonify(dict(row)), 201

    @app.patch("/api/reminders/<int:reminder_id>/complete")
    def complete_reminder(reminder_id):
        data = request.get_json(silent=True) or {}
        connection = get_db(app)
        reminder = connection.execute(
            "SELECT * FROM reminders WHERE id = ?", (reminder_id,)
        ).fetchone()
        if not reminder:
            connection.close()
            return jsonify({"error": "Reminder not found."}), 404
        complete = 1 if data.get("complete", True) else 0
        connection.execute(
            "UPDATE reminders SET complete = ? WHERE id = ?", (complete, reminder_id)
        )
        connection.commit()
        updated = dict(connection.execute(
            "SELECT * FROM reminders WHERE id = ?", (reminder_id,)
        ).fetchone())
        connection.close()
        return jsonify(updated)

    @app.put("/api/reminders/<int:reminder_id>")
    @app.patch("/api/reminders/<int:reminder_id>")
    def update_reminder(reminder_id):
        denied = require_caregiver()
        if denied:
            return denied
        data = request.get_json(silent=True) or {}
        connection = get_db(app)
        reminder = connection.execute(
            "SELECT * FROM reminders WHERE id=?", (reminder_id,)
        ).fetchone()
        if not reminder:
            connection.close()
            return jsonify({"error": "Reminder not found."}), 404
        connection.execute(
            "UPDATE reminders SET title=?, time_label=?, complete=? WHERE id=?",
            (
                data.get("title", reminder["title"]).strip(),
                data.get("time_label", reminder["time_label"]).strip(),
                int(data.get("complete", bool(reminder["complete"]))),
                reminder_id,
            ),
        )
        connection.commit()
        updated = dict(connection.execute(
            "SELECT * FROM reminders WHERE id=?", (reminder_id,)
        ).fetchone())
        connection.close()
        return jsonify(updated)

    @app.delete("/api/reminders/<int:reminder_id>")
    def delete_reminder(reminder_id):
        denied = require_caregiver()
        if denied:
            return denied
        connection = get_db(app)
        result = connection.execute("DELETE FROM reminders WHERE id=?", (reminder_id,))
        connection.commit()
        connection.close()
        if result.rowcount == 0:
            return jsonify({"error": "Reminder not found."}), 404
        return jsonify({"deleted": reminder_id})

    @app.post("/api/games/<game>/session")
    def game_session(game):
        data = request.get_json(silent=True) or {}
        score = max(0, min(100, int(data.get("score", 0))))
        difficulty = max(1, min(5, int(data.get("difficulty", 1))))
        connection = get_db(app)
        cursor = connection.execute(
            """INSERT INTO game_sessions
               (patient_id, game, score, difficulty, created_at)
               VALUES (?, ?, ?, ?, ?)""",
            (
                session.get("user_id") or first_patient_id(),
                game[:80],
                score,
                difficulty,
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        connection.commit()
        row = connection.execute(
            "SELECT * FROM game_sessions WHERE id = ?", (cursor.lastrowid,)
        ).fetchone()
        connection.close()
        return jsonify(dict(row)), 201

    @app.get("/api/games/difficulty")
    def game_difficulty():
        patient_id = session.get("user_id") or first_patient_id()
        connection = get_db(app)
        rows = connection.execute(
            "SELECT score FROM game_sessions WHERE patient_id=? ORDER BY id DESC LIMIT 10",
            (patient_id,),
        ).fetchall()
        connection.close()
        recommended = recommend_difficulty([row["score"] for row in rows])
        return jsonify({"difficulty": recommended})

    @app.get("/api/games/history")
    def game_history():
        patient_id = session.get("user_id") or first_patient_id()
        connection = get_db(app)
        rows = connection.execute(
            "SELECT * FROM game_sessions WHERE patient_id = ? ORDER BY id DESC LIMIT 50",
            (patient_id,),
        ).fetchall()
        connection.close()
        return jsonify([dict(row) for row in rows])

    @app.post("/api/upload")
    def upload():
        denied = require_caregiver()
        if denied:
            return denied
        upload = request.files.get("file")
        if not upload or not upload.filename:
            return jsonify({"error": "Choose an image to upload."}), 400
        filename = secure_filename(upload.filename)
        extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        if extension not in {"png", "jpg", "jpeg", "webp"}:
            return jsonify({"error": "Use a PNG, JPG, JPEG, or WebP image."}), 400
        if not upload.mimetype.startswith("image/"):
            return jsonify({"error": "The uploaded file must be an image."}), 400
        if upload.stream.seekable():
            upload.stream.seek(0, os.SEEK_END)
            size = upload.stream.tell()
            upload.stream.seek(0)
            if size > app.config["MAX_CONTENT_LENGTH"]:
                return jsonify({"error": "The image must be 10 MB or smaller."}), 413
        bucket = os.getenv("S3_BUCKET")
        if bucket:
            try:
                import boto3
            except ImportError as error:
                return jsonify({"error": "S3 storage support requires boto3."}), 500
            s3 = boto3.client(
                "s3",
                region_name=os.getenv("AWS_REGION", "us-east-1"),
            )
            key = f"mindmitra/uploads/{filename}"
            s3.upload_fileobj(upload.stream, bucket, key, ExtraArgs={"ContentType": upload.mimetype})
            url = s3.generate_presigned_url(
                "get_object",
                Params={"Bucket": bucket, "Key": key},
                ExpiresIn=3600,
            )
        else:
            upload.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
            url = f"/uploads/{filename}"
        connection = get_db(app)
        connection.execute(
            """INSERT INTO memories
               (patient_id, title, description, category, photo_url)
               VALUES (?, ?, ?, 'Family', ?)""",
            (first_patient_id(), filename.rsplit(".", 1)[0], "Uploaded family photo.", url),
        )
        connection.commit()
        connection.close()
        return jsonify({"filename": filename, "url": url}), 201

    @app.get("/uploads/<path:filename>")
    def uploaded_file(filename):
        return send_from_directory(app.config["UPLOAD_FOLDER"], filename)
