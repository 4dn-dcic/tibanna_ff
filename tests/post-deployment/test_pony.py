import pytest
import os
import json
import time
from tibanna_4dn.core import API
from tibanna_4dn.vars import DEV_SFN


JSON_DIR = 'test_json/pony/'


def test_md5():
    api = API()
    res = api.run_workflow(os.path.abspath(os.path.join(JSON_DIR, 'md5.json')), sfn=DEV_SFN)
    assert 'jobid' in res
    assert 'exec_arn' in res['_tibanna']
    time.sleep(360)
    assert api.check_status(res['_tibanna']['exec_arn']) == 'SUCCEEDED'
    postrunjson = json.loads(api.log(job_id=res['jobid'], postrunjson=True))
    assert 'status' in postrunjson['Job']
    assert postrunjson['Job']['status'] == '0'


def test_fastqc():
    api = API()
    res = api.run_workflow(os.path.abspath(os.path.join(JSON_DIR, 'fastqc.json')), sfn=DEV_SFN)
    assert 'jobid' in res
    assert 'exec_arn' in res['_tibanna']
    time.sleep(360)
    assert api.check_status(res['_tibanna']['exec_arn']) == 'SUCCEEDED'
    postrunjson = json.loads(api.log(job_id=res['jobid'], postrunjson=True))
    assert 'status' in postrunjson['Job']
    assert postrunjson['Job']['status'] == '0'


def test_bwa():
    api = API()
    res = api.run_workflow(os.path.abspath(os.path.join(JSON_DIR, 'bwa-mem.json')), sfn=DEV_SFN)
    assert 'jobid' in res
    assert 'exec_arn' in res['_tibanna']
    time.sleep(60 * 16)  # runs for 15 min
    assert api.check_status(res['_tibanna']['exec_arn']) == 'SUCCEEDED'
    postrunjson = json.loads(api.log(job_id=res['jobid'], postrunjson=True))
    assert 'status' in postrunjson['Job']
    assert postrunjson['Job']['status'] == '0'
