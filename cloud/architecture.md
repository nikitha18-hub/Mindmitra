MindMitra deployment architecture:

```text
Browser -> Flask on EC2 -> PostgreSQL on RDS
            |                |
            +-> S3 uploads   +-> Backup
            |
            +-> CloudWatch logs and metrics
```

- EC2 runs the Flask application behind a load balancer.
- RDS PostgreSQL replaces SQLite in production.
- S3 stores validated user uploads.
- IAM roles grant least-privilege access; no AWS keys are stored in code.
- CloudWatch monitors application and infrastructure health.