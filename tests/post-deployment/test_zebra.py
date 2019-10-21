import pytest
import os
import json
import time
from tibanna_cgap.core import API


SFN = 'tibanna_zebra_pre'
JSON_DIR = 'test_json/zebra/'


def test_md5():
    api = API()
    res = api.run_workflow(os.path.abspath(os.path.join(JSON_DIR, 'md5.json')), sfn=SFN)
    assert 'jobid' in res
    time.sleep(360)
    assert api.check_status(res['exec_arn']) == 'SUCCEEDED'
    postrunjson = json.loads(api.log(job_id=res['jobid'], postrunjson=True))
    assert 'status' in postrunjson['Job']
    assert postrunjson['Job']['status']


def test_fastqc():
    res = API().run_workflow(os.path.abspath(os.path.join(JSON_DIR, 'fastqc.json')), sfn=SFN)
    assert 'jobid' in res
    time.sleep(360)
    assert api.check_status(res['exec_arn']) == 'SUCCEEDED'
    postrunjson = json.loads(API().log(job_id=res['jobid'], postrunjson=True))
    assert 'status' in postrunjson['Job']
    assert postrunjson['Job']['status']
