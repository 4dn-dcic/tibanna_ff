from tibanna_smaht.check_task import check_task
from tibanna.lambdas.check_task_awsem import config
from tibanna_ffcommon.exceptions import exception_coordinator
from tibanna_smaht.vars import LAMBDA_TYPE, AWS_REGION



config = {
    'function_name': 'check_task_awsem',
    'function_module': 'service',
    'function_handler': 'handler',
    'handler': 'service.handler',
    'region': AWS_REGION,
    'runtime': 'python3.11',
    'role': 'tibanna_lambda_init_role',
    'description': 'check status of AWSEM run by interegating appropriate files on S3 ',
    'timeout': 300,
    'memory_size': 256
}

config['function_name'] = 'check_task_' + LAMBDA_TYPE


def metadata_only(event):
    event.update({'postrunjson': 'metadata_only'})
    return event


@exception_coordinator('check_task', metadata_only)
def handler(event, context):
    return check_task(event)
