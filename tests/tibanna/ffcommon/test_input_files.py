from tibanna_ffcommon.input_files import (
    FFInputFiles,
    FFInputFile
)
import pytest
import mock


@pytest.fixture
def fake_inputfile1():
    return {
               "workflow_argument_name": "input_vcf",
               "uuid": "e7fc0f39-560a-4c5c-9bdb-040e43819eb7",
               "unzip": "gz"
           }

@pytest.fixture
def fake_inputfile2():
    return {
               "workflow_argument_name": "unrelated",
               "uuid": "e07590b8-a6cc-42ee-85b9-ed16ed0ec34e",
               "mount": True,
               "format_if_extra": "rck.tar.index"
           }

@pytest.fixture
def fake_inputfile3():
    return {
               "workflow_argument_name": "trio",
               "uuid": ['b4cde603-4df9-48d2-bd06-765900b9f165',
                        '2c6ca4b1-62b6-4235-98c0-e4c25a9ab1ec'],
               "rename": ['abc.rck', 'def.rck']
           }
@pytest.fixture
def fake_inputfiles(fake_inputfile1, fake_inputfile2, fake_inputfile3):
    return [fake_inputfile1, fake_inputfile2, fake_inputfile3]


@pytest.fixture
def minimal_file_metadata1():
    return {'file_format': 'vcf', '@type': ['FileProcessed'],
            'upload_key': 'someuuid/someacc.vcf.gz'}

@pytest.fixture
def minimal_file_metadata_4dn_opendata():
    return {'file_format': 'txt', '@type': ['FileReference'],
            'upload_key': 'someuuid/someacc.txt',
            'open_data_url': 'https://4dn-open-data-public.s3.amazonaws.com/fourfront-webprod/files/someuuid/someacc.txt'}


def test_FFInputFiles(fake_inputfiles):
    ffinpf = FFInputFiles(fake_inputfiles)
    assert ffinpf
    assert len(ffinpf.input_files) == 3
    assert isinstance(ffinpf.input_files[0], FFInputFile)

def test_FFInputFile(fake_inputfile1):
    ffinpf = FFInputFile(**fake_inputfile1)
    assert ffinpf.workflow_argument_name == 'input_vcf'
    assert ffinpf.uuid == 'e7fc0f39-560a-4c5c-9bdb-040e43819eb7'
    assert ffinpf.unzip == 'gz'
    assert ffinpf.mount is False
    assert ffinpf.rename == ''
    assert ffinpf.format_if_extra == ''

def test_FFInputFile(fake_inputfile2):
    ffinpf = FFInputFile(**fake_inputfile2)
    assert ffinpf.workflow_argument_name == 'unrelated'
    assert ffinpf.uuid == 'e07590b8-a6cc-42ee-85b9-ed16ed0ec34e'
    assert ffinpf.unzip == ''
    assert ffinpf.mount is True
    assert ffinpf.rename == ''
    assert ffinpf.format_if_extra == 'rck.tar.index'

def test_FFInputFile(fake_inputfile3):
    ffinpf = FFInputFile(**fake_inputfile3)
    assert ffinpf.workflow_argument_name == 'trio'
    assert ffinpf.uuid == ['b4cde603-4df9-48d2-bd06-765900b9f165',
                           '2c6ca4b1-62b6-4235-98c0-e4c25a9ab1ec']
    assert ffinpf.unzip == ''
    assert ffinpf.mount is False
    assert ffinpf.rename == ['abc.rck', 'def.rck']
    assert ffinpf.format_if_extra == ''

def test_FFInputFile(minimal_file_metadata1):
    """Just testing cached metadata use, no need to actually have any input file info"""
    ffinpf = FFInputFile(uuid='someuuid', workflow_argument_name='')
    ffinpf._metadata['someuuid'] = minimal_file_metadata1  # fake-cache a fake metadata
    assert ffinpf.get_file_type_from_uuid('someuuid') == 'FileProcessed'
    assert ffinpf.get_object_key_from_uuid('someuuid') == 'someacc.vcf.gz'
    assert ffinpf.get_upload_key_from_uuid('someuuid') == 'someuuid/someacc.vcf.gz'
    assert ffinpf.get_s3_key_from_uuid('someuuid') == 'someuuid/someacc.vcf.gz'
    # bucket & object_key fill_in test
    ffinpf.ff_env = 'data'
    assert ffinpf.bucket_name == 'elasticbeanstalk-fourfront-webprod-wfoutput'
    assert ffinpf.object_key == 'someacc.vcf.gz'

def test_FFInputFile_4dn_opendata(minimal_file_metadata_4dn_opendata):
    """Just testing cached metadata use, no need to actually have any input file info"""
    ffinpf = FFInputFile(uuid='someuuid', workflow_argument_name='')
    ffinpf._metadata['someuuid'] = minimal_file_metadata_4dn_opendata  # fake-cache a fake metadata
    assert ffinpf.get_file_type_from_uuid('someuuid') == 'FileReference'
    assert ffinpf.get_object_key_from_uuid('someuuid') == 'someacc.txt'
    assert ffinpf.get_upload_key_from_uuid('someuuid') == 'someuuid/someacc.txt'
    assert ffinpf.get_s3_key_from_uuid('someuuid') == 'fourfront-webprod/files/someuuid/someacc.txt'
    # # bucket & object_key fill_in test
    ffinpf.ff_env = 'data'
    assert ffinpf.bucket_name == '4dn-open-data-public'
    assert ffinpf.object_key == 'someacc.txt'

def test_FFInputFile_as_dict(minimal_file_metadata1):
    ffinpf = FFInputFile(uuid='someuuid', workflow_argument_name='somearg', ff_env='data')
    ffinpf._metadata['someuuid'] = minimal_file_metadata1  # fake-cache a fake metadata
    assert ffinpf.as_dict() == {'bucket_name': 'elasticbeanstalk-fourfront-webprod-wfoutput',
                                'object_key': 'someacc.vcf.gz',
                                'uuid': 'someuuid',
                                'workflow_argument_name': 'somearg',
                                'unzip': '',
                                'mount': False,
                                'rename': '',
                                'format_if_extra': ''}
