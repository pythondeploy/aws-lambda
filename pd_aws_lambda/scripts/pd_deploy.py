"""Script to delpoy the application to Lambda functions through PythonDeploy."""
import argparse
import json
import os
import ssl
import time
import urllib.request
from pathlib import Path

from boto3 import Session

from .helpers import BUILD_FILE_NAME, PD_API_URL, get_build_dir


ctx = None
if os.environ.get("PD_SKIP_CERT_VALIDATION") == "skip":
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE


def get_s3_access_data(app_id, api_key):
    """Retrieve access information from PythonDeploy."""
    print("Requesting s3 access information")

    jsondata = json.dumps({"action": "temp_s3_access"})
    jsondataasbytes = jsondata.encode("utf-8")

    req = urllib.request.Request(PD_API_URL.format(app_id=app_id))
    req.add_header("Content-Length", len(jsondataasbytes))
    req.add_header("Content-Type", "application/json; charset=utf-8")
    req.add_header("Authorization", f"Bearer {api_key}")
    with urllib.request.urlopen(req, jsondataasbytes, context=ctx) as response:
        s3_access = json.loads(response.read().decode("utf-8"))

    return s3_access


def upload_to_s3(s3_access, build_file, s3_path):
    """
    Upload a local file to a S3 bucket using the provided access data.

    `s3_access` is a dictionary with access information from the
    PythonDeploy API.
    """
    print("Uploading file to S3")
    bucket = (
        Session(
            aws_access_key_id=s3_access["credentials"]["aws_access_key_id"],
            aws_secret_access_key=s3_access["credentials"]["aws_secret_access_key"],
            aws_session_token=s3_access["credentials"]["aws_session_token"],
            region_name=s3_access["credentials"]["region_name"],
        )
        .resource("s3")
        .Bucket(s3_access["bucket"])
    )

    bucket.upload_file(build_file, s3_path)

    s3_url = f"s3://{s3_access['bucket']}/{s3_path}"
    print(f"Successfully uploaded '{build_file}' to '{s3_url}'")


def lambda_update(app_id, api_key, s3_path):
    """Push the uploaded code to the Lambda functions using PythonDeploy."""
    print("Deploying code to Lambda functions")

    jsondata = json.dumps({"action": "lambda_deploy", "s3_path": s3_path})
    jsondataasbytes = jsondata.encode("utf-8")

    req = urllib.request.Request(PD_API_URL.format(app_id=app_id))
    req.add_header("Content-Length", len(jsondataasbytes))
    req.add_header("Content-Type", "application/json; charset=utf-8")
    req.add_header("Authorization", f"Bearer {api_key}")
    urllib.request.urlopen(req, jsondataasbytes, context=ctx)


def deploy(app_id, api_key, s3_path):
    """Upload the build ZIP file to the application's S3 bucket."""
    build_dir = get_build_dir()
    build_file = str(Path(build_dir) / BUILD_FILE_NAME)

    if not app_id:
        raise ValueError("Missing App ID.")

    if not api_key:
        raise ValueError("Missing Api Key.")

    try:
        s3_access = get_s3_access_data(app_id, api_key)
    except urllib.error.HTTPError as error:
        if error.status == 404:
            raise ValueError("Invalid or unknown AppId.")
        raise

    upload_to_s3(s3_access, build_file, s3_path)
    lambda_update(app_id, api_key, s3_path)


def _deploy_args(parser):
    """Add arguments required to run deploy()."""
    parser.add_argument(
        "--s3-path",
        help=(
            "s3 path to upload the ZIP to. Default: 'python_deploy/{timestamp}.zip'"
        ),
        default="python_deploy/{timestamp}.zip".format(timestamp=int(time.time())),
    )
    parser.add_argument(
        "--app-id",
        help="PythonDeploy application id. Default: environment variable PD_APP_ID ",
        required=False,
        default=os.environ.get("PD_APP_ID"),
    )
    parser.add_argument(
        "--api-key",
        help="PythonDeploy api key. Default: environment variable PD_API_KEY ",
        required=False,
        default=os.environ.get("PD_API_KEY"),
    )


def run():
    """CLI access to the deploy function."""
    parser = argparse.ArgumentParser(
        description=(
            "Deploy the built ZIP file to the AWS lambda functions. The ZIP file is"
            " uploaded to the private S3 bucket."
        )
    )
    _deploy_args(parser)

    args = parser.parse_args()
    s3_path = args.s3_path.lstrip("/")
    app_id = args.app_id
    api_key = args.api_key

    deploy(app_id, api_key, s3_path)
