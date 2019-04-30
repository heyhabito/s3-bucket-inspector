resource "aws_iam_role" "s3bi_lambda_run_role" {
  name        = "s3bi_lambda_run_role"
  description = "Role for S3 Bucket Inspector job which actually runs the tests"

  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Effect": "Allow",
      "Sid": ""
    }
  ]
}
EOF
}

resource "aws_iam_policy" "s3bi_lambda_read_config_policy" {
  name        = "s3bi_lambda_read_config_policy"
  description = "Ability to read s3bi configs from ${var.config_bucket_arn}"

  policy = <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject"
            ],
            "Resource": "${var.config_bucket_arn}/*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "s3:ListBucket"
            ],
            "Resource": "${var.config_bucket_arn}"
        }
    ]
}
EOF
}

resource "aws_iam_policy" "s3bi_lambda_write_output_policy" {
  name        = "s3bi_lambda_write_output_policy"
  description = "Ability to read from and write to ${var.output_bucket_arn}. Read and list access needed for comparison with previous results."

  policy = <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:ListBucket",
                "s3:PutObject"
            ],
            "Resource": [
                "${var.output_bucket_arn}",
                "${var.output_bucket_arn}/*"
            ]
        }
    ]
}
EOF
}

resource "aws_iam_policy" "s3bi_lambda_decrypt_config_policy" {
  name        = "s3bi_lambda_decrypt_config_policy"
  description = "Ability to use the KMS key (needed to decrypt Slack hook url)"

  policy = <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "kms:Decrypt"
            ],
            "Resource": "${var.kms_key_arn}"
        }
    ]
}
EOF
}

resource "aws_iam_role_policy_attachment" "s3bi-read-config" {
  role       = "${aws_iam_role.s3bi_lambda_run_role.name}"
  policy_arn = "${aws_iam_policy.s3bi_lambda_read_config_policy.arn}"
}

resource "aws_iam_role_policy_attachment" "s3bi-write-output" {
  role       = "${aws_iam_role.s3bi_lambda_run_role.name}"
  policy_arn = "${aws_iam_policy.s3bi_lambda_write_output_policy.arn}"
}

resource "aws_iam_role_policy_attachment" "s3bi-decrypt-hook" {
  role       = "${aws_iam_role.s3bi_lambda_run_role.name}"
  policy_arn = "${aws_iam_policy.s3bi_lambda_decrypt_config_policy.arn}"
}

resource "aws_lambda_function" "s3bi_run_lambda" {
  function_name = "s3bi-run"
  description   = "Job to run s3bi using a config"
  filename      = "${path.module}/../no-code-deployed-yet.zip"
  role          = "${aws_iam_role.s3bi_lambda_run_role.arn}"
  handler       = "lambda.run_handler"
  runtime       = "python3.7"
  timeout       = 900

  environment {
    variables = {
      CONFIG_BUCKET      = "${var.config_bucket_name}"
      OUTPUT_BUCKET      = "${var.output_bucket_name}"
      ENCRYPTED_HOOK_URL = "${var.encrypted_slack_hook}"
    }
  }
}

module "s3bi_run_cron" {
  source              = "../lambda-schedule"
  rule_description    = "Runs s3bi to check for bucket security issues"
  schedule_expression = "${var.schedule_expression}"
  lambda_name         = "${aws_lambda_function.s3bi_run_lambda.function_name}"
  lambda_arn          = "${aws_lambda_function.s3bi_run_lambda.arn}"
}
