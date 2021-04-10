"""This module converts an AWS API Gateway proxied request to a WSGI request."""
from codecs import decode, encode

from apig_wsgi import (
    DEFAULT_NON_BINARY_CONTENT_TYPE_PREFIXES,
    V2Response,
    get_environ_v2,
)


def handler(app, event, context):
    """Process an HTTP Lambda request with `apig_wsgi`."""
    environ = get_environ_v2(event, context, binary_support=True)

    # https://stackoverflow.com/questions/1885181/how-to-un-escape-a-backslash-escaped-string/57192592#57192592
    # https://github.com/adamchainz/apig-wsgi/issues/219
    environ["HTTP_COOKIE"] = decode(
        encode(environ["HTTP_COOKIE"], "latin-1", "backslashreplace"), "unicode-escape"
    )
    # WSGI should be iso-8859-1 encoded, but lambda provides utf-8 strings, and
    # `apig_wsgi` is not taking that into account.
    environ["PATH_INFO"] = (
        environ["PATH_INFO"].encode("utf-8", "replace").decode("iso-8859-1", "replace")
    )

    response = V2Response(
        binary_support=True,
        non_binary_content_type_prefixes=DEFAULT_NON_BINARY_CONTENT_TYPE_PREFIXES,
    )

    result = app(environ, response.start_response)
    response.consume(result)
    return response.as_apig_response()
