"""Handler to invoke a Django management command."""
import logging
from io import StringIO

import django
from django.core.management import call_command

logger = logging.getLogger(__name__)
logger.setLevel("INFO")


def handler(event: dict, _context: object):
    """
    Execute a Django command using `django.core.management.call_command`.

    The command is passed the `args` key from the event as `*args` and the `kwargs`
    key as `**kwargs`.

    The command can be passed as the first element in the `args` list, or as the
    `command_name` key in the `kwargs` dict.

    No validations are made regarding the parameters passed to `call_command`.

    :param event: The Lambda event information.
    :type event: dict
    :param _context: The Lambda invocation context object.
        https://docs.aws.amazon.com/lambda/latest/dg/python-context.html
    :type _context: object
    :return: A dict with `stdout` and `stderr` from the command invocation.
    :rtype: dict
    """
    stdout = StringIO()
    stderr = StringIO()

    django.setup(set_prefix=False)

    call_command(
        *event.get("args", []), stdout=stdout, stderr=stderr, **event.get("kwargs", {})
    )
    response = {"stdout": stdout.getvalue(), "stderr": stderr.getvalue()}
    stdout.close()
    stderr.close()

    return response
