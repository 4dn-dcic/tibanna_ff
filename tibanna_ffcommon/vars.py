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

# Workflow argument file types
OUTPUT_PROCESSED_FILE = 'Output processed file'
OUTPUT_REPORT_FILE = 'Output report file'
OUTPUT_QC_FILE = 'Output QC file'
GENERIC_QC_FILE = 'Generic QC file'
OUTPUT_TO_BE_EXTRA_INPUT_FILE = 'Output to-be-extra-input file'
INPUT_FILE = 'Input file'

# Core file types
OUTPUT_FILE  = 'OutputFile' # SMaHT
SUBMITTED_FILE = 'SubmittedFile' # SMaHT
REFERENCE_FILE = 'ReferenceFile' # SMaHT
FILE_PROCESSED = 'FileProcessed' # CGAP/4DN
FILE_FASTQ = 'FileFastq' # CGAP/4DN
FILE_REFERENCE = 'FileReference' # CGAP/4DN
FILE_SUBMITTED = 'FileSubmitted' # CGAP/4DN
FILE_MICROSCOPY = 'FileMicroscopy' # 4DN


# Secure Tibanna AMI
# Note that this means only these regions will work (replicate AMI in main account as needed)
# Note additionally that these AMI's all must be configured to be launchable by our AWS
# accounts
AMI_PER_REGION = {
    'x86': {
        'us-east-1': 'ami-0afc2a6bf9a8c35c6',
        'us-east-2': 'ami-019d106d5006c260b'
    },
    'Arm': {
        'us-east-1': 'ami-0f62f740c44080b8f',
        'us-east-2': 'ami-01bec7663ee3ab696'
    }
}

if AWS_REGION not in AMI_PER_REGION['x86']:
    logger.warning("Secure Tibanna AMI for region %s is not available." % AWS_REGION)
    raise Exception('')


def BUCKET_NAME(env, filetype):
    global _BUCKET_NAME_PROCESSED_FILES
    global _BUCKET_NAME_RAW_FILES
    global _BUCKET_NAME_SYS
    global _BUCKET_NAME_LOG
    global _BUCKET_NAME_CWL

    processed_file_types = [FILE_PROCESSED, OUTPUT_FILE]
    raw_file_types = [FILE_FASTQ, FILE_REFERENCE, REFERENCE_FILE, SUBMITTED_FILE, FILE_MICROSCOPY, FILE_SUBMITTED]

    # use cache
    if filetype in processed_file_types and env in _BUCKET_NAME_PROCESSED_FILES:
        return _BUCKET_NAME_PROCESSED_FILES[env]
    if filetype in raw_file_types and env in _BUCKET_NAME_RAW_FILES:
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

    if filetype in processed_file_types:
        return _BUCKET_NAME_PROCESSED_FILES[env]
    elif filetype in raw_file_types:
        return _BUCKET_NAME_RAW_FILES[env]
    elif filetype == 'system':
        return _BUCKET_NAME_SYS[env]
    elif filetype == 'cwl':
        return _BUCKET_NAME_CWL[env]
    else:  # log
        return _BUCKET_NAME_LOG[env]
