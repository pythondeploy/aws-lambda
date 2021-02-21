"""Handler to execute custom python code."""


def handler(event: dict, _context: object):
    """
    Execute python code.

    `exec` is passed the `args` key from the event as `*args` and the `kwargs`
    key as `**kwargs`.

    :param event: The Lambda event information.
    :type event: dict
    :param _context: The Lambda invocation context object.
        https://docs.aws.amazon.com/lambda/latest/dg/python-context.html
    :type _context: [type]
    """
    exec(*event["args"], **event["kwargs"])  # type: ignore  # pylint: disable=exec-used
