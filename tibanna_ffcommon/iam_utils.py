from tibanna.iam_utils import IAM
from .vars import (
    AWS_ACCOUNT_NUMBER,
    AWS_REGION,
    LAMBDA_TYPE,
    RUN_TASK_LAMBDA_NAME,
    CHECK_TASK_LAMBDA_NAME
)


class IAM(_IAM):

    account_id = AWS_ACCOUNT_NUMBER
    region = AWS_REGION
    lambda_type = LAMBDA_TYPE  # lambda_type : '' for unicorn, 'pony' for pony, 'zebra' for zebra
    run_task_lambda_name = RUN_TASK_LAMBDA_NAME
    check_task_lambda_name = CHECK_TASK_LAMBDA_NAME
