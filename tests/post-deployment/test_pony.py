import pytest
import os
import json
import time
from tibanna_4dn.core import API


SFN = 'tibanna_pony_pre'
JSON_DIR = 'test_json/pony/'


def test_md5():
    api = API()
    res = api.run_workflow(os.path.abspath(os.path.join(JSON_DIR, 'md5.json')), sfn=SFN)
    assert 'jobid' in res
    assert 'exec_arn' in res['_tibanna']
    time.sleep(360)
    assert api.check_status(res['_tibanna']['exec_arn']) == 'SUCCEEDED'
    postrunjson = json.loads(api.log(job_id=res['jobid'], postrunjson=True))
    assert 'status' in postrunjson['Job']
    assert postrunjson['Job']['status']


def test_fastqc():
    api = API()
    res = api.run_workflow(os.path.abspath(os.path.join(JSON_DIR, 'fastqc.json')), sfn=SFN)
    assert 'jobid' in res
    assert 'exec_arn' in res['_tibanna']
    time.sleep(360)
    assert api.check_status(res['_tibanna']['exec_arn']) == 'SUCCEEDED'
    postrunjson = json.loads(api.log(job_id=res['jobid'], postrunjson=True))
    assert 'status' in postrunjson['Job']
    assert postrunjson['Job']['status']
