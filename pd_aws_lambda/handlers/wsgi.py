"""This module converts an AWS API Gateway proxied request to a WSGI request."""

from apig_wsgi import (
    DEFAULT_NON_BINARY_CONTENT_TYPE_PREFIXES,
    V2Response,
    get_environ_v2,
)


def handler(app, event, context):
    """Process an HTTP Lambda request with `apig_wsgi`."""
    environ = get_environ_v2(event, context, binary_support=True)
    response = V2Response(
        binary_support=True,
        non_binary_content_type_prefixes=DEFAULT_NON_BINARY_CONTENT_TYPE_PREFIXES,
    )

    result = app(environ, response.start_response)
    response.consume(result)
    return response.as_apig_response()
