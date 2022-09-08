from tibanna.vars import *
import os
from dcicutils.s3_utils import s3Utils
from tibanna._version import __version__ as tibanna_version


S3_ENCRYPT_KEY = os.environ.get('S3_ENCRYPT_KEY', '')
S3_ENCRYPT_KEY_ID = os.environ.get('S3_ENCRYPT_KEY_ID', None)
DEV_SUFFIX = 'pre'

RUN_TASK_LAMBDA_NAME = 'run_task'
CHECK_TASK_LAMBDA_NAME = 'check_task'
UPDATE_COST_LAMBDA_NAME = 'update_cost'
START_RUN_LAMBDA_NAME = 'start_run'
UPDATE_FFMETA_LAMBDA_NAME = 'update_ffmeta'

GLOBAL_ENV_BUCKET = os.environ.get('GLOBAL_ENV_BUCKET', None)
if not GLOBAL_ENV_BUCKET:
    raise Exception('GLOBAL_ENV_BUCKET not present - redeploy Tibanna with it set!')
AWSF_IMAGE = '%s.dkr.ecr.%s.amazonaws.com/tibanna-awsf:%s' % (AWS_ACCOUNT_NUMBER, AWS_REGION, tibanna_version)


# cached bucket names (internally used by function BUCKET_NAME
_BUCKET_NAME_PROCESSED_FILES = dict()
_BUCKET_NAME_RAW_FILES = dict()
_BUCKET_NAME_SYS = dict()
_BUCKET_NAME_LOG = dict()
_BUCKET_NAME_CWL = dict()


# Secure Tibanna AMI
# Note that this means only these regions will work (replicate AMI in main account as needed)
# Note additionally that these AMI's all must be configured to be launchable by our AWS
# accounts
AMI_PER_REGION = {
    'us-east-1': 'ami-00ad035048da98fc2',
    'us-east-2': 'ami-0afbf1ab3268ddf17',
}
if AWS_REGION not in AMI_PER_REGION:
    logger.warning("Secure Tibanna AMI for region %s is not available." % AWS_REGION)
    raise Exception('')
AMI_ID = AMI_PER_REGION.get(AWS_REGION, '')


def BUCKET_NAME(env, filetype):
    global _BUCKET_NAME_PROCESSED_FILES
    global _BUCKET_NAME_RAW_FILES
    global _BUCKET_NAME_SYSG
    global _BUCKET_NAME_LOG
    global _BUCKET_NAME_CWL

    # use cache
    if filetype == 'FileProcessed' and env in _BUCKET_NAME_PROCESSED_FILES:
        return _BUCKET_NAME_PROCESSED_FILES[env]
    if filetype in ['FileFastq', 'FileReference', 'FileMicroscopy', 'FileSubmitted'] and env in _BUCKET_NAME_RAW_FILES:
        return _BUCKET_NAME_RAW_FILES[env]
    if filetype == 'system' and env in _BUCKET_NAME_SYS:  # log bucket
        return _BUCKET_NAME_SYS[env]
    if filetype == 'log' and env in _BUCKET_NAME_LOG:  # log bucket
        return _BUCKET_NAME_LOG[env]
    if filetype == 'cwl' and env in _BUCKET_NAME_CWL:
        return _BUCKET_NAME_CWL[env]

    # no cache
    if filetype == 'log' and AWS_ACCOUNT_NUMBER == '643366669028':  # 4dn-dcic account
        _BUCKET_NAME_LOG[env] = 'tibanna-output'
    else:
        s3 = s3Utils(env=env)
        _BUCKET_NAME_PROCESSED_FILES[env] = s3.outfile_bucket
        _BUCKET_NAME_RAW_FILES[env] = s3.raw_file_bucket
        _BUCKET_NAME_SYS[env] = s3.sys_bucket
        _BUCKET_NAME_LOG[env] = s3.tibanna_output_bucket
        _BUCKET_NAME_CWL[env] = s3.tibanna_cwls_bucket

    if filetype == 'FileProcessed':
        return _BUCKET_NAME_PROCESSED_FILES[env]
    elif filetype in ['FileFastq', 'FileReference', 'FileMicroscopy', 'FileSubmitted']:
        return _BUCKET_NAME_RAW_FILES[env]
    elif filetype == 'system':
        return _BUCKET_NAME_SYS[env]
    elif filetype == 'cwl':
        return _BUCKET_NAME_CWL[env]
    else:  # log
        return _BUCKET_NAME_LOG[env]
