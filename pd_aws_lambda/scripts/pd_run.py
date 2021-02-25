"""Script to run shell commands on a Lambda Function."""
import argparse
import json
import os
import sys
from pprint import pprint

from boto3 import Session

from .helpers import get_aws_account_information


class LambdaInvocationFailed(Exception):
    """The invokation of the Lambda function failed."""


class ShellCommandFailed(Exception):
    """The invoked shell command failed."""


class UnexpectedResponse(Exception):
    """The response from the LambdaFunction has an unknown format."""


def run_shell(shell_args, log_result, app_id, api_key):
    """
    Run a shell command in the Tasks lambda function.

    `stdout` and and `stderr` form the ran command are printed locally
    in their corresponding stream.

    The python process exits with the same return code form the ran command.

    If the lambda function fails to execute, or it is not possible to execute
    the shell command, an exception is raised.
    """
    aws_account = get_aws_account_information(app_id, api_key)

    lambda_client = Session(
        aws_access_key_id=aws_account["credentials"]["aws_access_key_id"],
        aws_secret_access_key=aws_account["credentials"]["aws_secret_access_key"],
        aws_session_token=aws_account["credentials"]["aws_session_token"],
        region_name=aws_account["credentials"]["region_name"],
    ).client("lambda")

    payload = {
        "args": shell_args,
        "log_result": log_result,
        "handler_path": "pd_aws_lambda.handlers.shell.handler",
    }

    print("Invoking Lambda function")
    response = lambda_client.invoke(
        FunctionName=aws_account["tasks_function"],
        Payload=json.dumps(payload).encode(),
    )

    if response["StatusCode"] != 200:
        raise LambdaInvocationFailed("Lambda execution failed", response.get("FunctionError"))

    result = json.loads(response["Payload"].read().decode())

    if not isinstance(result, dict):
        raise UnexpectedResponse(result)

    if "FunctionError" in response:
        pprint(result["errorMessage"], stream=sys.stderr)
        raise ShellCommandFailed("Shell command failed", result["errorType"])

    if result["stdout"]:
        print(result["stdout"].strip("\n"))

    if result["stderr"]:
        print(result["stderr"].strip("\n"), file=sys.stderr)

    exit(result["returncode"])


def run():
    """CLI access to the build and deploy functions."""
    parser = argparse.ArgumentParser(
        description="Execute shell commands in your Lambda Task function."
    )
    parser.add_argument(
        "shell_args",
        nargs="+",
        help="Arguments to pass to the `subprocess.run()` method.",
    )
    parser.add_argument(
        "--log-result",
        action="store_true",
        help="Log the results into AWS CloudWatch.",
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

    args = parser.parse_args()
    run_shell(args.shell_args, args.log_result, args.app_id, args.api_key)
