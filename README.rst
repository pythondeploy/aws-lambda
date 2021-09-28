===================================
Python Deploy AWS Lambda Dispatcher
===================================

.. image:: https://badge.fury.io/py/pd-aws-lambda.svg
    :target: https://badge.fury.io/py/pd-aws-lambda
.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
    :target: https://github.com/ambv/black

Handle AWS Lambda events.

Events are passed to handlers for processing.
Each event is passed to the handler in this order:

- Handler defined in the event
- HTTP events handler (for WSGI applications)
- SQS events handler (if configured)
- Default handler (if configured)
- Logger handler (if no default is defined)

Provided Handlers
-----------------

- `pd_aws_lambda.handlers.wsgi.handler`: convert HttpAPI requests to WSGI environs.
- `pd_aws_lambda.handlers.shell.handler`: Run shell commands.
- `pd_aws_lambda.handlers.logger.handler`: log the received event and context.

Usage
-----

1. Add `pd_aws_lambda` to your application dependencies.

   .. code-block:: console

    poetry add pd_aws_lambda

2. Set the required environment variables according to your needs in your
   `Python Deploy`_ application configuration.

   .. code-block:: ini

    # Python path to the WSGI application that will handle HTTP requests.
    PD_WSGI_APPLICATION=my_django_project.wsgi.application

    # Python path to the handler for SQS events.
    PD_SQS_HANDLER=my_custom_handlers.sqs_handler

    # Python path to the default fallback handler.
    PD_DEFAULT_HANDLER=my_custom_handlers.default_handler

Custom handlers
---------------

A handler is a python function that receives an `event` and a `context` and
does something with them. It can return a value if it makes sense for the type
of event. For example, HttpAPI handlers like the one we use to call your wsgi
application (`pd_aws_lambda.handlers.wsgi.handler`) should return a dictionary
compatible with the `AWS HttpAPI`_ to form an HTTP response.

.. code-block:: python

    def handler(event, context):
        """
        I handle AWS Lambda invocations.

        I print the received event and context.
        """
        print("The event:", event)
        print("The context:", context)

----

`Python Deploy`_

.. _AWS HttpAPI: https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-develop-integrations-lambda.html
.. _Python Deploy: https://pythondeploy.co
