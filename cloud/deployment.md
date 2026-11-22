# Deployment

- Run tests before deployment.
- Use a production WSGI server rather than Flask debug mode.
- Replace SQLite with PostgreSQL.
- Keep secret values outside source control.
- Store uploads in S3.
- Do not provision resources until the owner approves the estimated monthly cost.