variable "kms_key_arn" {
  description = "Key required to decrypt the Slack hook URL"
  type        = string
}

variable "encrypted_slack_hook" {
  description = "Slack hook URL encrypted with KMS key"
  type        = string
}

variable "function_name" {
  # Set function_name if you want multiple run lambdas, as they need unique names (prefixed by s3bi-)
  description = "Name of lambda function"
  type        = string
  default     = "run"
}

variable "diff_only" {
  # Set to anything other than the empty string
  default = ""
}

variable "config_bucket_name" {
  type = string
}

variable "config_bucket_arn" {
  type = string
}

variable "output_bucket_name" {
  type = string
}

variable "output_bucket_arn" {
  type = string
}

variable "schedule_expression" {
  type    = string
  default = "cron(0 10 * * ? *)"
}
