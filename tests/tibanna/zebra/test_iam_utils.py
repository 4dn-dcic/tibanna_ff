from tibanna_cgap import iam_utils
from tibanna_cgap.vars import AWS_ACCOUNT_NUMBER
import pytest


@pytest.fixture
def expected_policy_arn_list_for_cgap():
    prefix = 'arn:aws:iam::%s:policy/' % AWS_ACCOUNT_NUMBER
    return {'check_task': [prefix + 'tibanna_zebra_cgap_cw_metric',
                           prefix + 'tibanna_zebra_cgap_cloudwatchlogs',
                           prefix + 'tibanna_zebra_cgap_bucket_access',
                           prefix + 'tibanna_zebra_cgap_ec2_desc',
                           prefix + 'tibanna_zebra_cgap_ec2_termination',
                           prefix + 'tibanna_zebra_cgap_dynamodb',
                           prefix + 'tibanna_zebra_cgap_pricing',
                           prefix + 'tibanna_zebra_cgap_vpc_access'],
            'ec2': [prefix + 'tibanna_zebra_cgap_bucket_access',
                    prefix + 'tibanna_zebra_cgap_cw_metric',
                    'arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly'],
            'run_task': [prefix + 'tibanna_zebra_cgap_list_instanceprofiles',
                         prefix + 'tibanna_zebra_cgap_cloudwatchlogs',
                         prefix + 'tibanna_zebra_cgap_iam_passrole_s3',
                         prefix + 'tibanna_zebra_cgap_bucket_access',
                         prefix + 'tibanna_zebra_cgap_dynamodb',
                         prefix + 'tibanna_zebra_cgap_executions',
                         prefix + 'tibanna_zebra_cgap_cw_dashboard',
                         'arn:aws:iam::aws:policy/AmazonEC2FullAccess'],
            'run_workflow': [prefix + 'tibanna_zebra_cgap_vpc_access',
                             prefix + 'tibanna_zebra_cgap_bucket_access',
                             prefix + 'tibanna_zebra_cgap_cloudwatchlogs',
                             prefix + 'tibanna_zebra_cgap_dynamodb',
                             prefix + 'tibanna_zebra_cgap_executions'],
            'start_run': [prefix + 'tibanna_zebra_cgap_vpc_access',
                          prefix + 'tibanna_zebra_cgap_bucket_access',
                          prefix + 'tibanna_zebra_cgap_cloudwatchlogs',
                          prefix + 'tibanna_zebra_cgap_dynamodb',
                          prefix + 'ElasticBeanstalkFullAccess'],
            'status_wfr': [prefix + 'tibanna_zebra_cgap_vpc_access',
                           prefix + 'tibanna_zebra_cgap_bucket_access',
                           prefix + 'tibanna_zebra_cgap_cloudwatchlogs',
                           prefix + 'tibanna_zebra_cgap_dynamodb',
                           prefix + 'tibanna_zebra_cgap_executions'],
            'stepfunction': ['arn:aws:iam::aws:policy/service-role/AWSLambdaRole'],
            'update_cost': [prefix + 'tibanna_zebra_cgap_bucket_access',
                            prefix + 'tibanna_zebra_cgap_executions',
                            prefix + 'tibanna_zebra_cgap_dynamodb',
                            prefix + 'tibanna_zebra_cgap_pricing',
                            prefix + 'tibanna_zebra_cgap_vpc_access'],
            'update_ffmeta': [prefix + 'tibanna_zebra_cgap_vpc_access',
                              prefix + 'tibanna_zebra_cgap_bucket_access',
                              prefix + 'tibanna_zebra_cgap_cloudwatchlogs',
                              prefix + 'tibanna_zebra_cgap_dynamodb',
                              prefix + 'ElasticBeanstalkFullAccess']}


def test_policy_prefix(expected_policy_arn_list_for_cgap):
    iam = iam_utils.IAM(user_group_tag='cgap')
    assert iam.tibanna_policy_prefix == 'tibanna_zebra_cgap'
    assert iam.policy_arn_list_for_role == expected_policy_arn_list_for_cgap
