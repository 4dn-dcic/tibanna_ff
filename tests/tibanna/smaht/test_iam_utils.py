from tibanna_smaht import iam_utils
from tibanna_smaht.vars import AWS_ACCOUNT_NUMBER
import pytest


@pytest.fixture
def expected_policy_arn_list_for_smaht():
    prefix = 'arn:aws:iam::%s:policy/' % AWS_ACCOUNT_NUMBER
    return {'check_task': [prefix + 'tibanna_tiger_smaht_vpc_access',
                           prefix + 'tibanna_tiger_smaht_cw_metric',
                           prefix + 'tibanna_tiger_smaht_cloudwatchlogs',
                           prefix + 'tibanna_tiger_smaht_bucket_access',
                           prefix + 'tibanna_tiger_smaht_ec2_desc',
                           prefix + 'tibanna_tiger_smaht_ec2_termination',
                           prefix + 'tibanna_tiger_smaht_dynamodb',
                           prefix + 'tibanna_tiger_smaht_pricing',
                           'arn:aws:iam::aws:policy/AWSElasticBeanstalkReadOnly'],
            'ec2': [prefix + 'tibanna_tiger_smaht_bucket_access',
                    prefix + 'tibanna_tiger_smaht_cw_metric',
                    prefix + 'tibanna_tiger_smaht_ec2_desc',
                    'arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly',
                    'arn:aws:iam::aws:policy/CloudWatchAgentServerPolicy'],
            'run_task': [prefix + 'tibanna_tiger_smaht_list_instanceprofiles',
                         prefix + 'tibanna_tiger_smaht_cloudwatchlogs',
                         prefix + 'tibanna_tiger_smaht_iam_passrole_s3',
                         prefix + 'tibanna_tiger_smaht_bucket_access',
                         prefix + 'tibanna_tiger_smaht_dynamodb',
                         prefix + 'tibanna_tiger_smaht_executions',
                         prefix + 'tibanna_tiger_smaht_cw_dashboard',
                         'arn:aws:iam::aws:policy/AmazonEC2FullAccess',
                         'arn:aws:iam::aws:policy/AWSElasticBeanstalkReadOnly'],
            'start_run': [prefix + 'tibanna_tiger_smaht_vpc_access',
                          prefix + 'tibanna_tiger_smaht_bucket_access',
                          prefix + 'tibanna_tiger_smaht_cloudwatchlogs',
                          prefix + 'tibanna_tiger_smaht_dynamodb',
                          'arn:aws:iam::aws:policy/AWSElasticBeanstalkReadOnly'],
            'stepfunction': ['arn:aws:iam::aws:policy/service-role/AWSLambdaRole'],
            'update_cost': [prefix + 'tibanna_tiger_smaht_bucket_access',
                            prefix + 'tibanna_tiger_smaht_executions',
                            prefix + 'tibanna_tiger_smaht_dynamodb',
                            prefix + 'tibanna_tiger_smaht_pricing',
                            prefix + 'tibanna_tiger_smaht_vpc_access',
                            'arn:aws:iam::aws:policy/AWSElasticBeanstalkReadOnly'],
            'update_ffmeta': [prefix + 'tibanna_tiger_smaht_vpc_access',
                              prefix + 'tibanna_tiger_smaht_bucket_access',
                              prefix + 'tibanna_tiger_smaht_cloudwatchlogs',
                              prefix + 'tibanna_tiger_smaht_dynamodb',
                              'arn:aws:iam::aws:policy/AWSElasticBeanstalkReadOnly']}


def test_policy_prefix(expected_policy_arn_list_for_smaht):
    iam = iam_utils.IAM(user_group_tag='smaht')
    assert iam.tibanna_policy_prefix == 'tibanna_tiger_smaht'
    for lambda_name, policy_list in iam.policy_arn_list_for_role.items():
        assert sorted(policy_list) == sorted(expected_policy_arn_list_for_smaht[lambda_name])
