from tibanna_cgap import iam_utils
from tibanna_cgap.vars import AWS_ACCOUNT_NUMBER
import pytest


@pytest.fixture
def expected_policy_arn_list_for_cgap():
    prefix = 'arn:aws:iam::%s:policy/' % AWS_ACCOUNT_NUMBER
    return {'check_task': [prefix + 'tibanna_zebra_cgap_vpc_access',
                           prefix + 'tibanna_zebra_cgap_cw_metric',
                           prefix + 'tibanna_zebra_cgap_cloudwatchlogs',
                           prefix + 'tibanna_zebra_cgap_bucket_access',
                           prefix + 'tibanna_zebra_cgap_ec2_desc',
                           prefix + 'tibanna_zebra_cgap_ec2_termination',
                           prefix + 'tibanna_zebra_cgap_dynamodb',
                           prefix + 'tibanna_zebra_cgap_pricing',
                           'arn:aws:iam::aws:policy/AWSElasticBeanstalkReadOnly'],
            'ec2': [prefix + 'tibanna_zebra_cgap_bucket_access',
                    prefix + 'tibanna_zebra_cgap_cw_metric',
                    prefix + 'tibanna_zebra_cgap_ec2_desc',
                    'arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly',
                    'arn:aws:iam::aws:policy/CloudWatchAgentServerPolicy'],
            'run_task': [prefix + 'tibanna_zebra_cgap_list_instanceprofiles',
                         prefix + 'tibanna_zebra_cgap_cloudwatchlogs',
                         prefix + 'tibanna_zebra_cgap_iam_passrole_s3',
                         prefix + 'tibanna_zebra_cgap_bucket_access',
                         prefix + 'tibanna_zebra_cgap_dynamodb',
                         prefix + 'tibanna_zebra_cgap_executions',
                         prefix + 'tibanna_zebra_cgap_cw_dashboard',
                         'arn:aws:iam::aws:policy/AmazonEC2FullAccess',
                         'arn:aws:iam::aws:policy/AWSElasticBeanstalkReadOnly'],
            'start_run': [prefix + 'tibanna_zebra_cgap_vpc_access',
                          prefix + 'tibanna_zebra_cgap_bucket_access',
                          prefix + 'tibanna_zebra_cgap_cloudwatchlogs',
                          prefix + 'tibanna_zebra_cgap_dynamodb',
                          'arn:aws:iam::aws:policy/AWSElasticBeanstalkReadOnly'],
            'stepfunction': ['arn:aws:iam::aws:policy/service-role/AWSLambdaRole'],
            'update_cost': [prefix + 'tibanna_zebra_cgap_bucket_access',
                            prefix + 'tibanna_zebra_cgap_executions',
                            prefix + 'tibanna_zebra_cgap_dynamodb',
                            prefix + 'tibanna_zebra_cgap_pricing',
                            prefix + 'tibanna_zebra_cgap_vpc_access',
                            'arn:aws:iam::aws:policy/AWSElasticBeanstalkReadOnly'],
            'update_ffmeta': [prefix + 'tibanna_zebra_cgap_vpc_access',
                              prefix + 'tibanna_zebra_cgap_bucket_access',
                              prefix + 'tibanna_zebra_cgap_cloudwatchlogs',
                              prefix + 'tibanna_zebra_cgap_dynamodb',
                              'arn:aws:iam::aws:policy/AWSElasticBeanstalkReadOnly']}


def test_policy_prefix(expected_policy_arn_list_for_cgap):
    iam = iam_utils.IAM(user_group_tag='cgap')
    assert iam.tibanna_policy_prefix == 'tibanna_zebra_cgap'
    for lambda_name, policy_list in iam.policy_arn_list_for_role.items():
        assert sorted(policy_list) == sorted(expected_policy_arn_list_for_cgap[lambda_name])
