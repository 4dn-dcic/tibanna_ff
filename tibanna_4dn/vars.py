from tibanna_ffcommon.vars import *
import os

LAMBDA_TYPE = 'pony'
SFN_TYPE = 'pony'
ACCESSION_PREFIX = '4DN'


# default step function name
TIBANNA_DEFAULT_STEP_FUNCTION_NAME = os.environ.get('TIBANNA_DEFAULT_STEP_FUNCTION_NAME', 'tibanna_' + LAMBDA_TYPE)


# fourfront
DEFAULT_AWARD = '1U01CA200059-01'
DEFAULT_LAB = '4dn-dcic-lab'

HIGLASS_BUCKETS = [BUCKET_NAME('fourfront-webprod', 'FileProcessed'),
                   BUCKET_NAME('fourfront-webdev', 'FileProcessed')]

DEV_ENV = 'fourfront-webdev'
IAM_BUCKETS = [BUCKET_NAME(DEV_ENV, 'FileProcessed'),
               BUCKET_NAME(DEV_ENV, 'FileFastq'),
               'tibanna-output']

DEV_SFN = 'tibanna_' + SFN_TYPE + '_' + DEV_SUFFIX
