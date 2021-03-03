"""Dispatcher for Lambda events."""
import importlib
import logging
import os

from .handlers.logger import handler as logger_handler
from .handlers.wsgi import handler as wsgi_handler

logger = logging.getLogger(__name__)


def import_module_attribute(function_path):
    """Import and return a module attribute given a full path."""
    module, attribute = function_path.rsplit(".", 1)
    app_module = importlib.import_module(module)
    return getattr(app_module, attribute)


# Create a single application instance that will be reused in
# all the requests that the LambdaFunction processes.
# Faster than instantiating the application in every request.
#
# AWS_LAMBDA_FUNCTION_NAME is part of the variables set by AWS.
# https://docs.aws.amazon.com/lambda/latest/dg/configuration-envvars.html#configuration-envvars-runtime
WSGI_APPLICATION = (
    import_module_attribute(os.environ.get("PD_WSGI_APPLICATION"))
    if "HttpFunction" in os.environ.get("AWS_LAMBDA_FUNCTION_NAME", "")
    and os.environ.get("PD_WSGI_APPLICATION")
    else None
)


def is_sqs(event: dict):
    """Return True if the event seems to come from SQS."""
    records = event.get("Records")
    return (
        isinstance(records, list)
        and records
        and records[0].get("eventSource") == "aws:sqs"
    )


def dispatcher(event: dict, context):
    """Dispatch the lambda event to the appropriate handler."""
    # Did we get a request for a specific handler?
    handler_path = event.get("handler_path")
    if handler_path:
        return import_module_attribute(handler_path)(event, context)

    # We got an HttpAPI request.
    if WSGI_APPLICATION and "requestContext" in event and "version" in event:
        return wsgi_handler(WSGI_APPLICATION, event, context)

    # We got an SQS invocation, do we know how to handle it?
    if os.environ.get("PD_SQS_HANDLER") and is_sqs(event):
        return import_module_attribute(os.environ.get("PD_SQS_HANDLER"))(event, context)

    # Use default handler, if there is one.
    if os.environ.get("PD_DEFAULT_HANDLER"):
        return import_module_attribute(os.environ.get("PD_DEFAULT_HANDLER"))(
            event, context
        )

    # Not handled by anyone.
    logger.error("No handler found for this event")
    return logger_handler(event, context)
