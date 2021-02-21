"""Handler that logs its input to a Python logger."""
import logging

logger = logging.getLogger(__name__)
logger.setLevel("INFO")


def handler(event: dict, context: object):
    """
    Log the event and context objects.

    :param event: The Lambda event information.
    :type event: dict
    :param context: The Lambda invocation context object.
        https://docs.aws.amazon.com/lambda/latest/dg/python-context.html
    :type context: [type]
    """
    logger.info("Lambda event: %s", event)
    logger.info("Lambda context: %s", context.__dict__)
