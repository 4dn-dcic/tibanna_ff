import boto3
import os
import time
from tibanna_cgap.core import API
from tibanna_cgap.vars import DEV_SFN
from tests.tibanna.zebra.conftest import post_new_fastqfile, get_test_json, dev_key


JSON_DIR = 'test_json/zebra/'
FILE_DIR = 'tests/files/'


def test_bwa():
    key = dev_key()
    # prep new File
    data = get_test_json('bwa-check.json')
    fq1_uuid = post_new_fastqfile(key=key, upload_file=os.path.join(FILE_DIR, 'fastq/B.R1.fastq.gz'))
    fq2_uuid = post_new_fastqfile(key=key, upload_file=os.path.join(FILE_DIR, 'fastq/B.R2.fastq.gz'))
    # prep input json
    data['input_files'][0]['uuid'] = fq1_uuid  # fastq1
    data['input_files'][1]['uuid'] = fq2_uuid  # fastq2
    api = API()
    res = api.run_workflow(data, sfn=DEV_SFN)
    assert 'jobid' in res
    assert 'exec_arn' in res['_tibanna']
    time.sleep(60)
    # Unintentionally terminate EC2 instance
    ec2 = boto3.client('ec2')
    ec2_res = ec2.describe_instances(Filters=[{'Name': 'tag:Name', 'Values': ['awsem-' + res['jobid']]}])
    instance_id = ec2_res['Reservations'][0]['Instances'][0]['InstanceId']
    ec2.terminate_instances(InstanceIds=[instance_id])
    time.sleep(520)
    assert api.check_status(res['_tibanna']['exec_arn']) == 'FAILED'
