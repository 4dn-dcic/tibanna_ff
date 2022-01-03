from tibanna.iam_utils import IAM as _IAM
from .vars import (
    RUN_TASK_LAMBDA_NAME,
    CHECK_TASK_LAMBDA_NAME,
    UPDATE_COST_LAMBDA_NAME,
    START_RUN_LAMBDA_NAME,
    UPDATE_FFMETA_LAMBDA_NAME,
    S3_ENCRYPT_KEY_ID,
)


class IAM(_IAM):

    run_task_lambda_name = RUN_TASK_LAMBDA_NAME
    check_task_lambda_name = CHECK_TASK_LAMBDA_NAME
    update_cost_lambda_name = UPDATE_COST_LAMBDA_NAME
    start_run_lambda_name = START_RUN_LAMBDA_NAME
    update_ffmeta_lambda_name = UPDATE_FFMETA_LAMBDA_NAME

    @property
    def lambda_names(self):
        return [self.run_task_lambda_name, self.check_task_lambda_name,
                self.start_run_lambda_name, self.update_ffmeta_lambda_name,
                self.update_cost_lambda_name]

    @property
    def policy_arn_list_for_role(self):
        """returns a dictionary with role_type as keys"""
        arnlist = super().policy_arn_list_for_role

        general_lambda_policy_types = ['vpc', 'bucket', 'cloudwatch', 'dynamodb']
        if S3_ENCRYPT_KEY_ID:  # if we have a value, this key is valid and we must add perms
            general_lambda_policy_types.append('kms')

        # Give EB read access to tibanna (for now, so perms are compatible in legacy account) - Will Sept 22 2021
        arnlist[self.start_run_lambda_name] = [self.policy_arn(_) for _ in general_lambda_policy_types] + \
                                              ['arn:aws:iam::aws:policy/AWSElasticBeanstalkReadOnly']
        arnlist[self.run_task_lambda_name] += ['arn:aws:iam::aws:policy/AWSElasticBeanstalkReadOnly']
        arnlist[self.check_task_lambda_name] += ['arn:aws:iam::aws:policy/AWSElasticBeanstalkReadOnly']
        arnlist[self.update_cost_lambda_name] += ['arn:aws:iam::aws:policy/AWSElasticBeanstalkReadOnly']
        arnlist[self.update_ffmeta_lambda_name] = [self.policy_arn(_) for _ in general_lambda_policy_types] + \
                                                  ['arn:aws:iam::aws:policy/AWSElasticBeanstalkReadOnly']

        return arnlist
