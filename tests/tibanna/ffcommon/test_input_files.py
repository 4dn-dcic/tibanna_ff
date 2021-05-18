from tibanna_ffcommon.input_files import (
    FFInputFiles,
    FFInputFile
)
import pytest
import mock
from tibanna_ffcommon.exceptions import (
    MalFormattedFFInputException
)
from tibanna_ffcommon.file_format import (
    FormatExtensionMap
)
from tibanna_ffcommon.wfr import (
    InputFilesForWFRMeta
)

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
def fake_metadata():
    return {'e7fc0f39-560a-4c5c-9bdb-040e43819eb7':
                {'file_format': 'vcf', '@type': ['FileProcessed'],
                 'upload_key': 'e7fc0f39-560a-4c5c-9bdb-040e43819eb7/someacc1.vcf.gz'},
            'e07590b8-a6cc-42ee-85b9-ed16ed0ec34e':
                {'file_format': 'rck.tar', '@type': ['FileReference'],
                 'upload_key': 'e07590b8-a6cc-42ee-85b9-ed16ed0ec34e/someacc2.vcf.gz'},
            'b4cde603-4df9-48d2-bd06-765900b9f165':
                {'file_format': 'rck', '@type': ['FileProcessed'],
                 'upload_key': 'b4cde603-4df9-48d2-bd06-765900b9f165/someacc3.vcf.gz'},
            '2c6ca4b1-62b6-4235-98c0-e4c25a9ab1ec':
                {'file_format': 'rck', '@type': ['FileProcessed'],
                 'upload_key': '2c6ca4b1-62b6-4235-98c0-e4c25a9ab1ec/someacc4.vcf.gz'}}

@pytest.fixture
def minimal_file_metadata1():
    return {'file_format': 'vcf', '@type': ['FileProcessed'],
            'upload_key': 'someuuid/someacc.vcf.gz'}

@pytest.fixture
def minimal_file_metadata2():
    return {'file_format': 'vcf', '@type': ['FileProcessed'],
            'upload_key': 'someuuid2/someacc2.vcf.gz'}

@pytest.fixture
def minimal_file_metadata_4dn_opendata():
    return {'file_format': 'txt', '@type': ['FileReference'],
            'upload_key': 'someuuid/someacc.txt',
            'open_data_url': 'https://4dn-open-data-public.s3.amazonaws.com/fourfront-webprod/files/someuuid/someacc.txt'}

@pytest.fixture
def minimal_file_metadata_4dn_opendata2():
    return {'file_format': 'txt', '@type': ['FileReference'],
            'upload_key': 'someuuid2/someacc2.txt',
            'open_data_url': 'https://4dn-open-data-public.s3.amazonaws.com/fourfront-webprod/files/someuuid2/someacc2.txt'}

@pytest.fixture
def minimal_file_metadata_w_extrafile():
    return {'file_format': 'bwt', '@type': ['FileReference'],
            'upload_key': 'someuuid/someacc.bwt',
            'extra_files': [{'file_format': 'sa', 'status': 'uploaded'},
                            {'file_format': 'ann', 'status': 'uploaded'}]}

@pytest.fixture
def minimal_file_metadata_w_extrafile_not_ready():
    return {'file_format': 'bwt', '@type': ['FileReference'],
            'upload_key': 'someuuid/someacc.bwt',
            'extra_files': [{'file_format': 'sa', 'status': 'uploading'},
                            {'file_format': 'ann', 'status': 'deleted'}]}

@pytest.fixture
def minimal_file_metadata_w_extrafile_not_ready2():
    return {'file_format': 'bwt', '@type': ['FileReference'],
            'upload_key': 'someuuid2/someacc2.bwt',
            'extra_files': [{'file_format': 'sa', 'status': 'to be uploaded by workflow'},
                            {'file_format': 'ann', 'status': 'uploaded'}]}

@pytest.fixture
def minimal_file_metadata_4dn_opendata_w_extrafile():
    return {'file_format': 'bwt', '@type': ['FileReference'],
            'upload_key': 'someuuid/someacc.bwt',
            'extra_files': [{'file_format': 'sa', 'status': 'uploaded'},
                            {'file_format': 'ann', 'status': 'uploaded'}],
            'open_data_url': 'https://4dn-open-data-public.s3.amazonaws.com/fourfront-webprod/files/someuuid/someacc.bwt'}

@pytest.fixture
def minimal_file_metadata_4dn_opendata_w_extrafile2():
    return {'file_format': 'bwt', '@type': ['FileReference'],
            'upload_key': 'someuuid2/someacc2.bwt',
            'extra_files': [{'file_format': 'sa', 'status': 'uploaded'},
                            {'file_format': 'ann', 'status': 'uploaded'}],
            'open_data_url': 'https://4dn-open-data-public.s3.amazonaws.com/fourfront-webprod/files/someuuid2/someacc2.bwt'}

@pytest.fixture
def fake_format_search_result():
    return [{'file_format': 'bwt',
             'standard_file_extension': 'bwt',
             'extrafile_formats': ['/file-formats/sa/', '/file-formats/ann/']},
             {'file_format': 'sa',
              'standard_file_extension': 'sa'},
             {'file_format': 'ann',
              'standard_file_extension': 'ann'}
            ]

# Tests for FFInputFile class
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
    ffinpf = FFInputFile(uuid='someuuid', workflow_argument_name='somearg')
    # cache a fake metadata for data without 4dn open data url
    ffinpf._metadata['someuuid'] = minimal_file_metadata1
    assert ffinpf.get_file_type_from_uuid('someuuid') == 'FileProcessed'
    assert ffinpf.get_object_key_from_uuid('someuuid') == 'someacc.vcf.gz'
    assert ffinpf.get_upload_key_from_uuid('someuuid') == 'someuuid/someacc.vcf.gz'
    assert ffinpf.get_s3_key_from_uuid('someuuid') == 'someuuid/someacc.vcf.gz'
    # bucket & object_key fill_in test for our 4dn bucket
    ffinpf.ff_env = 'data'
    assert ffinpf.bucket_name == 'elasticbeanstalk-fourfront-webprod-wfoutput'
    assert ffinpf.object_key == 'someacc.vcf.gz'
    assert ffinpf.s3_key == 'someuuid/someacc.vcf.gz'

def test_FFInputFile_w_extrafile(minimal_file_metadata_w_extrafile,
                                 fake_format_search_result):
    ffinpf = FFInputFile(uuid='someuuid', workflow_argument_name='somearg')
    # cache a fake metadata for data without 4dn open data url
    ffinpf._metadata['someuuid'] = minimal_file_metadata_w_extrafile
    # bucket & object_key fill_in test for our 4dn bucket
    ffinpf.ff_env = 'data'
    ffinpf._fe_map = FormatExtensionMap(ffe_all=fake_format_search_result)
    assert ffinpf.bucket_name == 'elasticbeanstalk-fourfront-webprod-files'
    assert ffinpf.extra_file_s3_keys == ['someuuid/someacc.sa', 'someuuid/someacc.ann']

def test_FFInputFile_w_extrafile_not_ready(minimal_file_metadata_w_extrafile_not_ready,
                                           fake_format_search_result):
    ffinpf = FFInputFile(uuid='someuuid', workflow_argument_name='somearg')
    # cache a fake metadata for data without 4dn open data url
    ffinpf._metadata['someuuid'] = minimal_file_metadata_w_extrafile_not_ready
    # bucket & object_key fill_in test for our 4dn bucket
    ffinpf.ff_env = 'data'
    ffinpf._fe_map = FormatExtensionMap(ffe_all=fake_format_search_result)
    assert ffinpf.bucket_name == 'elasticbeanstalk-fourfront-webprod-files'
    assert ffinpf.extra_file_s3_keys is None

def test_FFInputFile_w_extrafile_not_ready2(minimal_file_metadata_w_extrafile_not_ready2,
                                            fake_format_search_result):
    ffinpf = FFInputFile(uuid='someuuid2', workflow_argument_name='somearg')
    # cache a fake metadata for data without 4dn open data url
    ffinpf._metadata['someuuid2'] = minimal_file_metadata_w_extrafile_not_ready2
    # bucket & object_key fill_in test for our 4dn bucket
    ffinpf.ff_env = 'data'
    ffinpf._fe_map = FormatExtensionMap(ffe_all=fake_format_search_result)
    assert ffinpf.bucket_name == 'elasticbeanstalk-fourfront-webprod-files'
    assert ffinpf.extra_file_s3_keys == 'someuuid2/someacc2.ann'

def test_FFInputFile_format_if_extra(minimal_file_metadata_w_extrafile,
                                     fake_format_search_result):
    ffinpf = FFInputFile(uuid='someuuid', workflow_argument_name='somearg',
                         format_if_extra='ann')
    # cache a fake metadata for data without 4dn open data url
    ffinpf._metadata['someuuid'] = minimal_file_metadata_w_extrafile
    # bucket & object_key fill_in test for our 4dn bucket
    ffinpf.ff_env = 'data'
    ffinpf._fe_map = FormatExtensionMap(ffe_all=fake_format_search_result)
    assert ffinpf.bucket_name == 'elasticbeanstalk-fourfront-webprod-files'
    assert ffinpf.s3_key == 'someuuid/someacc.ann'
    assert not ffinpf.extra_file_s3_keys

def test_FFInputFile_format_if_extra_not_ready(minimal_file_metadata_w_extrafile_not_ready,
                                               fake_format_search_result):
    ffinpf = FFInputFile(uuid='someuuid', workflow_argument_name='somearg',
                         format_if_extra='sa')  # 'uploading'
    # cache a fake metadata for data without 4dn open data url
    ffinpf._metadata['someuuid'] = minimal_file_metadata_w_extrafile_not_ready
    # bucket & object_key fill_in test for our 4dn bucket
    ffinpf.ff_env = 'data'
    ffinpf._fe_map = FormatExtensionMap(ffe_all=fake_format_search_result)
    assert ffinpf.bucket_name == 'elasticbeanstalk-fourfront-webprod-files'
    assert ffinpf.s3_key == 'someuuid/someacc.sa'
    assert not ffinpf.extra_file_s3_keys

def test_FFInputFile_4dn_opendata(minimal_file_metadata_4dn_opendata):
    ffinpf = FFInputFile(uuid='someuuid', workflow_argument_name='somearg')
    # cache a fake metadata for data with 4dn open data url
    ffinpf._metadata['someuuid'] = minimal_file_metadata_4dn_opendata
    assert ffinpf.get_file_type_from_uuid('someuuid') == 'FileReference'
    assert ffinpf.get_object_key_from_uuid('someuuid') == 'someacc.txt'
    assert ffinpf.get_upload_key_from_uuid('someuuid') == 'someuuid/someacc.txt'
    assert ffinpf.get_s3_key_from_uuid('someuuid') == 'fourfront-webprod/files/someuuid/someacc.txt'
    # # bucket & object_key fill_in test for 4dn open data bucket
    ffinpf.ff_env = 'data'
    assert ffinpf.bucket_name == '4dn-open-data-public'
    assert ffinpf.object_key == 'someacc.txt'
    assert ffinpf.s3_key == 'fourfront-webprod/files/someuuid/someacc.txt'

def test_FFInputFile_4dn_opendata_w_extrafile(minimal_file_metadata_4dn_opendata_w_extrafile,
                                              fake_format_search_result):
    ffinpf = FFInputFile(uuid='someuuid', workflow_argument_name='somearg')
    # cache a fake metadata for data without 4dn open data url
    ffinpf._metadata['someuuid'] = minimal_file_metadata_4dn_opendata_w_extrafile
    # bucket & object_key fill_in test for our 4dn bucket
    ffinpf.ff_env = 'data'
    ffinpf._fe_map = FormatExtensionMap(ffe_all=fake_format_search_result)
    assert ffinpf.get_extra_file_formats_from_uuid('someuuid') == ['sa', 'ann']
    assert ffinpf.get_extra_file_s3_keys_from_uuid('someuuid') == ['fourfront-webprod/files/someuuid/someacc.sa', 'fourfront-webprod/files/someuuid/someacc.ann']
    assert ffinpf.bucket_name == '4dn-open-data-public'
    assert ffinpf.extra_file_s3_keys == ['fourfront-webprod/files/someuuid/someacc.sa', 'fourfront-webprod/files/someuuid/someacc.ann']

def test_FFInputFile_list(minimal_file_metadata1, minimal_file_metadata2):
    ffinpf = FFInputFile(uuid=['someuuid', 'someuuid2'], workflow_argument_name='somearg')
    # cache a fake metadata for both one with 4dn open data url and one without
    # This should be a problem since all files for a single argument should be
    # from the same bucket.
    ffinpf._metadata['someuuid'] = minimal_file_metadata1
    ffinpf._metadata['someuuid2'] = minimal_file_metadata2
    ffinpf.ff_env = 'data'
    assert ffinpf.bucket_name == 'elasticbeanstalk-fourfront-webprod-wfoutput'
    assert ffinpf.s3_key == ['someuuid/someacc.vcf.gz', 'someuuid2/someacc2.vcf.gz']

def test_FFInputFile_list_w_extrafile_not_ready(minimal_file_metadata_w_extrafile_not_ready,
                                                minimal_file_metadata_w_extrafile_not_ready2,
                                                fake_format_search_result):
    ffinpf = FFInputFile(uuid=['someuuid', 'someuuid2'],
                         workflow_argument_name='somearg',
                         rename=['somename1.bwt', 'somename2.bwt'])
    # cache a fake metadata for both one with 4dn open data url and one without
    # This should be a problem since all files for a single argument should be
    # from the same bucket.
    ffinpf._metadata['someuuid'] = minimal_file_metadata_w_extrafile_not_ready
    ffinpf._metadata['someuuid2'] = minimal_file_metadata_w_extrafile_not_ready2
    ffinpf.ff_env = 'data'
    ffinpf._fe_map = FormatExtensionMap(ffe_all=fake_format_search_result)
    assert ffinpf.bucket_name == 'elasticbeanstalk-fourfront-webprod-files'
    assert ffinpf.extra_file_s3_keys == 'someuuid2/someacc2.ann'
    assert ffinpf.extra_file_renames == 'somename2.ann'

def test_FFInputFile_list_4dn_opendata(minimal_file_metadata_4dn_opendata,
                                       minimal_file_metadata_4dn_opendata2,
                                       fake_format_search_result):
    ffinpf = FFInputFile(uuid=['someuuid', 'someuuid2'], workflow_argument_name='somearg')
    # cache a fake metadata for both one with 4dn open data url and one without
    # This should be a problem since all files for a single argument should be
    # from the same bucket.
    ffinpf._metadata['someuuid'] = minimal_file_metadata_4dn_opendata
    ffinpf._metadata['someuuid2'] = minimal_file_metadata_4dn_opendata2
    ffinpf.ff_env = 'data'
    ffinpf._fe_map = FormatExtensionMap(ffe_all=fake_format_search_result)
    assert ffinpf.bucket_name == '4dn-open-data-public'
    assert ffinpf.s3_key == ['fourfront-webprod/files/someuuid/someacc.txt',
                             'fourfront-webprod/files/someuuid2/someacc2.txt']
    assert ffinpf.extra_file_s3_keys is None
    assert ffinpf.extra_file_renames is ''

def test_FFInputFile_list_4dn_opendata_w_extrafile(minimal_file_metadata_4dn_opendata_w_extrafile,
                                                   minimal_file_metadata_4dn_opendata_w_extrafile2,
                                                   fake_format_search_result):
    ffinpf = FFInputFile(uuid=['someuuid', 'someuuid2'],
                         workflow_argument_name='somearg',
                         rename=['somename.bwt', 'somename2.bwt'])
    # cache a fake metadata for both one with 4dn open data url and one without
    # This should be a problem since all files for a single argument should be
    # from the same bucket.
    ffinpf._metadata['someuuid'] = minimal_file_metadata_4dn_opendata_w_extrafile
    ffinpf._metadata['someuuid2'] = minimal_file_metadata_4dn_opendata_w_extrafile2
    ffinpf.ff_env = 'data'
    ffinpf._fe_map = FormatExtensionMap(ffe_all=fake_format_search_result)
    assert ffinpf.bucket_name == '4dn-open-data-public'
    assert ffinpf.extra_file_s3_keys == [['fourfront-webprod/files/someuuid/someacc.sa',
                                          'fourfront-webprod/files/someuuid/someacc.ann'],
                                         ['fourfront-webprod/files/someuuid2/someacc2.sa',
                                          'fourfront-webprod/files/someuuid2/someacc2.ann']]
    assert ffinpf.extra_file_renames == [['somename.sa', 'somename.ann'],
                                         ['somename2.sa', 'somename2.ann']]

def test_FFInputFile_mix_4dn_opendata_and_non_open_data(minimal_file_metadata1,
                                                        minimal_file_metadata_4dn_opendata):
    ffinpf = FFInputFile(uuid=['someuuid', 'someuuid2'], workflow_argument_name='somearg')
    # cache a fake metadata for both one with 4dn open data url and one without
    # This should be a problem since all files for a single argument should be
    # from the same bucket.
    ffinpf._metadata['someuuid'] = minimal_file_metadata1
    ffinpf._metadata['someuuid2'] = minimal_file_metadata_4dn_opendata
    ffinpf.ff_env = 'data'
    with pytest.raises(MalFormattedFFInputException) as ex_info:
        ffinpf.bucket_name
    assert 'All the input files for a given argument name must be in the same bucket' in str(ex_info.value)

def test_FFInputFile_as_dict(minimal_file_metadata1):
    ffinpf = FFInputFile(uuid='someuuid', workflow_argument_name='somearg', ff_env='data')
    # cache a fake metadata for data without 4dn open data url
    ffinpf._metadata['someuuid'] = minimal_file_metadata1
    assert ffinpf.as_dict() == {'bucket_name': 'elasticbeanstalk-fourfront-webprod-wfoutput',
                                'object_key': 'someacc.vcf.gz',
                                'uuid': 'someuuid',
                                'workflow_argument_name': 'somearg',
                                'unzip': '',
                                'mount': False,
                                'rename': '',
                                'format_if_extra': ''}

def test_FFInputFile_create_unicorn_arg_input_file(minimal_file_metadata1):
    ffinpf = FFInputFile(uuid='someuuid', workflow_argument_name='somearg', ff_env='data')
    # cache a fake metadata for data without 4dn open data url
    ffinpf._metadata['someuuid'] = minimal_file_metadata1
    res = ffinpf.create_unicorn_arg_input_file()
    assert res == {'somearg': {'bucket_name': 'elasticbeanstalk-fourfront-webprod-wfoutput',
                               'object_key': 'someuuid/someacc.vcf.gz',  # actual s3 key
                               'unzip': '',
                               'mount': False,
                               'rename': ''}}

def test_FFInputFile_create_unicorn_arg_secondary_file(minimal_file_metadata_w_extrafile,
                                                       fake_format_search_result):
    ffinpf = FFInputFile(uuid='someuuid', workflow_argument_name='somearg', ff_env='data')
    # cache a fake metadata for data without 4dn open data url
    ffinpf._metadata['someuuid'] = minimal_file_metadata_w_extrafile
    ffinpf._fe_map = FormatExtensionMap(ffe_all=fake_format_search_result)
    res = ffinpf.create_unicorn_arg_secondary_file()
    assert res == {'somearg': {'bucket_name': 'elasticbeanstalk-fourfront-webprod-files',
                               'object_key': ['someuuid/someacc.sa', 'someuuid/someacc.ann'],  # actual s3 key
                               'mount': False,
                               'rename': ''}}

def test_FFInputFile_create_unicorn_arg_input_file_format_if_extra(minimal_file_metadata_w_extrafile,
                                                                   fake_format_search_result):
    ffinpf = FFInputFile(uuid='someuuid', workflow_argument_name='somearg', ff_env='data',
                         format_if_extra='ann')
    # cache a fake metadata for data without 4dn open data url
    ffinpf._metadata['someuuid'] = minimal_file_metadata_w_extrafile
    ffinpf._fe_map = FormatExtensionMap(ffe_all=fake_format_search_result)
    res = ffinpf.create_unicorn_arg_input_file()
    assert res == {'somearg': {'bucket_name': 'elasticbeanstalk-fourfront-webprod-files',
                               'object_key': 'someuuid/someacc.ann',  # actual s3 key
                               'unzip': '',
                               'mount': False,
                               'rename': ''}}

def test_FFInputFile_create_unicorn_arg_secondary_file_format_if_extra(minimal_file_metadata_w_extrafile,
                                                                       fake_format_search_result):
    ffinpf = FFInputFile(uuid='someuuid', workflow_argument_name='somearg', ff_env='data',
                         format_if_extra='ann')
    # cache a fake metadata for data without 4dn open data url
    ffinpf._metadata['someuuid'] = minimal_file_metadata_w_extrafile
    ffinpf._fe_map = FormatExtensionMap(ffe_all=fake_format_search_result)
    assert not ffinpf.create_unicorn_arg_secondary_file()

def test_FFInputFile_create_unicorn_arg_input_file_list(minimal_file_metadata1, minimal_file_metadata2):
    ffinpf = FFInputFile(uuid=['someuuid', 'someuuid2'],
                         workflow_argument_name='somearg',
                         ff_env='data')
    # cache a fake metadata for data without 4dn open data url
    ffinpf._metadata['someuuid'] = minimal_file_metadata1
    ffinpf._metadata['someuuid2'] = minimal_file_metadata2
    res = ffinpf.create_unicorn_arg_input_file()
    assert res == {'somearg': {'bucket_name': 'elasticbeanstalk-fourfront-webprod-wfoutput',
                               'object_key': ['someuuid/someacc.vcf.gz', 'someuuid2/someacc2.vcf.gz'],
                               'unzip': '',
                               'mount': False,
                               'rename': ''}}

def test_FFInputFile_create_unicorn_arg_secondary_file_list(minimal_file_metadata_w_extrafile,
                                                            minimal_file_metadata_w_extrafile_not_ready2,
                                                            fake_format_search_result):
    ffinpf = FFInputFile(uuid=['someuuid', 'someuuid2'],
                         workflow_argument_name='somearg',
                         rename=['somename1.bwt', 'somename2.bwt'],
                         mount=True,
                         ff_env='data')
    # cache a fake metadata for data without 4dn open data url
    ffinpf._metadata['someuuid'] = minimal_file_metadata_w_extrafile
    ffinpf._metadata['someuuid2'] = minimal_file_metadata_w_extrafile_not_ready2
    ffinpf._fe_map = FormatExtensionMap(ffe_all=fake_format_search_result)
    res = ffinpf.create_unicorn_arg_secondary_file()
    assert res == {'somearg': {'bucket_name': 'elasticbeanstalk-fourfront-webprod-files',
                               'object_key': [['someuuid/someacc.sa', 'someuuid/someacc.ann'],
                                              ['someuuid2/someacc2.ann']],
                               'mount': True,
                               'rename': [['somename1.sa', 'somename1.ann'], ['somename2.ann']]}}

def test_FFInputFile_add_to_input_files_for_wfrmeta():
    ffinpf = FFInputFile(uuid='someuuid',
                         workflow_argument_name='somearg')
    inpfws = InputFilesForWFRMeta()
    ffinpf.add_to_input_files_for_wfrmeta(inpfws)
    res = inpfws.as_dict()
    assert res == [{'workflow_argument_name': 'somearg',
                    'value': 'someuuid',
                    'dimension': '0',
                    'ordinal': 1}]

def test_FFInputFile_add_to_input_files_for_wfrmeta_1d_list():
    ffinpf = FFInputFile(uuid=['someuuid', 'someuuid2'],
                         workflow_argument_name='somearg')
    inpfws = InputFilesForWFRMeta()
    ffinpf.add_to_input_files_for_wfrmeta(inpfws)
    res = inpfws.as_dict()
    assert res == [{'workflow_argument_name': 'somearg',
                    'value': 'someuuid',
                    'dimension': '0',
                    'ordinal': 1},
                   {'workflow_argument_name': 'somearg',
                    'value': 'someuuid2',
                    'dimension': '1',
                    'ordinal': 2}]

def test_FFInputFile_add_to_input_files_for_wfrmeta_2d_list():
    ffinpf = FFInputFile(uuid=[['someuuid', 'someuuid2'],
                               ['someuuid3', 'someuuid4']],
                         workflow_argument_name='somearg')
    inpfws = InputFilesForWFRMeta()
    ffinpf.add_to_input_files_for_wfrmeta(inpfws)
    res = inpfws.as_dict()
    assert res == [{'workflow_argument_name': 'somearg',
                    'value': 'someuuid',
                    'dimension': '0-0',
                    'ordinal': 1},
                   {'workflow_argument_name': 'somearg',
                    'value': 'someuuid2',
                    'dimension': '0-1',
                    'ordinal': 2},
                   {'workflow_argument_name': 'somearg',
                    'value': 'someuuid3',
                    'dimension': '1-0',
                    'ordinal': 3},
                   {'workflow_argument_name': 'somearg',
                    'value': 'someuuid4',
                    'dimension': '1-1',
                    'ordinal': 4}]

# Tests for FFInputFiles class
def test_FFInputFiles(fake_inputfiles):
    ffinpfs = FFInputFiles(fake_inputfiles)
    assert ffinpfs
    assert len(ffinpfs.input_files) == 3
    assert isinstance(ffinpfs.input_files[0], FFInputFile)
    assert ffinpfs.input_files[0].uuid == 'e7fc0f39-560a-4c5c-9bdb-040e43819eb7'
    assert ffinpfs.input_files[1].uuid == 'e07590b8-a6cc-42ee-85b9-ed16ed0ec34e'
    assert ffinpfs.input_files[2].uuid == ['b4cde603-4df9-48d2-bd06-765900b9f165',
                                           '2c6ca4b1-62b6-4235-98c0-e4c25a9ab1ec']

def test_FFInputFiles_as_dict(fake_inputfiles, fake_metadata):
    ffinpfs = FFInputFiles(fake_inputfiles, ff_env='data')
    # put fake metadata into metadata cache
    for inpf in ffinpfs.input_files:
        inpf._metadata = fake_metadata
    assert ffinpfs.as_dict() == [{'bucket_name': 'elasticbeanstalk-fourfront-webprod-wfoutput',
                                  'object_key': 'someacc1.vcf.gz',
                                  'uuid': 'e7fc0f39-560a-4c5c-9bdb-040e43819eb7',
                                  'workflow_argument_name': 'input_vcf',
                                  'unzip': 'gz',
                                  'mount': False,
                                  'rename': '',
                                  'format_if_extra': ''},
                                 {'bucket_name': 'elasticbeanstalk-fourfront-webprod-files',
                                  'object_key': 'someacc2.vcf.gz',
                                  'uuid': 'e07590b8-a6cc-42ee-85b9-ed16ed0ec34e',
                                  'workflow_argument_name': 'unrelated',
                                  'unzip': '',
                                  'mount': True,
                                  'rename': '',
                                  'format_if_extra': 'rck.tar.index'},
                                 {'bucket_name': 'elasticbeanstalk-fourfront-webprod-wfoutput',
                                  'object_key': ['someacc3.vcf.gz', 'someacc4.vcf.gz'],
                                  'uuid': ['b4cde603-4df9-48d2-bd06-765900b9f165',
                                           '2c6ca4b1-62b6-4235-98c0-e4c25a9ab1ec'],
                                  'workflow_argument_name': 'trio',
                                  'unzip': '',
                                  'mount': False,
                                  'rename': ['abc.rck', 'def.rck'],
                                  'format_if_extra': ''}]

def test_FFInputFiles_create_input_files_for_wfrmeta(fake_inputfiles):
    ffinpfs = FFInputFiles(fake_inputfiles)
    wfr_inpf = ffinpfs.create_input_files_for_wfrmeta()
    assert wfr_inpf == [{'value': 'e7fc0f39-560a-4c5c-9bdb-040e43819eb7',
                         'workflow_argument_name': 'input_vcf',
                         'ordinal': 1,
                         'dimension': '0'},
                        {'value': 'e07590b8-a6cc-42ee-85b9-ed16ed0ec34e',
                         'workflow_argument_name': 'unrelated',
                         'ordinal': 1,
                         'dimension': '0',
                         'format_if_extra': 'rck.tar.index'},
                        {'value': 'b4cde603-4df9-48d2-bd06-765900b9f165',
                         'workflow_argument_name': 'trio',
                         'ordinal': 1,
                         'dimension': '0'},
                        {'value': '2c6ca4b1-62b6-4235-98c0-e4c25a9ab1ec',
                         'workflow_argument_name': 'trio',
                         'ordinal': 2,
                         'dimension': '1'}]

def test_FFInputFiles_create_input_files_for_wfrmeta2():
    input_file_list = [{
          "bucket_name": "bucket1",
          "workflow_argument_name": "input_pairs1",
          "uuid": [['a', 'b'], ['c', 'd']],
          "object_key": [['e', 'f'], ['g', 'h']]
       },
       {
          "bucket_name": "bucket1",
          "workflow_argument_name": "input_pairs2",
          "uuid": ["d2c897ec-bdb2-47ce-b1b1-845daccaa571", "d2c897ec-bdb2-47ce-b1b1-845daccaa571"],
          "object_key": ["4DNFI25JXLLI.pairs.gz", "4DNFI25JXLLI.pairs.gz"]
       }
    ]
    ffinpfs = FFInputFiles(input_file_list)
    res = ffinpfs.create_input_files_for_wfrmeta()
    assert len(res) == 6
    assert 'dimension' in res[0]
    assert res[0]['dimension'] == '0-0'
    assert 'dimension' in res[1]
    assert res[1]['dimension'] == '0-1'
    assert res[1]['ordinal'] == 2
    assert 'dimension' in res[4]
    assert res[4]['dimension'] == '0'
