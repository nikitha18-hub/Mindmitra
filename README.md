# <h1 align="center">MindMitra</h1>

MindMitra is a supportive, privacy-first dementia-engagement platform. It connects familiar memories, daily reminders, gentle games, voice assistance, and caregiver tools in one calm web experience.

MindMitra is an engagement tool, not a medical device or diagnosis system.

## Run locally

```powershell
python -m pip install -r requirements.txt
python seed_demo.py
python app.py
```

Open `http://127.0.0.1:5000/`.

Demo accounts:

- Patient: `asha` / `demo`
- Caregiver: `meera` / `demo`

## Test

```powershell
python -m pytest -q
```

## Stack

Python, Flask, SQLAlchemy, SQLite, Jinja, vanilla JavaScript, and CSS. AWS storage and database adapters can be added after the local experience is stable.
