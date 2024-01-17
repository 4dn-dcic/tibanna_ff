from tibanna.lambdas.update_cost_awsem import handler as _handler
from tibanna_smaht.vars import LAMBDA_TYPE, AWS_REGION

config = {
    'function_name': 'update_cost_awsem',
    'function_module': 'service',
    'function_handler': 'handler',
    'handler': 'service.handler',
    'region': AWS_REGION,
    'runtime': 'python3.11',
    'role': 'tibanna_lambda_init_role',
    'description': 'update costs of a workflow run',
    'timeout': 300,
    'memory_size': 256
}

config['function_name'] = 'update_cost_' + LAMBDA_TYPE


def handler(event, context):
    return _handler(event, context)
