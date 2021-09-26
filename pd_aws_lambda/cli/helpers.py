"""Define helpers used across multiple PythonDeploy scripts."""
import json
import os
import ssl
import urllib.request
from typing import Any, Dict, Optional

from .. import __version__

import typer

PD_API_DOMAIN = os.environ.get("PD_API_DOMAIN", "api.pythondeploy.co")
PD_API_URL = f"https://{PD_API_DOMAIN}/applications/{{app_id}}/api/"


ctx = None
if os.environ.get("_PD_SKIP_CERT_VALIDATION") == "skip":
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE


def get_aws_account_information(app_id: str, api_key: str) -> Dict[str, Any]:
    """Retrieve aws account information from PythonDeploy."""
    typer.echo("Requesting aws account information")

    return api_request(app_id, api_key, "aws_account")


def api_request(
    app_id: str, api_key: str, action: str, data: Optional[Dict[Any, Any]] = None
) -> Any:
    data = data or {}
    jsondata = json.dumps({**data, "action": action})
    jsondataasbytes = jsondata.encode("utf-8")

    req = urllib.request.Request(PD_API_URL.format(app_id=app_id))
    req.add_header("Content-Length", str(len(jsondataasbytes)))
    req.add_header("Content-Type", "application/json; charset=utf-8")
    req.add_header("Authorization", f"Bearer {api_key}")
    req.add_header("PD-version", __version__)

    try:
        with urllib.request.urlopen(req, jsondataasbytes, context=ctx) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        if error.status == 404:
            raise ValueError("Invalid or unknown AppId.")
        raise
