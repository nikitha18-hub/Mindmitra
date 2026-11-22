variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "instance_type" {
  type    = string
  default = "t3.micro"
}

variable "admin_cidr" {
  type        = string
  description = "Public CIDR allowed SSH access."
  default     = "203.0.113.0/32"
}

variable "upload_bucket_name" {
  type = string
}

variable "repository_url" {
  type        = string
  description = "Git URL for the public or deploy-key-accessible MindMitra repository."
  default     = "https://github.com/nikitha18-hub/Mindmitra.git"
}
