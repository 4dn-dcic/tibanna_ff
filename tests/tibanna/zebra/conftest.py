import pytest
from dcicutils.s3_utils import s3Utils
from dcicutils import ff_utils
import os
import json
import uuid
from tests.tibanna.ffcommon.conftest import read_event_file
from tibanna_cgap.zebra_utils import (
    ProcessedFileMetadata
)
from tibanna_cgap.vars import (
    DEFAULT_INSTITUTION,
    DEFAULT_PROJECT
)

def pytest_runtest_setup(item):
    # called for running each test in directory
    print("Running lambda tests for: ", item)


valid_env = pytest.mark.skipif(not os.environ.get("S3_ENCRYPT_KEY", False),
                               reason='Required environment not setup to run test')


@pytest.fixture(scope='session')
def start_run_event_md5():
    return get_event_file_for('start_run', event_file='event_md5.json')


@pytest.fixture(scope='session')
def start_run_event_bwa_check():
    return get_event_file_for('start_run', event_file='event_bwa-check.json')


@valid_env
def post_new_processedfile(file_format, key, **kwargs):
    new_pf = ProcessedFileMetadata(file_format=file_format, other_fields=kwargs).as_dict()
    res = ff_utils.post_metadata(new_pf, 'FileProcessed', key=key)
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


def get_event_file_for(lambda_name, ff_keys=None, event_file='event.json'):
    dir_path = os.path.dirname(os.path.realpath(__file__))
    event_file_name = os.path.join(dir_path, lambda_name, event_file)
    return read_event_file(event_file_name, ff_keys)
