from tibanna.iam_utils import IAM as _IAM
from .vars import (
    RUN_TASK_LAMBDA_NAME,
    CHECK_TASK_LAMBDA_NAME,
    UPDATE_COST_LAMBDA_NAME,
    START_RUN_LAMBDA_NAME,
    UPDATE_FFMETA_LAMBDA_NAME,
    RUN_WORKFLOW_LAMBDA_NAME,
    STATUS_WFR_LAMBDA_NAME,
    VALIDATE_MD5_S3_INITIATOR_LAMBDA_NAME,
    VALIDATE_MD5_S3_TRIGGER_LAMBDA_NAME
)


class IAM(_IAM):

    run_task_lambda_name = RUN_TASK_LAMBDA_NAME
    check_task_lambda_name = CHECK_TASK_LAMBDA_NAME
    update_cost_lambda_name = UPDATE_COST_LAMBDA_NAME
    start_run_lambda_name = START_RUN_LAMBDA_NAME
    update_ffmeta_lambda_name = UPDATE_FFMETA_LAMBDA_NAME
    run_workflow_lambda_name = RUN_WORKFLOW_LAMBDA_NAME
    status_wfr_lambda_name = STATUS_WFR_LAMBDA_NAME
    validate_md5_s3_initiator_lambda_name = VALIDATE_MD5_S3_INITIATOR_LAMBDA_NAME
    validate_md5_s3_trigger_lambda_name = VALIDATE_MD5_S3_TRIGGER_LAMBDA_NAME

    @property
    def lambda_names(self):
        return [self.run_task_lambda_name, self.check_task_lambda_name,
                self.start_run_lambda_name, self.update_ffmeta_lambda_name,
                self.run_workflow_lambda_name, self.status_wfr_lambda_name,
                self.validate_md5_s3_initiator_lambda_name,
                self.validate_md5_s3_trigger_lambda_name,
                self.update_cost_lambda_name]

    @property
    def policy_arn_list_for_role(self):
        """returns a dictionary with role_type as keys"""
        arnlist = super().policy_arn_list_for_role

        general_lambda_policy_types = ['vpc', 'bucket', 'cloudwatch', 'dynamodb']
        execution_lambda_policy_types = general_lambda_policy_types + ['executions']

        arnlist[self.start_run_lambda_name] = [self.policy_arn(_) for _ in general_lambda_policy_types]
        arnlist[self.update_ffmeta_lambda_name] = [self.policy_arn(_) for _ in general_lambda_policy_types]
        arnlist[self.run_workflow_lambda_name] = [self.policy_arn(_) for _ in execution_lambda_policy_types]
        arnlist[self.status_wfr_lambda_name] = [self.policy_arn(_) for _ in execution_lambda_policy_types]
        arnlist[self.validate_md5_s3_initiator_lambda_name] = [self.policy_arn(_) for _ in execution_lambda_policy_types]
        arnlist[self.validate_md5_s3_trigger_lambda_name] = [self.policy_arn(_) for _ in execution_lambda_policy_types]

        return arnlist
