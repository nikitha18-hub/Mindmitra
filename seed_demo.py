from werkzeug.security import generate_password_hash

from app.database import get_db


def seed_demo(app):
    connection = get_db(app)
    patient = connection.execute(
        "SELECT * FROM users WHERE username = 'asha'"
    ).fetchone()
    caregiver = connection.execute(
        "SELECT * FROM users WHERE username = 'meera'"
    ).fetchone()

    if not patient:
        cursor = connection.execute(
            "INSERT INTO users (name, username, password_hash, role) VALUES (?, ?, ?, ?)",
            ("Asha", "asha", generate_password_hash("demo"), "patient"),
        )
        patient_id = cursor.lastrowid
    else:
        patient_id = patient["id"]

    if not caregiver:
        connection.execute(
            "INSERT INTO users (name, username, password_hash, role) VALUES (?, ?, ?, ?)",
            ("Meera", "meera", generate_password_hash("demo"), "caregiver"),
        )

    if not connection.execute(
        "SELECT id FROM memories WHERE patient_id = ? LIMIT 1", (patient_id,)
    ).fetchone():
        connection.executemany(
            """INSERT INTO memories
               (patient_id, title, description, category, date_label)
               VALUES (?, ?, ?, ?, ?)""",
            [
                (patient_id, "First garden in Mysore", "A warm day with jasmine flowers.", "Places", "18 March"),
                (patient_id, "Meera's birthday", "Family singing beside the blue table.", "Family", "12 June"),
                (patient_id, "Sunday music lessons", "Learning a favourite old song.", "Interests", "Always"),
            ],
        )

    if not connection.execute(
        "SELECT id FROM mindmap_nodes WHERE patient_id = ? LIMIT 1", (patient_id,)
    ).fetchone():
        names = [
            ("Asha", "Family", "This is Asha."),
            ("Meera", "Family", "Meera is Asha's daughter."),
            ("Mysore", "Places", "A remembered family home."),
            ("Blue garden", "Places", "Jasmine and evening light."),
            ("Music", "Interests", "Old songs and Sunday lessons."),
            ("Reading", "Interests", "A quiet favourite afternoon."),
            ("Birthday", "Events", "Family birthday gathering."),
        ]
        node_ids = {}
        for name, category, description in names:
            cursor = connection.execute(
                "INSERT INTO mindmap_nodes (patient_id, label, description, category) VALUES (?, ?, ?, ?)",
                (patient_id, name, description, category),
            )
            node_ids[name] = cursor.lastrowid

        edges = [
            ("Asha", "Meera"), ("Asha", "Mysore"), ("Asha", "Blue garden"),
            ("Asha", "Music"), ("Asha", "Reading"), ("Asha", "Birthday"),
            ("Meera", "Birthday"), ("Mysore", "Blue garden"),
        ]
        connection.executemany(
            "INSERT INTO mindmap_edges (patient_id, source_id, target_id) VALUES (?, ?, ?)",
            [(patient_id, node_ids[source], node_ids[target]) for source, target in edges],
        )

    if not connection.execute(
        "SELECT id FROM reminders WHERE patient_id = ? LIMIT 1", (patient_id,)
    ).fetchone():
        connection.executemany(
            "INSERT INTO reminders (patient_id, title, time_label, complete) VALUES (?, ?, ?, 0)",
            [
                (patient_id, "Drink a glass of water", "09:00"),
                (patient_id, "Look at the family photo", "11:30"),
                (patient_id, "Sit in the garden", "16:00"),
            ],
        )

    connection.commit()
    patient = connection.execute(
        "SELECT * FROM users WHERE id = ?", (patient_id,)
    ).fetchone()
    result = dict(patient)
    connection.close()
    return result


if __name__ == "__main__":
    from app import create_app

    app = create_app()
    with app.app_context():
        patient = seed_demo(app)
        print(f"Seeded patient {patient['username']} and caregiver meera")
