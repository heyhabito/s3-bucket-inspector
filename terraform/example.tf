# You might want `source = "git::https://github.com/blah.git//terraform/s3bi-buckets"`

variable "zip_file" {
  type    = "string"
  default = "./function.zip"
}

module "s3bi_buckets" {
  source             = "./s3bi-buckets"
  s3bi_config_bucket = "my-s3bi-config-bucket"
  s3bi_output_bucket = "my-s3bi-output-bucket"
}

module "s3bi_run" {
  source               = "./s3bi-run-job"
  kms_key_arn          = "blah"
  encrypted_slack_hook = "wskldjfkls"
  config_bucket_name   = "${module.s3bi_buckets.config_bucket_name}"
  config_bucket_arn    = "${module.s3bi_buckets.config_bucket_arn}"
  output_bucket_name   = "${module.s3bi_buckets.output_bucket_name}"
  output_bucket_arn    = "${module.s3bi_buckets.output_bucket_arn}"
  zip_file             = "${var.zip_file}"
  schedule_expression  = "cron(35 10 * * ? *)"
}

module "s3bi_config_main" {
  source              = "./s3bi-config-job"
  config_bucket_name  = "${module.s3bi_buckets.config_bucket_name}"
  config_bucket_arn   = "${module.s3bi_buckets.config_bucket_arn}"
  zip_file            = "${var.zip_file}"
  schedule_expression = "cron(0 10 * * ? *)"
}

# Config job for the datascience account (repeat these 2 modules for all extra accounts)
module "s3bi_config_datascience" {
  providers = {
    aws = "aws.datascience"
  }

  source              = "./s3bi-config-job"
  config_bucket_name  = "${module.s3bi_buckets.config_bucket_name}"
  config_bucket_arn   = "${module.s3bi_buckets.config_bucket_arn}"
  zip_file            = "${var.zip_file}"
  schedule_expression = "cron(0 10 * * ? *)"
}

module "s3bi_datascience_cross_account_access_to_config_bucket" {
  source      = "./s3bi-cross-account-access"
  bucket_name = "${module.s3bi_buckets.config_bucket_name}"
  account_id  = 12345
}
