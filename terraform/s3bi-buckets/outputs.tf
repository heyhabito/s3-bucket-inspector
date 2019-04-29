output "config_bucket_arn" {
  value = "${aws_s3_bucket.s3bi_config_bucket.arn}"
}

output "output_bucket_arn" {
  value = "${aws_s3_bucket.s3bi_output_bucket.arn}"
}

output "config_bucket_name" {
  value = "${aws_s3_bucket.s3bi_config_bucket.id}"
}

output "output_bucket_name" {
  value = "${aws_s3_bucket.s3bi_output_bucket.id}"
}
