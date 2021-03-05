"""Define exceptions for PD Aws Lambda package."""


class CloudFormationTransofrmationFailed(Exception):
    """The changes to CloudFormation failed to apply."""
