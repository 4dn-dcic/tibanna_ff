import pytest
from dcicutils.s3_utils import s3Utils
from dcicutils import ff_utils
import os
import json
import uuid
import boto3
from tests.tibanna.ffcommon.conftest import read_event_file
from tibanna_ffcommon.portal_utils import (
    TibannaSettings
)
from tibanna_cgap.zebra_utils import (
    ProcessedFileMetadata
)
from tibanna_cgap.vars import (
    DEFAULT_INSTITUTION,
    DEFAULT_PROJECT,
    BUCKET_NAME,
    DEV_ENV
)

def pytest_runtest_setup(item):
    # called for running each test in directory
    print("Running lambda tests for: ", item)


valid_env = pytest.mark.skipif(not os.environ.get("S3_ENCRYPT_KEY", False),
                               reason='Required environment not setup to run test')


@pytest.fixture(scope='session')
def s3_utils(used_env):
    return s3Utils(env=used_env)


@pytest.fixture(scope='session')
def ff_keys(s3_utils):
    return s3_utils.get_access_keys('access_key_tibanna')


@pytest.fixture(scope='session')
def start_run_event_md5():
    return get_event_file_for('start_run', event_file='event_md5.json')


@pytest.fixture(scope='session')
def start_run_event_bwa_check():
    return get_event_file_for('start_run', event_file='event_bwa-check.json')


@pytest.fixture(scope='session')
def update_ffmeta_event_data_bamcheck(ff_keys):
    return get_event_file_for('update_ffmeta', ff_keys=ff_keys, event_file='event_bamcheck.json')


@valid_env
def post_new_fastqfile(key, upload_file=None, upload_content=None):
    """upload_content must be in bytes"""
    ffobject = {"uuid": str(uuid.uuid4()),
                "file_format": "fastq",
                "description": "tibanna test",
                "institution": DEFAULT_INSTITUTION,
                "project": DEFAULT_PROJECT}
    res = ff_utils.post_metadata(ffobject, 'FileFastq', key=key)
    if upload_file:
        f_uuid = res['@graph'][0]['uuid']
        accession = res['@graph'][0]['accession']
        upload_key = f_uuid + '/' + accession + '.fastq.gz'
        boto3.client('s3').upload_file(upload_file, BUCKET_NAME(DEV_ENV, 'FileFastq'), upload_key)
    if upload_content:
        f_uuid = res['@graph'][0]['uuid']
        accession = res['@graph'][0]['accession']
        upload_key = f_uuid + '/' + accession + '.fastq.gz'
        boto3.client('s3').put_object(Body=upload_content,
                                      Bucket=BUCKET_NAME(DEV_ENV, 'FileFastq'),
                                      Key=upload_key)
    return res['@graph'][0]['uuid']


@valid_env
def post_new_processedfile(file_format, key, extra_file_formats=None,
                           upload_file=None, extension=None, **kwargs):
    if extra_file_formats:
        extra_files = [{'file_format': ef} for ef in extra_file_formats]
    else:
        extra_files = None
    other_fields = kwargs
    other_fields.update({"description": "tibanna test"})
    new_pf = ProcessedFileMetadata(file_format=file_format,
                                   extra_files=extra_files,
                                   other_fields=other_fields).as_dict()
    res = ff_utils.post_metadata(new_pf, 'FileProcessed', key=key)
    if upload_file:
        f_uuid = res['@graph'][0]['uuid']
        accession = res['@graph'][0]['accession']
        upload_key = f_uuid + '/' + accession + '.' + extension
        boto3.client('s3').upload_file(upload_file, BUCKET_NAME(DEV_ENV, 'FileProcessed'), upload_key)
    return res['@graph'][0]['uuid']


@valid_env
def post_new_qc(qctype, key, **kwargs):
    if not qctype.startswith('QualityMetric'):
        raise Exception("qctype must begin with QualityMetric")
    qc_object = {"uuid": str(uuid.uuid4()),
                 "institution": DEFAULT_INSTITUTION,
                 "project": DEFAULT_PROJECT}
    for k, v in kwargs.items():
        qc_object[k] = v
    res = ff_utils.post_metadata(qc_object, qctype, key=key)
    return res['@graph'][0]['uuid']


def get_test_json(file_name):
    dir_path = os.path.dirname(os.path.realpath(__file__))
    event_file_name = os.path.join(dir_path, '..', '..', '..', 'test_json', 'zebra', file_name)
    return read_event_file(event_file_name)


def get_event_file_for(lambda_name, ff_keys=None, event_file='event.json'):
    dir_path = os.path.dirname(os.path.realpath(__file__))
    event_file_name = os.path.join(dir_path, lambda_name, event_file)
    return read_event_file(event_file_name, ff_keys)


def dev_key():
    data = {'env': DEV_ENV,
            'settings': {'1': '1'}}
    tibanna = TibannaSettings(**data)
    return tibanna.ff_keys
