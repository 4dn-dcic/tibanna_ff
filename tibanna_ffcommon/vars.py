from tibanna.vars import *
import os

S3_ENCRYPT_KEY = os.environ.get("S3_ENCRYPT_KEY", '')
DEV_SUFFIX = 'pre'

RUN_TASK_LAMBDA_NAME = 'run_task'
CHECK_TASK_LAMBDA_NAME = 'check_task'
UPDATE_COST_LAMBDA_NAME = 'update_cost'

TIBANNA_REPO_BRANCH = os.environ.get('TIBANNA_REPO_BRANCH', 'huit')


def BUCKET_NAME(env, filetype):
    if filetype in ['FileFastq', 'FileReference']:
        bucket_type = 'files'
    else:
        bucket_type = 'wfoutput'
    if env in ['data', 'staging', 'fourfront-green', 'fourfront-blue']:
        env = 'fourfront-webprod'
    return 'elasticbeanstalk-%s-%s' % (env, bucket_type)
