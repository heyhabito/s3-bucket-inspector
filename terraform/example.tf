# You might want `source = "./s3bi-run-job"` to use local rather than remote module sources, or to use `?ref=hash_or_branch_name`.

module "s3bi_buckets" {
  source             = "github.com/heyhabito/s3-bucket-inspector.git//terraform/s3bi-buckets"
  s3bi_config_bucket = "my-s3bi-config-bucket"
  s3bi_output_bucket = "my-s3bi-output-bucket"
}

module "s3bi_run" {
  source               = "github.com/heyhabito/s3-bucket-inspector.git//terraform/s3bi-run-job"
  kms_key_arn          = "blah"
  encrypted_slack_hook = "wskldjfkls"
  config_bucket_name   = "${module.s3bi_buckets.config_bucket_name}"
  config_bucket_arn    = "${module.s3bi_buckets.config_bucket_arn}"
  output_bucket_name   = "${module.s3bi_buckets.output_bucket_name}"
  output_bucket_arn    = "${module.s3bi_buckets.output_bucket_arn}"
  schedule_expression  = "cron(35 10 * * ? *)"
}

module "s3bi_config_main" {
  source              = "github.com/heyhabito/s3-bucket-inspector.git//terraform/s3bi-config-job"
  config_bucket_name  = "${module.s3bi_buckets.config_bucket_name}"
  config_bucket_arn   = "${module.s3bi_buckets.config_bucket_arn}"
  schedule_expression = "cron(0 10 * * ? *)"
}

# Config job for the datascience account (repeat these 2 modules for all extra accounts)
module "s3bi_config_datascience" {
  providers = {
    aws = "aws.datascience"
  }

  source              = "github.com/heyhabito/s3-bucket-inspector.git//terraform/s3bi-config-job"
  config_bucket_name  = "${module.s3bi_buckets.config_bucket_name}"
  config_bucket_arn   = "${module.s3bi_buckets.config_bucket_arn}"
  schedule_expression = "cron(0 10 * * ? *)"
}

module "s3bi_datascience_cross_account_access_to_config_bucket" {
  source      = "github.com/heyhabito/s3-bucket-inspector.git//terraform/s3bi-cross-account-access"
  bucket_name = "${module.s3bi_buckets.config_bucket_name}"
  account_id  = 12345
}
