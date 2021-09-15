from tibanna.vars import *
import os
from dcicutils.s3_utils import s3Utils
from tibanna._version import __version__ as tibanna_version


S3_ENCRYPT_KEY = os.environ.get("S3_ENCRYPT_KEY", '')
DEV_SUFFIX = 'pre'

RUN_TASK_LAMBDA_NAME = 'run_task'
CHECK_TASK_LAMBDA_NAME = 'check_task'
UPDATE_COST_LAMBDA_NAME = 'update_cost'
START_RUN_LAMBDA_NAME = 'start_run'
UPDATE_FFMETA_LAMBDA_NAME = 'update_ffmeta'
RUN_WORKFLOW_LAMBDA_NAME = 'run_workflow'
STATUS_WFR_LAMBDA_NAME = 'status_wfr'

GLOBAL_BUCKET_ENV = os.environ.get('GLOBAL_BUCKET_ENV', '')
AWSF_IMAGE = '%s.dkr.ecr.%s.amazonaws.com/tibanna-awsf:%s' % (AWS_ACCOUNT_NUMBER, AWS_REGION, tibanna_version)


# cached bucket names (internally used by function BUCKET_NAME
_BUCKET_NAME_PROCESSED_FILES = dict()
_BUCKET_NAME_RAW_RILES = dict()
_BUCKET_NAME_SYS = dict()
_BUCKET_NAME_LOG = dict()


def BUCKET_NAME(env, filetype):
    global _BUCKET_NAME_PROCESSED_FILES
    global _BUCKET_NAME_RAW_RILES
    global _BUCKET_NAME_SYSG
    global _BUCKET_NAME_LOG

    # use cache
    if filetype == 'FileProcessed' and env in _BUCKET_NAME_PROCESSED_FILES:
        return _BUCKET_NAME_PROCESSED_FILES[env]
    if filetype in ['FileFastq', 'FileReference'] and env in _BUCKET_NAME_RAW_RILES:
        return _BUCKET_NAME_RAW_RILES[env]
    if filetype == 'system' and env in _BUCKET_NAME_SYS:  # log bucket
        return _BUCKET_NAME_SYS[env]
    if filetype == 'log' and env in _BUCKET_NAME_LOG:  # log bucket
        return _BUCKET_NAME_LOG[env]

    # no cache
    if filetype == 'log' and AWS_ACCOUNT_NUMBER == '643366669028':  # 4dn-dcic account
        _BUCKET_NAME_LOG[env] = 'tibanna-output'
    else:
        s3 = s3Utils(env=env)
        _BUCKET_NAME_PROCESSED_FILES[env] = s3.outfile_bucket
        _BUCKET_NAME_RAW_RILES[env] = s3.raw_file_bucket
        _BUCKET_NAME_SYS[env] = s3.sys_bucket
        _BUCKET_NAME_LOG[env] = s3.tibanna_output_bucket

    if filetype == 'FileProcessed':
        return _BUCKET_NAME_PROCESSED_FILES[env]
    elif filetype in ['FileFastq', 'FileReference']:
        return _BUCKET_NAME_RAW_RILES[env]
    elif filetype == 'system':
        return _BUCKET_NAME_SYS[env]
    else:  # log
        return _BUCKET_NAME_LOG[env]
