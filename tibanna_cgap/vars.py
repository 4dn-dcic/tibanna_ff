from tibanna_ffcommon.vars import *
import os


LAMBDA_TYPE = 'zebra'  # XXX: This interaction breaks the executions IAM permission
SFN_TYPE = 'zebra'
ACCESSION_PREFIX = 'GAP'


# default step function name
TIBANNA_DEFAULT_STEP_FUNCTION_NAME = 'tibanna_' + LAMBDA_TYPE  # note that this is mismatched


# fourfront
DEFAULT_INSTITUTION = '828cd4fe-ebb0-4b36-a94a-d2e3a36cc989'
DEFAULT_PROJECT = '12a92962-8265-4fc0-b2f8-cf14f05db58b'

HIGLASS_BUCKETS = []


DEV_ENV = 'cgapwolf'
PROD_ENV = 'cgap'


def IAM_BUCKETS(env):
    """ This function determines the buckets for which the IAM policy is generated for.
        If you want tibanna to have access to more buckets, this is where to add them.
    """
    iam_buckets = [BUCKET_NAME(env, 'FileProcessed'),
                   BUCKET_NAME(env, 'FileFastq'),
                   BUCKET_NAME(env, 'system'),
                   BUCKET_NAME(env, 'log'),
                   BUCKET_NAME(env, 'cwl')]
    if GLOBAL_ENV_BUCKET:
        iam_buckets.append(GLOBAL_ENV_BUCKET)
    return iam_buckets


DEV_SFN = 'tibanna_' + SFN_TYPE + '_' + DEV_ENV + '_' + DEV_SUFFIX
