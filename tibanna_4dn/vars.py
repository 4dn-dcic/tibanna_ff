from tibanna_ffcommon.vars import *
import os

LAMBDA_TYPE = 'pony'
SFN_TYPE = 'pony'
ACCESSION_PREFIX = '4DN'


# default step function name
TIBANNA_DEFAULT_STEP_FUNCTION_NAME = 'tibanna_' + LAMBDA_TYPE


# fourfront
DEFAULT_AWARD = '1U01CA200059-01'
DEFAULT_LAB = '4dn-dcic-lab'

HIGLASS_BUCKETS = [BUCKET_NAME('data', 'FileProcessed'),
                   BUCKET_NAME('fourfront-webdev', 'FileProcessed')]

DEV_ENV = 'webdev'
PROD_ENV = 'data'

def IAM_BUCKETS(env):
    iam_buckets = [BUCKET_NAME(env, 'FileProcessed'),
                   BUCKET_NAME(env, 'FileFastq'),
                   '4dn-open-data-public',
                   BUCKET_NAME(env, 'system'),
                   BUCKET_NAME(env, 'log')]
    if GLOBAL_BUCKET_ENV:
        iam_buckets.append(GLOBAL_BUCKET_ENV)
    return iam_buckets

DEV_SFN = 'tibanna_' + SFN_TYPE + '_' + DEV_SUFFIX
