from tibanna.iam_utils import IAM as _IAM
from .vars import (
    RUN_TASK_LAMBDA_NAME,
    CHECK_TASK_LAMBDA_NAME,
    UPDATE_COST_LAMBDA_NAME,
    START_RUN_LAMBDA_NAME,
    UPDATE_FFMETA_LAMBDA_NAME
)


class IAM(_IAM):

    run_task_lambda_name = RUN_TASK_LAMBDA_NAME
    check_task_lambda_name = CHECK_TASK_LAMBDA_NAME
    update_cost_lambda_name = UPDATE_COST_LAMBDA_NAME
    start_run_lambda_name = START_RUN_LAMBDA_NAME
    update_ffmeta_lambda_name = UPDATE_FFMETA_LAMBDA_NAME

    @property
    def policy_arn_list_for_role(self):
        """returns a dictionary with role_type as keys"""
        arnlist = super().policy_arn_list_for_role

        start_run_custom_policy_types = ['vpc']
        update_ffmeta_custom_policy_types = ['vpc']

        arnlist[self.start_run_lambda_name] = [self.policy_arn(_) for _ in start_run_custom_policy_types]
        arnlist[self.update_ffmeta_lambda_name] = [self.policy_arn(_) for _ in update_ffmeta_custom_policy_types]

        return arnlist
