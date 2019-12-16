resource "aws_iam_role" "s3bi_lambda_config_role" {
  name        = "s3bi_lambda_config_role"
  description = "Role for S3 Bucket Inspector config job"

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

resource "aws_iam_policy" "s3bi_lambda_list_policy" {
  name        = "s3bi_lambda_list_policy"
  description = "List buckets and keys"

  policy = <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:List*"
            ],
            "Resource": "*"
        }
    ]
}
EOF
}

resource "aws_iam_policy" "s3bi_lambda_write_config_policy" {
  name        = "s3bi_lambda_write_config_policy"
  description = "Ability to write to ${var.config_bucket_arn}"

  policy = <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:PutObject",
                "s3:PutObjectAcl"
            ],
            "Resource": "${var.config_bucket_arn}/*"
        }
    ]
}
EOF
}

resource "aws_iam_role_policy_attachment" "s3bi-list-buckets" {
  role       = "${aws_iam_role.s3bi_lambda_config_role.name}"
  policy_arn = "${aws_iam_policy.s3bi_lambda_list_policy.arn}"
}

resource "aws_iam_role_policy_attachment" "s3bi-write-config" {
  role       = "${aws_iam_role.s3bi_lambda_config_role.name}"
  policy_arn = "${aws_iam_policy.s3bi_lambda_write_config_policy.arn}"
}

resource "aws_iam_role_policy_attachment" "s3bi-cloudwatch-logs" {
  role       = "${aws_iam_role.s3bi_lambda_config_role.name}"
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_lambda_function" "s3bi_config_lambda" {
  function_name = "s3bi-config"
  description   = "Job to make a config for s3bi with a list of buckets and keys"
  filename      = "${path.module}/../no-code-deployed-yet.zip"
  role          = "${aws_iam_role.s3bi_lambda_config_role.arn}"
  handler       = "lambda.config_handler"
  runtime       = "python3.7"
  timeout       = 900

  environment {
    variables = {
      CONFIG_BUCKET = "${var.config_bucket_name}"
    }
  }

  lifecycle {
    ignore_changes = [
      "filename",
    ]
  }
}

module "s3bi_config_cron" {
  source              = "../lambda-schedule"
  rule_description    = "Generate config (list of buckets, etc) for s3bi on a schedule"
  schedule_expression = "${var.schedule_expression}"
  lambda_name         = "${aws_lambda_function.s3bi_config_lambda.function_name}"
  lambda_arn          = "${aws_lambda_function.s3bi_config_lambda.arn}"
}
