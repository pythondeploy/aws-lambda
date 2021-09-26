"""CLI command to run shell commands on a Lambda Function."""
import json
import os
from pprint import pformat
from typing import List, Optional

import typer
from boto3 import Session

from .exceptions import LambdaInvocationFailed, ShellCommandFailed, UnexpectedResponse
from .helpers import get_aws_account_information


def run_shell(
    shell_args: Optional[List[str]], log_result: bool, app_id: str, api_key: str
) -> None:
    """
    Run a shell command in the Tasks lambda function.

    `stdout` and and `stderr` from the ran command are printed locally
    in their corresponding stream.

    The python process exits with the same return code from the command.

    If the lambda function fails to execute or it is not possible to execute
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

    typer.echo("Invoking Lambda function")
    response = lambda_client.invoke(
        FunctionName=aws_account["tasks_function"],
        Payload=json.dumps(payload).encode(),
    )

    if response["StatusCode"] != 200:
        raise LambdaInvocationFailed(
            "Lambda execution failed", response.get("FunctionError")
        )

    result = json.loads(response["Payload"].read().decode())

    if not isinstance(result, dict):
        raise UnexpectedResponse(result)

    if "FunctionError" in response:
        typer.echo(pformat(result["errorMessage"]), err=True)
        raise ShellCommandFailed("Shell command failed", result["errorType"])

    if result["stdout"]:
        typer.echo(result["stdout"].strip("\n"))

    if result["stderr"]:
        typer.echo(result["stderr"].strip("\n"), err=True)

    exit(result["returncode"])


def run_command(
    shell_args: Optional[List[str]] = typer.Argument(
        None, help="Arguments to pass to the `subprocess.run()` method."
    ),
    log_result: bool = typer.Option(False, help="Log the results into AWS CloudWatch."),
    app_id: str = typer.Option(
        os.environ.get("PD_APP_ID"),
        help="PythonDeploy application id. Default: environment variable PD_APP_ID",
    ),
    api_key: str = typer.Option(
        os.environ.get("PD_API_KEY"),
        help="PythonDeploy api key. Default: environment variable PD_API_KEY",
    ),
) -> None:
    """Execute shell commands in your Lambda Task function."""
    run_shell(shell_args, log_result, app_id, api_key)
