terraform {
  required_version = ">= 1.5"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

data "aws_availability_zones" "available" {
  state = "available"
}

data "aws_ami" "amazon_linux" {
  most_recent = true
  owners      = ["amazon"]
  filter {
    name   = "name"
    values = ["al2023-ami-*-x86_64"]
  }
}

resource "aws_vpc" "mindmitra" {
  cidr_block           = "10.20.0.0/16"
  enable_dns_support   = true
  enable_dns_hostnames = true
  tags = { Name = "mindmitra-vpc" }
}

resource "aws_internet_gateway" "mindmitra" {
  vpc_id = aws_vpc.mindmitra.id
}

resource "aws_subnet" "public" {
  count                   = 2
  vpc_id                  = aws_vpc.mindmitra.id
  cidr_block              = cidrsubnet(aws_vpc.mindmitra.cidr_block, 8, count.index)
  availability_zone       = data.aws_availability_zones.available.names[count.index]
  map_public_ip_on_launch = true
  tags = { Name = "mindmitra-public-${count.index}" }
}

resource "aws_subnet" "private" {
  count             = 2
  vpc_id            = aws_vpc.mindmitra.id
  cidr_block        = cidrsubnet(aws_vpc.mindmitra.cidr_block, 8, count.index + 10)
  availability_zone = data.aws_availability_zones.available.names[count.index]
  tags = { Name = "mindmitra-private-${count.index}" }
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.mindmitra.id
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.mindmitra.id
  }
}

resource "aws_route_table_association" "public" {
  count          = 2
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

resource "aws_db_subnet_group" "mindmitra" {
  name       = "mindmitra-db-subnets"
  subnet_ids = aws_subnet.private[*].id
}

resource "aws_security_group" "app" {
  name   = "mindmitra-app"
  vpc_id = aws_vpc.mindmitra.id
  ingress {
    from_port   = 5000
    to_port     = 5000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.admin_cidr]
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "database" {
  name   = "mindmitra-database"
  vpc_id = aws_vpc.mindmitra.id
  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.app.id]
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "random_password" "database" {
  length  = 32
  special = false
}

resource "random_password" "application" {
  length  = 48
  special = false
}

resource "aws_secretsmanager_secret" "database" {
  name = "mindmitra/database-url"
}

resource "aws_db_instance" "mindmitra" {
  identifier              = "mindmitra-db"
  allocated_storage       = 20
  engine                  = "postgres"
  engine_version          = "16"
  instance_class          = "db.t3.micro"
  db_name                 = "mindmitra"
  username                = "mindmitra"
  password                = random_password.database.result
  db_subnet_group_name    = aws_db_subnet_group.mindmitra.name
  vpc_security_group_ids  = [aws_security_group.database.id]
  publicly_accessible     = false
  skip_final_snapshot     = true
  storage_encrypted       = true
  backup_retention_period = 7
  deletion_protection     = false
}

resource "aws_secretsmanager_secret_version" "database" {
  secret_id = aws_secretsmanager_secret.database.id
  secret_string = jsonencode({
    database_url = "postgresql://mindmitra:${random_password.database.result}@${aws_db_instance.mindmitra.address}:5432/mindmitra"
    secret_key   = random_password.application.result
  })
}

resource "aws_s3_bucket" "uploads" {
  bucket = var.upload_bucket_name
}

resource "aws_s3_bucket_public_access_block" "uploads" {
  bucket                  = aws_s3_bucket.uploads.id
  block_public_acls       = true
  ignore_public_acls      = true
  block_public_policy     = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "uploads" {
  bucket = aws_s3_bucket.uploads.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_iam_role" "app" {
  name = "mindmitra-app-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = { Service = "ec2.amazonaws.com" }
      Action = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy" "app" {
  name = "mindmitra-app-policy"
  role = aws_iam_role.app.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = ["s3:PutObject", "s3:GetObject", "s3:DeleteObject"]
        Resource = "${aws_s3_bucket.uploads.arn}/*"
      },
      {
        Effect = "Allow"
        Action = ["secretsmanager:GetSecretValue"]
        Resource = aws_secretsmanager_secret.database.arn
      }
    ]
  })
}

resource "aws_iam_instance_profile" "app" {
  name = "mindmitra-app-profile"
  role = aws_iam_role.app.name
}

resource "aws_instance" "app" {
  ami                    = data.aws_ami.amazon_linux.id
  instance_type          = var.instance_type
  subnet_id              = aws_subnet.public[0].id
  vpc_security_group_ids = [aws_security_group.app.id]
  iam_instance_profile   = aws_iam_instance_profile.app.name
  associate_public_ip_address = true
  user_data_replace_on_change = true
  user_data = <<-EOF
    #!/bin/bash
    set -euxo pipefail
    dnf update -y
    dnf install -y git python3-pip awscli
    mkdir -p /opt/mindmitra
    git clone ${var.repository_url} /opt/mindmitra
    cd /opt/mindmitra
    python3 -m pip install -r requirements.txt
    python3 seed_demo.py
    cat >/etc/systemd/system/mindmitra.service <<'UNIT'
    [Unit]
    Description=MindMitra Flask Application
    After=network.target

    [Service]
    WorkingDirectory=/opt/mindmitra
    Environment=APP_ENV=production
    Environment=AWS_REGION=${var.aws_region}
    Environment=AWS_SECRETS_MANAGER_ID=${aws_secretsmanager_secret.database.id}
    Environment=S3_BUCKET=${aws_s3_bucket.uploads.id}
    Environment=SESSION_COOKIE_SECURE=1
    ExecStart=/usr/local/bin/gunicorn --bind 0.0.0.0:5000 --workers 3 --timeout 120 app:app
    Restart=always

    [Install]
    WantedBy=multi-user.target
    UNIT
    systemctl daemon_reload
    systemctl enable --now mindmitra
  EOF
  tags = { Name = "mindmitra-app" }
}
