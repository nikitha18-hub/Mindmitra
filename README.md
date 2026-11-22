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

## Environment

Copy `.env.example` into the process environment. `.env` files must not be committed.

- `SECRET_KEY`: required for production and should have at least 32 characters
- `DATABASE_URL`: SQLite local URL, for example `sqlite:///mindmitra.db`
- `APP_ENV`: `development` or `production`
- `SESSION_COOKIE_SECURE`: `1` behind HTTPS
- `HOST` and `PORT`: Flask listener settings

## AWS readiness

The repository includes EC2, RDS, S3, CloudWatch, and Terraform preparation documents. AWS resources are not automatically created. PostgreSQL support remains pending until database adapters and live RDS verification are completed.

Demo accounts:

- Patient: `asha` / `demo`
- Caregiver: `meera` / `demo`

For production, set `SECRET_KEY` and `DATABASE_URL` from `.env.example` without committing real secrets.

Deploy with a production WSGI server:

```bash
gunicorn --bind 0.0.0.0:5000 app:app
```

## Test

```powershell
python -m pytest -q
```

## Stack

Python, Flask, SQLAlchemy, SQLite, Jinja, vanilla JavaScript, and CSS. AWS storage and database adapters can be added after the local experience is stable.
