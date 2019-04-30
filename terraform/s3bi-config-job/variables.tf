variable "config_bucket_name" {
  type = "string"
}

variable "config_bucket_arn" {
  type = "string"
}

variable "schedule_expression" {
  type    = "string"
  default = "cron(0 10 * * ? *)"
}
