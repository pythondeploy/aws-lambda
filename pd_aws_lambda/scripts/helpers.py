"""Define helper used across multiple PythonDeploy scripts."""
import hashlib
import json
import os
import ssl
import tempfile
import urllib.request
from pathlib import Path
from shutil import rmtree

BUILD_FILE_NAME = Path("pd_build.zip")
PACKAGES_DIR_PATH = Path("packages")
PD_API_DOMAIN = os.environ.get("PD_API_DOMAIN", "api.pythondeploy.co")
PD_API_URL = f"https://{PD_API_DOMAIN}/applications/{{app_id}}/api/"


ctx = None
if os.environ.get("PD_SKIP_CERT_VALIDATION") == "skip":
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE


def get_build_dir(clean=False):
    """
    Return the directory to use for building the packages.

    If a an environment variable `PD_BUILD_DIR` exists, then its value is used,
    if not, a temporary directory is generated based on the md5 has of the
    current working directory absolute path.

    We need a deterministic temp path so the method can be used from
    different invocations without having to share a state.
    """
    build_dir = os.environ.get("PD_BUILD_DIR")
    if build_dir:
        return Path(build_dir)

    tmp_path = (
        Path(tempfile.gettempdir())
        / Path("pd")
        / hashlib.md5(str(Path(".").absolute()).encode("utf-8")).hexdigest()
    )
    if clean and tmp_path.exists():
        rmtree(tmp_path)

    os.makedirs(tmp_path, exist_ok=True)

    return tmp_path


def get_aws_account_information(app_id, api_key):
    """Retrieve aws account information from PythonDeploy."""
    print("Requesting aws account information")

    jsondata = json.dumps({"action": "aws_account"})
    jsondataasbytes = jsondata.encode("utf-8")

    req = urllib.request.Request(PD_API_URL.format(app_id=app_id))
    req.add_header("Content-Length", len(jsondataasbytes))
    req.add_header("Content-Type", "application/json; charset=utf-8")
    req.add_header("Authorization", f"Bearer {api_key}")

    try:
        with urllib.request.urlopen(req, jsondataasbytes, context=ctx) as response:
            aws_account = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        if error.status == 404:
            raise ValueError("Invalid or unknown AppId.")
        raise

    return aws_account
