from tibanna.lambdas.update_cost_awsem import handler as _handler, config
from tibanna_4dn.vars import LAMBDA_TYPE


config['function_name'] = 'update_cost_' + LAMBDA_TYPE


def handler(event, context):
    return _handler(event)
