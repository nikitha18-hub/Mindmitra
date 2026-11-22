# AWS Setup

Provision only after local behavior is stable and deployment costs are approved.

1. Create a private PostgreSQL RDS instance.
2. Create a private S3 bucket with block-public-access enabled.
3. Create an IAM role for EC2 with only required S3 and CloudWatch permissions.
4. Deploy Flask on EC2 or a container platform.
5. Set `DATABASE_URL`, `SECRET_KEY`, and upload configuration through environment or secrets management.
6. Configure CloudWatch logs and alarms.

MindMitra supports SQLite locally and PostgreSQL through `DATABASE_URL` or AWS Secrets Manager. PostgreSQL schema initialization is implemented; live RDS connection verification still requires AWS credentials and provisioning.

Infrastructure template:

```powershell
cd cloud/terraform
terraform init
terraform plan -var="upload_bucket_name=your-globally-unique-mindmitra-uploads"
```

Provision only after cost and account approval. Set `AWS_SECRETS_MANAGER_ID` to a JSON secret containing `database_url` and `secret_key`. EC2 uses its IAM instance profile to read the secret and S3 bucket.