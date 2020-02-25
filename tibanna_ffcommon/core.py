from tibanna.core import API as _API
from .stepfunction import StepFunctionFFAbstract
from .vars import (
    S3_ENCRYPT_KEY,
    TIBANNA_DEFAULT_STEP_FUNCTION_NAME,
    DYNAMODB_TABLE
)
import boto3


class API(_API):

    @property
    def tibanna_packages(self):
        import tibanna
        import tibanna_ffcommon
        return [tibanna, tibanna_ffcommon]

    StepFunction = StepFunctionFFAbstract
    default_stepfunction_name = TIBANNA_DEFAULT_STEP_FUNCTION_NAME
    sfn_type = ''  # fill in the actual type (e.g pony or zebra) for inherited class
    lambda_type = ''  # fill in the actual type (e.g pony or zebra) for inherited class

    run_task_lambda = 'run_task'
    check_task_lambda = 'check_task'

    @property
    def do_not_delete(self):
        return ['validate_md5_s3_trigger']

    def __init__(self):
        pass

    def env_list(self, name):
        envlist = super().env_list(name)
        if envlist:
            return envlist
        envlist_ff = {
            'run_workflow': {},
            'start_run': {'S3_ENCRYPT_KEY': S3_ENCRYPT_KEY},
            'update_ffmeta': {'S3_ENCRYPT_KEY': S3_ENCRYPT_KEY},
            'validate_md5_s3_initiator': {'S3_ENCRYPT_KEY': S3_ENCRYPT_KEY},
            'validate_md5_s3_trigger': {}
        }
        return envlist_ff.get(name, '')

    def get_info_from_dd(self, job_id):
        ddinfo = super().get_info_from_dd(job_id)
        if not ddinfo:
            return None
        try:
            dd = boto3.client('dynamodb')
            ddres = dd.query(TableName=DYNAMODB_TABLE,
                             KeyConditions={'Job Id': {'AttributeValueList': [{'S': job_id}],
                                                       'ComparisonOperator': 'EQ'}})
        except:
            return ddinfo
        if 'Items' in ddres:
            dditem = ddres['Items'][0]
            if 'WorkflowRun uuid' in dditem:
                wfr_uuid = dditem['WorkflowRun uuid']['S']
            else:
                wfr_uuid = ''
            if 'env' in dditem:
                env = dditem['env']['S']
            else:
                env = ''
            ddinfo.update({'wfr_uuid': wfr_uuid, 'env': env})
            return ddinfo
        else:
            return ddinfo
