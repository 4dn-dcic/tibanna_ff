from tibanna.vars import *
import os

S3_ENCRYPT_KEY = os.environ.get("S3_ENCRYPT_KEY", '')
DEV_SUFFIX = 'pre'

RUN_TASK_LAMBDA_NAME = 'run_task'
CHECK_TASK_LAMBDA_NAME = 'check_task'
UPDATE_COST_LAMBDA_NAME = 'update_cost'
START_RUN_LAMBDA_NAME = 'start_run'
UPDATE_FFMETA_LAMBDA_NAME = 'update_ffmeta'

GLOBAL_BUCKET_ENV = of.environ.get('GLOBAL_BUCKET_ENV', '')


# cached bucket names (internally used by function BUCKET_NAME
_BUCKET_NAME_PROCESSED_FILES = ''
_BUCKET_NAME_RAW_RILES = ''


def BUCKET_NAME(env, filetype):
    # use cache
    if filetype == 'FileProcessed' and _BUCKET_NAME_PROCESSED_FILES:
        return _BUCKET_NAME_PROCESSED_FILES
    if filetype in ['FileFastq', 'FileReference'] and _BUCKET_NAME_RAW_RILES:
        return _BUCKET_NAME_RAW_RILES

    # no cache
    if env.startswith('fourfront-'):
        env = env.replace('fourfront-', '')
    s3 = s3Utils(env=env)
    _BUCKET_NAME_PROCESSED_FILES = s3.outfile_bucket
    _BUCKET_NAME_RAW_RILES = s3.raw_file_bucket

    if filetype == 'FileProcessed':
        return _BUCKET_NAME_PROCESSED_FILES
    else:
        return _BUCKET_NAME_RAW_RILES

    return 'elasticbeanstalk-%s-%s' % (env, bucket_type)
