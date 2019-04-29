# S3 Bucket Inspector
Think you set your S3 bucket policies correctly? Nothing accidentally public? Trust but verify.

## Why
S3 configuration can be complicated. You can have conflicting bucket ACL, bucket policy, object ACLs, public access blocks. Tools for inspecting S3 policies don't always understand the nuances of IP whitelisting and can blurt out false positives or give false negatives. On top of that, your perfectly configured bucket could have been reconfigured by a colleague.

The best way to check for leaky buckets is to actually attempt access:
- From outside your VPC
- From a non-whitelisted IP
- Without an access key

for the operations List, Get, Put and Delete.

Check on a schedule for **Continuous Security(TM)**, and receive warnings on Slack.

## What
Two AWS lambda functions sharing the same code for the python 3.7 runtime:

 1. **Config lambda**: Create a config file with all your buckets and some random keys within the bucket. Requires AWS access `s3:List*`. Multiple copies must be run: one for each account you want to secure.
 2. **Run lambda**: Using the config files, attempt to operate on those buckets and objects without any authentication and reports issues.

Since the lambdas are run outside your VPC, they will be testing what access is allowed to the public Internet.

The following issues are reported:
 - All keys in your bucket can be listed at http://{bucket_name}.s3.amazonaws.com
 - Anyone can upload (PUT) objects into your bucket
 - Anyone can delete objects from your bucket
 - An object is publicly readable (Not comprehensive since that would require testing every single key)

## Configuring

### Terraform all the things
There is an example in the terraform directory of how to set up all the infrastructure for this with terraform including a cloudwatch event which triggers once a day (configurable). The AWS console is a massive foot-gun: use code for your infrastructure. Unfortunately, at the moment you need to run `package-lambda.sh` before `terraform plan` so that the zip file exists. Maybe we can in future use `null_resource` or `archive_file`?

### Buckets
Two buckets are required:
1. **Config bucket**: To hold the per-account config files produced by the config lambda and optionally a `whitelist.json`. Cross-account PUT access must be granted for the config lambdas to work.
 2. **Output bucket**: Holds JSON output files for each run, with timestamp as the name. The output history will allow for reporting issues over time to your vulnerability dashboard. No cross-account access required. GET access only required if you want to diff results with the previous run.

### False positives
You might want public read access on a particular bucket. If so, put a `whitelist.json` file in the config bucket with a dict of issue to list of buckets to ignore.
```json
{
  "PubliclyReadableFileIssue": [
    "my.publicly.readable.bucket",
    "another-bucket"
  ]
}
```
All buckets will still be checked for all issues and they'll appear in the output file, but you won't be notified on Slack. This way, the output files don't depend on the content of the `whitelist.json` file at run time.

### Slack notification
Create an integration and encrypt the Slack hook with a KMS key.
```bash
aws kms encrypt \
  --key-id "alias/$KEY_ALIAS" \
  --plaintext fileb://hook \
  --query CiphertextBlob > encrypted.b64
```
where the file "hook" contains the full Slack hook URL with no final newline.
You'll then need to give the run lambda KMS decrypt access with that key.
Alternatively, for testing you can set the `HOOK_URL` environment variable to the unencrypted hook URL.

### Code
Just zip the python files and upload. To avoid non-determinism in the zip file hash, we use `zip -X function.zip *.py && strip-nondeterminism --type zip function.zip` in `package-lambda.sh`. Otherwise the hash will randomly change without the lambda code being changed so the lambda will be redeployed unnecessarily. If you use nix, you should be able to add both `zip` and `strip-nondeterminism` to your nix env.

## Development
Format Python code with `format.sh` and then lint with `test.sh`.
Run `terraform fmt` if you change the terraform code.
Play around locally with a command like:
```bash
docker build -f Dockerfile.test -t s3bi-test . && \
  docker run --rm \
    -v $(pwd):/app \
    -v "$HOME/.aws:/root/.aws:ro" \
    -e OUTPUT_BUCKET=my-output-bucket-name \
    -e CONFIG_BUCKET=my-config-bucket-name \
    -e HOOK_URL=https://hooks.slack.com/services/blah/blah \
    -it s3bi-test \
    python -i /app/lambda.py
```
