import pytest
from dcicutils.s3_utils import s3Utils
import os
import json


def pytest_runtest_setup(item):
    # called for running each test in directory
    print("Running lambda tests for: ", item)


valid_env = pytest.mark.skipif(not os.environ.get("S3_ENCRYPT_KEY", False),
                               reason='Required environment not setup to run test')


def read_event_file(event_file_name, ff_keys=None):
    with open(event_file_name) as json_data:
        data = json.load(json_data)
        if ff_keys is not None:
            data['ff_keys'] = ff_keys
        return data


def minimal_postrunjson_template():
    return {'Job': {'App': {},
                    'Input': {'Input_files_data': {},
                              'Input_parameters': {},
                              'Secondary_files_data':{}},
                    'Output': {},
                    'JOBID': '',
                    'start_time': ''},
            'config': {'log_bucket': ''}}
