import os

from config import ConfigGenerator, get_configs
from run import get_whitelist, key_from_output, TestRunner

from slack import send_diff_message


def config_handler(event, context):  # pylint: disable=unused-argument
    config_generator = ConfigGenerator(os.environ["CONFIG_BUCKET"])
    config_generator.generate_and_upload()
    return {"statusCode": 200}


def run_handler(event, context):  # pylint: disable=unused-argument
    config_bucket_name = os.environ["CONFIG_BUCKET"]
    output_bucket_name = os.environ["OUTPUT_BUCKET"]
    configs = get_configs(config_bucket_name)
    test_runner = TestRunner(output_bucket_name, *configs.values())
    output = test_runner.run_and_upload(
        accounts=[k.split(".")[0] for k in configs.keys()]  # 123.json -> 123
    )
    new, fixed = test_runner.diff_previous_s3(output, get_whitelist(config_bucket_name))
    send_diff_message(new, fixed, output_bucket_name, key_from_output(output))
    return {"statusCode": 200}
