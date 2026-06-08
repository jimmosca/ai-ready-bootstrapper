terraform {
  required_version = ">= 1.5.0"
}

provider "aws" {
  region = "us-east-1"
}

resource "aws_ecr_repository" "backend" {
  name = "rag-backend"
}
