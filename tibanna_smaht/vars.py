from tibanna_ffcommon.vars import *


LAMBDA_TYPE = 'tiger'
SFN_TYPE = 'tiger'
ACCESSION_PREFIX = 'SMA'


# default step function name
TIBANNA_DEFAULT_STEP_FUNCTION_NAME = 'tibanna_' + LAMBDA_TYPE  # note that this is mismatched


# smaht-specific attribution
DEFAULT_CONSORTIUM = '358aed10-9b9d-4e26-ab84-4bd162da182b'
DEFAULT_SUBMISSION_CENTER = '9626d82e-8110-4213-ac75-0a50adf890ff'


HIGLASS_BUCKETS = []


DEV_ENV = 'smaht-wolf'
PROD_ENV = 'smaht-production'


def IAM_BUCKETS(env):
    """ This function determines the buckets for which the IAM policy is generated for.
        If you want tibanna to have access to more buckets, this is where to add them.
    """
    iam_buckets = [BUCKET_NAME(env, 'FileProcessed'),
                   BUCKET_NAME(env, 'FileFastq'),  # this is a holdover, in SMaHT these are all FileSubmitted
                   BUCKET_NAME(env, 'system'),
                   BUCKET_NAME(env, 'log'),
                   BUCKET_NAME(env, 'cwl')]
    if GLOBAL_ENV_BUCKET:
        iam_buckets.append(GLOBAL_ENV_BUCKET)
    return iam_buckets


DEV_SFN = 'tibanna_' + SFN_TYPE + '_' + DEV_ENV + '_' + DEV_SUFFIX
