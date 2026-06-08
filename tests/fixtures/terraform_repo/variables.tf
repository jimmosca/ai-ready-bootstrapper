variable "project" {
  type        = string
  description = "Project name used to prefix resources."
}

variable "region" {
  type        = string
  description = "AWS region to deploy into."
  default     = "us-east-1"
}
