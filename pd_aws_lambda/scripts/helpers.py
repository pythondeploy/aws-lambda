"""Define helper used across multiple PythonDeploy scripts."""
import os
import tempfile
from pathlib import Path
from shutil import rmtree
import hashlib

BUILD_FILE_NAME = Path("pd_build.zip")
PACKAGES_DIR_PATH = Path("packages")
PD_API_DOMAIN = os.environ.get("PD_API_DOMAIN", "api.pythondeploy.co")
PD_API_URL = f"https://{PD_API_DOMAIN}/applications/{{app_id}}/api/"


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
