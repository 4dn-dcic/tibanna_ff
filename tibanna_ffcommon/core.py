import copy
import os
import json
from tibanna.core import API as _API
from .stepfunction import StepFunctionFFAbstract
from ._version import __version__
from .vars import (
    S3_ENCRYPT_KEY,
    TIBANNA_DEFAULT_STEP_FUNCTION_NAME,
    RUN_TASK_LAMBDA_NAME,
    CHECK_TASK_LAMBDA_NAME,
    UPDATE_COST_LAMBDA_NAME,
    BUCKET_NAME,
    GLOBAL_ENV_BUCKET,
    AWSF_IMAGE,
    AMI_ID
)


class API(_API):

    @property
    def tibanna_packages(self):
        import tibanna
        import tibanna_ffcommon
        return [tibanna, tibanna_ffcommon]

    StepFunction = StepFunctionFFAbstract
    default_stepfunction_name = TIBANNA_DEFAULT_STEP_FUNCTION_NAME
    default_env = ''  # fill in the actual env name for inherited class
    sfn_type = ''  # fill in the actual type (e.g pony or zebra) for inherited class
    lambda_type = ''  # fill in the actual type (e.g pony or zebra) for inherited class

    run_task_lambda = RUN_TASK_LAMBDA_NAME
    check_task_lambda = CHECK_TASK_LAMBDA_NAME
    update_cost_lambda = UPDATE_COST_LAMBDA_NAME

    ami_id = AMI_ID

    @property
    def do_not_delete(self):
        return [] # add lambdas not to delete upon redeployment (e.g. used to contain 'validate_md5_s3_trigger')

    @property
    def IAM(self):
        from .iam_utils import IAM
        return IAM

    def __init__(self):
        pass

    def env_list(self, name):
        envlist = super().env_list(name)
        if envlist:
            # This is the envlist for run_task or check_task
            if GLOBAL_ENV_BUCKET:
                envlist.update({'GLOBAL_ENV_BUCKET': GLOBAL_ENV_BUCKET})
            return envlist
        envlist_ff = {
            'start_run': {'S3_ENCRYPT_KEY': S3_ENCRYPT_KEY},
            'update_ffmeta': {'S3_ENCRYPT_KEY': S3_ENCRYPT_KEY}
        }
        if GLOBAL_ENV_BUCKET:
            envlist_ff['start_run'].update({'GLOBAL_ENV_BUCKET': GLOBAL_ENV_BUCKET})
            envlist_ff['update_ffmeta'].update({'GLOBAL_ENV_BUCKET': GLOBAL_ENV_BUCKET})
        if AWSF_IMAGE:
            envlist_ff['start_run'].update({'AWSF_IMAGE': AWSF_IMAGE})
        for _, envs in envlist_ff.items():
            envs.update({'TIBANNA_FF_VERSION': __version__})
        return envlist_ff.get(name, '')

    def run_workflow(self, input_json, sfn=None,
                     env=None, jobid=None, sleep=3, verbose=True, open_browser=False):
        if isinstance(input_json, dict):
            data = copy.deepcopy(input_json)
        elif isinstance(input_json, str) and os.path.exists(input_json):
            with open(input_json) as input_file:
                data = json.load(input_file)
        else:
            raise Exception("input json must be either a file or a dictionary")

        # env priority: run_workflow parameter -> _tibanna_settings -> default_env
        if not env:
            if data.get('_tibanna', {}).get('env'):
                env = data['_tibanna']['env']
            else:
                env = self.default_env

        # automatic log bucket handling according to env
        if 'log_bucket' not in data['config']:
            data['config']['log_bucket'] = BUCKET_NAME(env, 'log')

        data['config']['ami_id'] = self.ami_id

        return super().run_workflow(input_json=data, sfn=sfn, env=env, jobid=jobid,
                                    sleep=sleep, verbose=verbose, open_browser=open_browser)

    def get_info_from_dd(self, ddres):
        ddinfo = super().get_info_from_dd(ddres)
        if not ddinfo:
            return None
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

    def kill(self, exec_arn=None, job_id=None):
        super().kill(exec_arn=exec_arn, job_id=job_id, soft=True)
