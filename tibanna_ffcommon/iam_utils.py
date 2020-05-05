from tibanna.iam_utils import IAM as _IAM
from .vars import (
    RUN_TASK_LAMBDA_NAME,
    CHECK_TASK_LAMBDA_NAME
)


class IAM(_IAM):

    run_task_lambda_name = RUN_TASK_LAMBDA_NAME
    check_task_lambda_name = CHECK_TASK_LAMBDA_NAME
