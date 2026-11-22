# AWS Setup

Provision only after local behavior is stable and deployment costs are approved.

1. Create a private PostgreSQL RDS instance.
2. Create a private S3 bucket with block-public-access enabled.
3. Create an IAM role for EC2 with only required S3 and CloudWatch permissions.
4. Deploy Flask on EC2 or a container platform.
5. Set `DATABASE_URL`, `SECRET_KEY`, and upload configuration through environment or secrets management.
6. Configure CloudWatch logs and alarms.

MindMitra currently uses SQLite in the checked-in application. PostgreSQL migration is prepared through environment configuration, but it is not complete until the data access layer and connection test are adapted and executed against RDS.