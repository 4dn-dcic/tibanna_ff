import pytest
from dcicutils.s3_utils import s3Utils
from dcicutils import ff_utils
import os
import uuid
import boto3
from tests.tibanna.ffcommon.conftest import read_event_file
from tibanna_ffcommon.portal_utils import (
    TibannaSettings
)
from tibanna_4dn.pony_utils import (
    ProcessedFileMetadata
)
from tibanna_4dn.vars import (
    DEFAULT_LAB,
    DEFAULT_AWARD,
    BUCKET_NAME,
    DEV_ENV
)


def pytest_runtest_setup(item):
    # called for running each test in directory
    print("Running lambda tests for: ", item)


valid_env = pytest.mark.skipif(not os.environ.get("S3_ENCRYPT_KEY", False),
                               reason='Required environment not setup to run test')


@pytest.fixture(scope='session')
def run_task_event_md5_fail():
    return get_event_file_for('run_task', event_file='event_fail.json')


@pytest.fixture(scope='session')
def used_env():
    return 'fourfront-webdev'


@pytest.fixture(scope='session')
def tibanna_env(used_env):
    return {'_tibanna': {'env': used_env}}


@pytest.fixture(scope='session')
def s3_utils(used_env):
    return s3Utils(env=used_env)


@pytest.fixture(scope='session')
def ff_keys(s3_utils):
    return s3_utils.get_access_keys('access_key_tibanna')


@pytest.fixture(scope='session')
def s3_trigger_event_data():
    return get_event_file_for('validate_md5_s3_trigger')


@pytest.fixture(scope='session')
def s3_trigger_event_data_pf():
    return get_event_file_for('validate_md5_s3_trigger', event_file='event_pf.json')


@pytest.fixture(scope='session')
def s3_trigger_event_data_pf_extra_status():
    return get_event_file_for('validate_md5_s3_trigger', event_file='event_pf_extra_status.json')


@pytest.fixture(scope='session')
def start_run_md5_data(ff_keys):
    return get_event_file_for('start_run', ff_keys=ff_keys, event_file='event_md5.json')


@pytest.fixture(scope='session')
def start_run_md5_mount_data(ff_keys):
    return get_event_file_for('start_run', ff_keys=ff_keys, event_file='event_md5-mount.json')


@pytest.fixture(scope='session')
def start_run_pseudo_workflow_event_data(ff_keys):
    return get_event_file_for('start_run', ff_keys=ff_keys, event_file='event_metadata_only.json')


@pytest.fixture(scope='session')
def start_run_nestedarray_data(ff_keys):
    return get_event_file_for('start_run', ff_keys=ff_keys, event_file='event-nestedarray.json')


@pytest.fixture(scope='session')
def start_run_dependency_data(ff_keys):
    return get_event_file_for('start_run', ff_keys=ff_keys, event_file='event_dependency.json')


@pytest.fixture(scope='session')
def start_run_dependency_fail_data(ff_keys):
    return get_event_file_for('start_run', ff_keys=ff_keys, event_file='event_dependency_fail.json')


@pytest.fixture(scope='session')
def start_run_fail_data(ff_keys):
    return get_event_file_for('start_run', ff_keys=ff_keys, event_file='event_fail.json')


@pytest.fixture(scope='session')
def start_run_fixedname_data(ff_keys):
    return get_event_file_for('start_run', ff_keys=ff_keys, event_file='event_fixedname.json')


@pytest.fixture(scope='session')
def start_run_hicprocessingbam_customfield_wALL_data(ff_keys):
    return get_event_file_for('start_run', ff_keys=ff_keys, event_file='event_hicprocessingbam_customfield_wALL.json')


@pytest.fixture(scope='session')
def start_run_hicprocessingbam_customfield_wArgname_data(ff_keys):
    return get_event_file_for('start_run', ff_keys=ff_keys,
                              event_file='event_hicprocessingbam_customfield_wArgname.json')


@pytest.fixture(scope='session')
def start_run_hicprocessingpartb_data(ff_keys):
    return get_event_file_for('start_run', ff_keys=ff_keys, event_file='event_hicprocessingpartb.json')


@pytest.fixture(scope='session')
def update_ffmeta_event_data(ff_keys):
    return get_event_file_for('update_ffmeta', ff_keys=ff_keys)


@pytest.fixture(scope='session')
def update_ffmeta_event_data_extra_md5(ff_keys):
    return get_event_file_for('update_ffmeta', ff_keys=ff_keys, event_file='event_extra_md5.json')


@pytest.fixture(scope='session')
def update_ffmeta_event_data_newmd5(ff_keys):
    return get_event_file_for('update_ffmeta', ff_keys=ff_keys, event_file='event_newmd5.json')


@pytest.fixture(scope='session')
def update_ffmeta_event_data_bed2multivec(ff_keys):
    return get_event_file_for('update_ffmeta', ff_keys=ff_keys, event_file='event_bed2multivec.json')


@pytest.fixture(scope='session')
def update_ffmeta_event_data_pairsqc(ff_keys):
    return get_event_file_for('update_ffmeta', ff_keys=ff_keys, event_file='event_pairsqc.json')


@pytest.fixture(scope='session')
def update_ffmeta_event_data_repliseq(ff_keys):
    return get_event_file_for('update_ffmeta', ff_keys=ff_keys, event_file='event_repliseq.json')


@pytest.fixture(scope='session')
def update_ffmeta_event_data_imargi(ff_keys):
    return get_event_file_for('update_ffmeta', ff_keys=ff_keys, event_file='event_imargi.json')


@pytest.fixture(scope='session')
def update_ffmeta_mcool(ff_keys):
    return get_event_file_for('update_ffmeta', ff_keys=ff_keys, event_file='event_mcool.json')


@pytest.fixture(scope='session')
def update_ffmeta_event_data_fastqc(ff_keys):
    return get_event_file_for('update_ffmeta', ff_keys=ff_keys, event_file='event_fastqc.json')


@pytest.fixture(scope='session')
def update_ffmeta_event_data_fastqc2(ff_keys):
    return get_event_file_for('update_ffmeta', ff_keys=ff_keys, event_file='event_fastqc2.json')


@pytest.fixture(scope='session')
def update_ffmeta_event_data_chipseq(ff_keys):
    return get_event_file_for('update_ffmeta', ff_keys=ff_keys, event_file='event_chipseq.json')


@pytest.fixture(scope='session')
def update_ffmeta_metaonly_data(ff_keys):
    return get_event_file_for('update_ffmeta', ff_keys=ff_keys, event_file='event_metadataonly.json')


@pytest.fixture(scope='session')
def update_ffmeta_metaonly_data2(ff_keys):
    return get_event_file_for('update_ffmeta', ff_keys=ff_keys, event_file='event_metadata_2.json')


@pytest.fixture(scope='session')
def update_ffmeta_tmpdata(ff_keys):
    return get_event_file_for('update_ffmeta', ff_keys=ff_keys, event_file='event_tmp.json')


@pytest.fixture(scope='session')
def update_ffmeta_hicbam(ff_keys):
    return get_event_file_for('update_ffmeta', ff_keys=ff_keys, event_file='event_hicbam.json')


@pytest.fixture(scope='session')
def update_ffmeta_event_data_rna_strandedness(ff_keys):
    return get_event_file_for('update_ffmeta', ff_keys=ff_keys, event_file='event_rna_strandedness.json')


@pytest.fixture(scope='session')
def update_ffmeta_event_data_madqc(ff_keys):
    return get_event_file_for('update_ffmeta', ff_keys=ff_keys, event_file='event_madqc.json')


@pytest.fixture(scope='session')
def update_ffmeta_event_data_fastq_first_line(ff_keys):
    return get_event_file_for('update_ffmeta', ff_keys=ff_keys, event_file='event_fastq_first_line.json')


@pytest.fixture(scope='session')
def update_ffmeta_event_data_re_check(ff_keys):
    return get_event_file_for('update_ffmeta', ff_keys=ff_keys, event_file='event_re_check.json')


@valid_env
def post_new_fastqfile(key, upload_file=None, upload_content=None):
    """upload_content must be in bytes"""
    ffobject = {"uuid": str(uuid.uuid4()),
                "file_format": "fastq",
                "description": "tibanna test",
                "lab": DEFAULT_LAB,
                "award": DEFAULT_AWARD}
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
                           upload_file=None, upload_content=None, extension=None, **kwargs):
    """upload_content must be in bytes"""
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
    if upload_content:
        f_uuid = res['@graph'][0]['uuid']
        accession = res['@graph'][0]['accession']
        upload_key = f_uuid + '/' + accession + '.' + extension
        boto3.client('s3').put_object(Body=upload_content,
                                      Bucket=BUCKET_NAME(DEV_ENV, 'FileFastq'),
                                      Key=upload_key)
    return res['@graph'][0]['uuid']


@valid_env
def post_new_qc(qctype, key, **kwargs):
    if not qctype.startswith('QualityMetric'):
        raise Exception("qctype must begin with QualityMetric")
    qc_object = {"uuid": str(uuid.uuid4()),
                 "lab": DEFAULT_LAB,
                 "award": DEFAULT_AWARD}
    for k, v in kwargs.items():
        qc_object[k] = v
    res = ff_utils.post_metadata(qc_object, qctype, key=key)
    return res['@graph'][0]['uuid']


def get_test_json(file_name):
    dir_path = os.path.dirname(os.path.realpath(__file__))
    event_file_name = os.path.join(dir_path, '..', '..', '..', 'test_json', 'pony', file_name)
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
