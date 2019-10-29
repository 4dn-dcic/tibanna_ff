import pytest
import os
import json
import time
from tibanna_cgap.core import API
from tibanna_cgap.vars import DEV_SFN
from tests.tibanna.zebra.conftest import post_new_fastqfile, get_test_json, dev_key
from dcicutils import ff_utils


JSON_DIR = 'test_json/zebra/'


def test_md5():
    data = get_test_json('md5.json')
    api = API()
    res = api.run_workflow(data), sfn=DEV_SFN)
    assert 'jobid' in res
    time.sleep(360)
    assert api.check_status(res['exec_arn']) == 'SUCCEEDED'
    postrunjson = json.loads(api.log(job_id=res['jobid'], postrunjson=True))
    assert 'status' in postrunjson['Job']
    assert postrunjson['Job']['status'] == '0'


def test_fastqc():
    data = get_test_json('fastqc.json')
    api = API()
    res = api.run_workflow(data), sfn=DEV_SFN)
    assert 'jobid' in res
    time.sleep(360)
    assert api.check_status(res['exec_arn']) == 'SUCCEEDED'
    postrunjson = json.loads(API().log(job_id=res['jobid'], postrunjson=True))
    assert 'status' in postrunjson['Job']
    assert postrunjson['Job']['status'] == '0'


def test_bwa():
    data = get_test_json('bwa-check.json')
    api = API()
    res = api.run_workflow(data, sfn=DEV_SFN)
    assert 'jobid' in res
    assert 'exec_arn' in res['_tibanna']
    time.sleep(60 * 20)  # runs for 15 min
    assert api.check_status(res['_tibanna']['exec_arn']) == 'SUCCEEDED'
    postrunjson = json.loads(api.log(job_id=res['jobid'], postrunjson=True))
    assert 'status' in postrunjson['Job']
    assert postrunjson['Job']['status'] == '0'
