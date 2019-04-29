resource "aws_cloudwatch_event_rule" "rule" {
  description         = "${var.rule_description}"
  schedule_expression = "${var.schedule_expression}"
}

resource "aws_cloudwatch_event_target" "target" {
  rule = "${aws_cloudwatch_event_rule.rule.name}"
  arn  = "${var.lambda_arn}"
}

resource "aws_lambda_permission" "allow_cloudwatch_to_call_s3bi_run" {
  action        = "lambda:InvokeFunction"
  function_name = "${var.lambda_name}"
  principal     = "events.amazonaws.com"
  source_arn    = "${aws_cloudwatch_event_rule.rule.arn}"
}
