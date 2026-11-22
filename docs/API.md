# MindMitra API

The API uses JSON except for `/api/upload`, which accepts multipart form data.

## Pages

- `GET /` - Landing page
- `GET /patient` - Patient dashboard
- `GET /caregiver` - Caregiver dashboard
- `GET /memory-map` - Memory constellation
- `GET /memory-library` - Photo library
- `GET /reminders` - Reminder timeline
- `GET /games` - Memory games

## Memories

- `GET /api/memories`
- `POST /api/memories` - Caregiver only
- `PUT/PATCH /api/memories/<id>` - Caregiver only
- `DELETE /api/memories/<id>` - Caregiver only

## Memory Map

- `GET /api/mindmap/<patient_id>`
- `POST /api/mindmap/nodes` - Caregiver only
- `PUT/PATCH /api/mindmap/nodes/<id>` - Caregiver only
- `DELETE /api/mindmap/nodes/<id>` - Caregiver only
- `POST /api/mindmap/edges` - Caregiver only
- `DELETE /api/mindmap/edges/<id>` - Caregiver only

## Reminders

- `GET /api/reminders`
- `POST /api/reminders` - Caregiver only
- `PATCH /api/reminders/<id>/complete`
- `PUT/PATCH /api/reminders/<id>` - Caregiver only
- `DELETE /api/reminders/<id>` - Caregiver only

## Games

- `POST /api/games/<game>/session`
- `GET /api/games/history`
- `GET /api/games/difficulty`

## Upload

- `POST /api/upload` - Caregiver only
- Allowed types: PNG, JPG, JPEG, WebP
- Maximum size: 10 MB

Mutation requests require the session CSRF token in `X-CSRF-Token` or form field `csrf_token`.
