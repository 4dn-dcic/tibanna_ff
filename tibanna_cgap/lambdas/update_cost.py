from tibanna.lambdas import update_cost_awsem as update_cost
from tibanna.lambdas.update_cost_awsem import config
from tibanna_ffcommon.exceptions import exception_coordinator
from tibanna_cgap.vars import LAMBDA_TYPE


config['function_name'] = 'update_cost_' + LAMBDA_TYPE


def handler(event, context):
    return update_cost(event)
