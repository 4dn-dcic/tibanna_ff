from tibanna_ffcommon.portal_utils import (
    TibannaSettings,
    FormatExtensionMap,
    get_extra_file_key,
)
from tibanna_4dn.pony_utils import (
    WorkflowRunMetadata,
    FourfrontStarter,
    ProcessedFileMetadata,
)
import pytest
from tests.tibanna.pony.conftest import valid_env, logger
import mock
from tibanna.vars import DYNAMODB_TABLE, DYNAMODB_KEYNAME
from tibanna.job import Job
from tibanna_ffcommon.core import API
import uuid
import time
import boto3


@valid_env
def test_tibanna():
    data = {'env': 'fourfront-webdev',
            'settings': {'1': '1'}}
    tibanna = TibannaSettings(**data)
    assert tibanna
    assert tibanna.as_dict() == data


@valid_env
@pytest.mark.webtest
def test_format_extension_map():
    data = {'env': 'fourfront-webdev',
            'settings': {'1': '1'}}
    tibanna = TibannaSettings(**data)
    fe_map = FormatExtensionMap(tibanna.ff_keys)
    assert(fe_map)
    assert 'bwt' in fe_map.fe_dict.keys()


@valid_env
@pytest.mark.webtest
def test_get_extra_file_key(start_run_md5_data):
    data = {'env': 'fourfront-webdev',
            'settings': {'1': '1'}}
    tibanna = TibannaSettings(**data)
    fe_map = FormatExtensionMap(tibanna.ff_keys)
    fe_map = FormatExtensionMap(tibanna.ff_keys)
    infile_key = 'hahaha/lalala.bedGraph.gz'
    infile_format = 'bg'
    extra_file_format = 'bw'
    extra_file_key = get_extra_file_key(infile_format, infile_key, extra_file_format, fe_map)
    assert extra_file_key == 'hahaha/lalala.bw'


def test_create_workflowrun_from_event_parameter(update_ffmeta_event_data_newmd5):
    meta = update_ffmeta_event_data_newmd5['ff_meta'].copy()
    meta['app_name'] = 'md5'
    ff_wfr = WorkflowRunMetadata(**meta)
    assert ff_wfr


@pytest.fixture()
def proc_file_in_webdev():
    return {'status': 'released',
            'uuid': 'f6d5ba22-aaf9-48e9-8df4-bc5c131c96af',
            'file_format': 'normvector_juicerformat',
            'accession': '4DNFIRO3UX7I',
            'award': '/awards/1U01CA200059-01/',
            'lab': '/labs/4dn-dcic-lab/'}


def test_processedFileMetadata(proc_file_in_webdev):
    pf = ProcessedFileMetadata(**proc_file_in_webdev)
    assert pf


@valid_env
@pytest.mark.webtest
def test_merge_source_experiment(start_run_md5_data):
    input_file = {
        "bucket_name": "elasticbeanstalk-fourfront-webdev-wfoutput",
        "workflow_argument_name": "input_pairs",
        "uuid": ["d2c897ec-bdb2-47ce-b1b1-845daccaa571", "d2c897ec-bdb2-47ce-b1b1-845daccaa571"],
        "object_key": ["4DNFI25JXLLI.pairs.gz", "4DNFI25JXLLI.pairs.gz"]
    }
    data = start_run_md5_data
    starter = FourfrontStarter(**data)
    starter.inp.input_files = [input_file]
    res = starter.merge_source_experiments()
    logger.debug("response from merge_source_experiment=" + str(res))
    assert 'fake_source_experiment' in res


@valid_env
@pytest.mark.webtest
def test_merge_source_experiment(start_run_md5_mount_data):
    starter = FourfrontStarter(**start_run_md5_mount_data)
    starter.create_ff()
    starter.inp.add_args(starter.ff)
    assert 'input_file' in starter.inp.args.input_files
    assert 'mount' in starter.inp.args.input_files['input_file']
    assert starter.inp.args.input_files['input_file']['mount']


@valid_env
@pytest.mark.webtest
def test_processed_extra_file_use_for(start_run_repliseq_data):
    starter = FourfrontStarter(**start_run_repliseq_data)
    exf = starter.pf_extra_files(['bg_px2', 'bw'], {'file_format': 'bw', 'use_for': 'visualization'})
    assert len(exf) == 2
    assert exf[1]['file_format'] == 'bw' and 'use_for' in exf[1]
    assert exf[1]['use_for'] == 'visualization'


@valid_env
@pytest.mark.webtest
def test_add_meta_to_dynamodb(start_run_md5_data):
    jobid = 'randomtestjobid-' + str(uuid.uuid4())
    Job.add_to_dd(jobid, 'someexecname', 'somesfn', 'somelogbucket')
    starter = FourfrontStarter(**start_run_md5_data)
    starter.inp.jobid = jobid
    starter.create_ff()
    starter.add_meta_to_dynamodb()
    logger.debug("jobid=%s" % jobid)
    time.sleep(10)
    dd_info = Job.info(jobid)
    assert dd_info
    print(dd_info)
    assert 'WorkflowRun uuid' in dd_info
    assert dd_info['WorkflowRun uuid'] == starter.ff.uuid
    assert 'env' in dd_info
    assert dd_info['env'] == starter.tbn.env
    # cleanup
    dd = boto3.client('dynamodb')
    dd.delete_item(TableName=DYNAMODB_TABLE, Key={DYNAMODB_KEYNAME : {'S' : jobid}})
