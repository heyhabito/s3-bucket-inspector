variable "kms_key_arn" {
  description = "Key required to decrypt the Slack hook URL"
  type        = "string"
}

variable "encrypted_slack_hook" {
  description = "Slack hook URL encrypted with KMS key"
  type        = "string"
}

variable "config_bucket_name" {
  type = "string"
}

variable "config_bucket_arn" {
  type = "string"
}

variable "output_bucket_name" {
  type = "string"
}

variable "output_bucket_arn" {
  type = "string"
}

variable "schedule_expression" {
  type    = "string"
  default = "cron(0 10 * * ? *)"
}

variable "zip_file" {
  description = "Path to deterministicly-generated zip file containing lambda code"
  type        = "string"
}
