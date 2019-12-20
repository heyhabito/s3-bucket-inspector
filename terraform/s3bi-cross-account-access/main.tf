resource "aws_s3_bucket_policy" "cross_account_upload_config" {
  bucket = var.bucket_name

  policy = <<POLICY
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowAccessBy${var.account_id}",
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::${var.account_id}:root"
      },
      "Action": [
        "s3:PutObject",
        "s3:PutObjectAcl"
      ],
      "Resource": "arn:aws:s3:::${var.bucket_name}/*"
    }
  ]
}
POLICY
}
