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


def register_routes(app):
    @app.get("/")
    def index():
        return render_template("index.html")

    @app.get("/login")
    def login():
        return render_template("login.html")

    @app.get("/patient")
    def patient():
        return render_template("patient.html")

    @app.get("/dashboard")
    def dashboard():
        return render_template("dashboard.html")

    @app.get("/caregiver")
    def caregiver():
        return render_template("caregiver.html")

    @app.get("/games")
    def games():
        return render_template("games.html")

    @app.get("/memory-map")
    def memory_map():
        return render_template("memory-map.html")

    @app.get("/memory-library")
    def memory_library():
        return render_template("memory-library.html")

    @app.get("/reminders")
    def reminders():
        return render_template("reminders.html")

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
        patient_id = session.get("user_id") or first_patient_id()
        connection = get_db(app)
        rows = connection.execute(
            "SELECT * FROM memories WHERE patient_id = ? ORDER BY id",
            (patient_id,),
        ).fetchall()
        connection.close()
        return jsonify([dict(row) for row in rows])

    @app.post("/api/memories")
    def create_memory():
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

    @app.get("/api/mindmap/<int:patient_id>")
    def mindmap_patient(patient_id):
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
        patient_id = session.get("user_id") or first_patient_id()
        connection = get_db(app)
        rows = connection.execute(
            "SELECT * FROM reminders WHERE patient_id = ? ORDER BY time_label",
            (patient_id,),
        ).fetchall()
        connection.close()
        return jsonify([dict(row) for row in rows])

    @app.post("/api/reminders")
    def create_reminder():
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
        upload = request.files.get("file")
        if not upload or not upload.filename:
            return jsonify({"error": "Choose an image to upload."}), 400
        filename = secure_filename(upload.filename)
        extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        if extension not in {"png", "jpg", "jpeg", "webp"}:
            return jsonify({"error": "Use a PNG, JPG, JPEG, or WebP image."}), 400
        if not upload.mimetype.startswith("image/"):
            return jsonify({"error": "The uploaded file must be an image."}), 400
        upload.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
        return jsonify({"filename": filename, "url": f"/uploads/{filename}"}), 201

    @app.get("/uploads/<path:filename>")
    def uploaded_file(filename):
        return send_from_directory(app.config["UPLOAD_FOLDER"], filename)
