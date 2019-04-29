# Config and results buckets for S3 Bucket Inspector (s3bi)
resource "aws_s3_bucket" "s3bi_config_bucket" {
  bucket = "${var.s3bi_config_bucket}"
  acl    = "private"
}

module "s3bi-config-non-public" {
  source      = "../non-public-bucket"
  bucket_name = "${aws_s3_bucket.s3bi_config_bucket.id}"
}

resource "aws_s3_bucket" "s3bi_output_bucket" {
  bucket = "${var.s3bi_output_bucket}"
  acl    = "private"
}

module "s3bi-output-non-public" {
  source      = "../non-public-bucket"
  bucket_name = "${aws_s3_bucket.s3bi_output_bucket.id}"
}
