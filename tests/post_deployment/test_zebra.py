import pytest
import os
import json
import time
from tibanna_cgap.core import API
from tibanna_cgap.vars import DEV_SFN, DEV_ENV
from tests.tibanna.zebra.conftest import post_new_fastqfile, get_test_json, dev_key
from dcicutils import ff_utils


JSON_DIR = 'test_json/zebra/'
FILE_DIR = 'tests/files/'


def test_md5():
    key = dev_key()
    # prep new File
    data = get_test_json('md5.json')
    fq_uuid = post_new_fastqfile(key=key, upload_content=str(uuid.uuid4()))  # upload random content to avoid md5 conflict
    # prep input json
    data['input_files'][0]['uuid'] = fq_uuid
    # run workflow
    api = API()
    res = api.run_workflow(data, sfn=DEV_SFN)
    assert 'jobid' in res
    assert 'exec_arn' in res['_tibanna']
    time.sleep(360)
    # check step function status
    assert api.check_status(res['_tibanna']['exec_arn']) == 'SUCCEEDED'
    outjson = api.check_output(res['_tibanna']['exec_arn'])
    # check postrun json
    postrunjson = json.loads(api.log(job_id=res['jobid'], postrunjson=True))
    assert 'status' in postrunjson['Job']
    assert postrunjson['Job']['status'] == '0'
    # check metadata update
    res = ff_utils.get_metadata(fq_uuid, key=key, ff_env=DEV_ENV, check_queue=True)
    ff_utils.patch_metadata({'status': 'deleted'}, fq_uuid, key=key)
    assert res['md5sum'] == '1a100f38fadf653091a67b3705dfc1f6'
    assert res['content_md5sum'] == 'f3de8413d8bf6a1b1848e2208b920c82'
    assert res['file_size'] == 123
    assert 'ff_meta' in outjson
    assert 'uuid' in outjson['ff_meta']
    wfr_uuid = outjson['ff_meta']['uuid']
    res = ff_utils.get_metadata(wfr_uuid, key=key, ff_env=DEV_ENV, check_queue=True)
    assert res['run_status'] == 'complete'
    assert 'quality_metric' in res


def test_fastqc():
    key = dev_key()
    data = get_test_json('fastqc.json')
    fq_uuid = post_new_fastqfile(key=key, upload_file=os.path.join(FILE_DIR, 'fastq/A.R2.fastq.gz'))
    data['input_files'][0]['uuid'] = fq_uuid
    api = API()
    res = api.run_workflow(data, sfn=DEV_SFN)
    assert 'jobid' in res
    assert 'exec_arn' in res['_tibanna']
    time.sleep(360)
    assert api.check_status(res['_tibanna']['exec_arn']) == 'SUCCEEDED'
    outjson = api.check_output(res['_tibanna']['exec_arn'])
    postrunjson = json.loads(api.log(job_id=res['jobid'], postrunjson=True))
    assert 'status' in postrunjson['Job']
    assert postrunjson['Job']['status'] == '0'
    res = ff_utils.get_metadata(fq_uuid, key=key, ff_env=DEV_ENV, check_queue=True)
    ff_utils.patch_metadata({'status': 'deleted'}, fq_uuid, key=key)
    assert 'quality_metric' in res
    assert 'ff_meta' in outjson
    assert 'uuid' in outjson['ff_meta']
    wfr_uuid = outjson['ff_meta']['uuid']
    res = ff_utils.get_metadata(wfr_uuid, key=key, ff_env=DEV_ENV, check_queue=True)
    assert res['run_status'] == 'complete'
    assert 'quality_metric' in res

    
def test_bwa():
    key = dev_key()
    # prep new File
    data = get_test_json('bwa-check.json')
    fq1_uuid = post_new_fastqfile(key=key, upload_file=os.path.join(FILE_DIR, 'fastq/B.R1.fastq.gz'))
    fq2_uuid = post_new_fastqfile(key=key, upload_file=os.path.join(FILE_DIR, 'fastq/B.R2.fastq.gz'))
    # prep input json
    data['input_files'][0]['uuid'] = fq1_uuid  # fastq_R1
    data['input_files'][0]['uuid'] = fq2_uuid  # fastq_R2
    api = API()
    res = api.run_workflow(data, sfn=DEV_SFN)
    assert 'jobid' in res
    assert 'exec_arn' in res['_tibanna']
    time.sleep(360)
    assert api.check_status(res['_tibanna']['exec_arn']) == 'SUCCEEDED'
    outjson = api.check_output(res['_tibanna']['exec_arn'])
    postrunjson = json.loads(api.log(job_id=res['jobid'], postrunjson=True))
    assert 'status' in postrunjson['Job']
    assert postrunjson['Job']['status'] == '0'
    assert 'ff_meta' in outjson
    assert 'uuid' in outjson['ff_meta']
    wfr_uuid = outjson['ff_meta']['uuid']
    pf_uuid = outjson['pf_meta'][0]['uuid']
    res = ff_utils.get_metadata(wfr_uuid, key=key, ff_env=DEV_ENV, check_queue=True)
    assert res['run_status'] == 'complete'
    assert 'quality_metric' in res
    res = ff_utils.get_metadata(pf_uuid, key=key, ff_env=DEV_ENV, check_queue=True)
    assert res['status'] == 'uploaded'
    ff_utils.patch_metadata({'status': 'deleted'}, fq1_uuid, key=key)
    ff_utils.patch_metadata({'status': 'deleted'}, fq2_uuid, key=key)
    ff_utils.patch_metadata({'status': 'deleted'}, wfr_uuid, key=key)
    ff_utils.patch_metadata({'status': 'deleted'}, pf_uuid, key=key)
