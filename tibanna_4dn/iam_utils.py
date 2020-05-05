from tibanna_ffcommon.iam_utils import IAM as _IAM
from .vars import (
    LAMBDA_TYPE,
)


class IAM(_IAM):

    lambda_type = LAMBDA_TYPE  # lambda_type : '' for unicorn, 'pony' for pony, 'zebra' for zebra
