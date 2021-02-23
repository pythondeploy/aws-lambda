"""Handler to execute shell commands."""
from subprocess import run


def handler(event: dict, _context: object):
    """
    Execute shell commands.

    `subprocess.run` is passed the `args` key from the event as the first positional
    argument.

    If "log_result" is True, the the result is also printed so it gets logged
    into CloudWatch.

    A dictionary with the exit status code and the captured `stdout` and `stderr`
    is returned.

    :param event: The Lambda event information.
    :type event: dict
    :param _context: The Lambda invocation context object.
        https://docs.aws.amazon.com/lambda/latest/dg/python-context.html
    :type _context: [type]
    :return: dictionary with the captured `stdout` and `stderr`.
    :rtype: dict
    """
    completed_process = run(event["args"], capture_output=True, text=True)
    result = {
        "returncode": completed_process.returncode,
        "stdout": completed_process.stdout,
        "stderr": completed_process.stderr,
    }

    if event.get("log_result") is True:
        print(result)

    return result
