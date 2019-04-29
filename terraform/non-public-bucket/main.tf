resource "aws_s3_bucket_public_access_block" "no_accidental_public_access" {
  bucket = "${var.bucket_name}"

  block_public_acls   = true
  block_public_policy = true
  ignore_public_acls  = true
}
