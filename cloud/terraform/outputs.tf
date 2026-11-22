output "app_public_ip" {
  value = aws_instance.app.public_ip
}

output "rds_endpoint" {
  value = aws_db_instance.mindmitra.address
}

output "upload_bucket" {
  value = aws_s3_bucket.uploads.id
}
