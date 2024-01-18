from tibanna.lambdas.run_task_awsem import handler as _handler
from tibanna_ffcommon.exceptions import exception_coordinator
from tibanna_smaht.vars import LAMBDA_TYPE, AWS_REGION

config = {
    'function_name': 'run_task_awsem',
    'function_module': 'service',
    'function_handler': 'handler',
    'handler': 'service.handler',
    'region': AWS_REGION,
    'runtime': 'python3.11',
    'role': 'tibanna_lambda_init_role',
    'description': 'launch an ec2 instance',
    'timeout': 300,
    'memory_size': 256
}

config['function_name'] = 'run_task_' + LAMBDA_TYPE


def metadata_only(event):
    event.update({'jobid': 'metadata_only'})
    return event


@exception_coordinator('run_task', metadata_only)
def handler(event, context):
    return _handler(event, context)
