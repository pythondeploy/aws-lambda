"""CLI command to deploy a Docker image to the Lambda Functions."""
import os
from base64 import b64decode
from time import sleep, time
from typing import Any, Dict, Generator

import docker
import typer
from boto3 import Session

from .exceptions import CloudFormationTransofrmationFailed, ECRPushFailed
from .helpers import api_request, get_aws_account_information


def push_to_ecr(aws_account: Dict[str, Any], image_tag: str) -> str:
    """
    Push the docker image to the ECR repository.

    `aws_account` is a dictionary with access information from the
    PythonDeploy API.
    """
    typer.echo("Pushing image to ECR")

    ecr_client = Session(
        aws_access_key_id=aws_account["credentials"]["aws_access_key_id"],
        aws_secret_access_key=aws_account["credentials"]["aws_secret_access_key"],
        aws_session_token=aws_account["credentials"]["aws_session_token"],
        region_name=aws_account["credentials"]["region_name"],
    ).client("ecr")

    docker_registry = aws_account["ecr_registry_private"]
    now_timestamp = str(time())
    authorization_token = ecr_client.get_authorization_token()

    docker_client = docker.from_env()
    user, password = (
        b64decode(authorization_token["authorizationData"][0]["authorizationToken"])
        .decode("utf-8")
        .split(":", 1)
    )
    docker_client.login(
        user,
        password,
        registry=docker_registry,
        reauth=True,
    )
    docker_image = docker_client.images.get(image_tag)
    docker_image.tag(docker_registry, now_timestamp)
    push_output = docker_client.images.push(
        docker_registry, now_timestamp, stream=True, decode=True
    )
    uploaded = False
    last_output = None
    for output in push_output:
        last_output = output
        status = output.get("status", None)
        if status and status.startswith(f"{now_timestamp}: digest: "):
            uploaded = True

    if not uploaded:
        raise ECRPushFailed(last_output)

    docker_image_uri = f"{docker_registry}:{now_timestamp}"
    typer.echo(f"Successfully pushed '{docker_image_uri}'")
    return docker_image_uri


def lambda_update(app_id: str, api_key: str, image_uri: str) -> None:
    """Push the uploaded code to the Lambda functions using PythonDeploy."""
    typer.echo("Deploying docker image to Lambda functions")
    api_request(app_id, api_key, "lambda_deploy", {"image_uri": image_uri})


def exponential() -> Generator[int, None, None]:
    """Exponentially increasing generator, with a max value of 10."""
    n = 0
    limit = 10
    while True:
        exp = 0.5 * 2 ** n
        if exp > 10:
            yield 10

        yield limit
        n += 1


def cloud_formation_wait(aws_account: Dict[str, Any]) -> None:
    """
    Wait until the CloudFormation stack finishes applying changes.

    The Stack might not be ready to accept new changes, but the new code
    has been deployed to the functions.

    If the changes fail to be applied, an exception is raised.
    - pd_aws_lambda.exceptions.CloudFormationTransofrmationFailed
    """
    for sleep_time in exponential():
        typer.echo("Waiting for CloudFormation changes")
        stack_status = (
            Session(
                aws_access_key_id=aws_account["credentials"]["aws_access_key_id"],
                aws_secret_access_key=aws_account["credentials"][
                    "aws_secret_access_key"
                ],
                aws_session_token=aws_account["credentials"]["aws_session_token"],
                region_name=aws_account["credentials"]["region_name"],
            )
            .client("cloudformation")
            .describe_stacks(StackName=aws_account["stack_name"], NextToken="string")[
                "Stacks"
            ][0]["StackStatus"]
        )

        if stack_status != "UPDATE_IN_PROGRESS":
            break

        sleep(sleep_time)

    if stack_status not in [
        "UPDATE_COMPLETE_CLEANUP_IN_PROGRESS",
        "UPDATE_COMPLETE",
    ]:
        raise CloudFormationTransofrmationFailed(stack_status)


def deploy_command(
    image_tag: str = typer.Argument(
        ...,
        help="Local docker image tag to be deployed",
    ),
    app_id: str = typer.Option(
        os.environ.get("PD_APP_ID"),
        help="PythonDeploy application id. Default: environment variable PD_APP_ID",
    ),
    api_key: str = typer.Option(
        os.environ.get("PD_API_KEY"),
        help="PythonDeploy api key. Default: environment variable PD_API_KEY",
    ),
    wait: bool = typer.Option(
        False,
        help=(
            "By default this command exits as soon as AWS receives the"
            " changes. If `--wait` is given, then the command finishes when"
            " the changes either are applied successfully, or failed to apply."
        ),
    ),
) -> None:
    """Deploy a Docker image to your Python Deploy Lambda functions."""
    aws_account = get_aws_account_information(app_id, api_key)

    image_uri = push_to_ecr(aws_account, image_tag)
    lambda_update(app_id, api_key, image_uri)
    if wait:
        cloud_formation_wait(aws_account)
