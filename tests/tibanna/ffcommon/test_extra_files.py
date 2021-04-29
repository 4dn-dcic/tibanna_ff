from tibanna_ffcommon.extra_files import (
    ExtraFile,
    ExtraFiles,
    get_extra_file_key
)
from tibanna_ffcommon.file_format import (
    FormatExtensionMap
)
import pytest


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


def test_get_extra_file_key(fake_format_search_result):
    fe_map = FormatExtensionMap(ffe_all=fake_format_search_result)
    infile_key = 'hahaha/lalala.bwt'
    infile_format = 'bwt'
    extra_file_format = 'sa'
    extra_file_key = get_extra_file_key(infile_format, infile_key, extra_file_format, fe_map)
    assert extra_file_key == 'hahaha/lalala.sa'

def test_ExtraFile():
    exf = ExtraFile(file_format='bai', status='uploaded')
    exf.as_dict() == {'file_format': 'bai', 'status': 'uploaded'}

def test_ExtraFile2():
    exf = ExtraFile(file_format='/file-formats/bai/', status='uploaded')
    exf.as_dict() == {'file_format': 'bai', 'status': 'uploaded'}

def test_ExtraFiles():
    extrafiles = ExtraFiles([{'file_format': 'sa', 'status': 'uploaded'},
                             {'file_format': 'ann', 'status': 'uploaded'}])
    assert extrafiles.n == 2
    assert extrafiles.file_formats == ['sa', 'ann']
    assert extrafiles.check_unique_formats() is True
    assert extrafiles.extra_files[0].as_dict() == {'file_format': 'sa',
                                                   'status': 'uploaded'}
    exf = extrafiles.select('sa')
    exf.status = 'to be uploaded by workflow'
    assert extrafiles.as_dict() == [{'file_format': 'sa', 'status': 'to be uploaded by workflow'},
                                    {'file_format': 'ann', 'status': 'uploaded'}]
    extrafiles.add_extra_file(file_format='pac', status='to be uploaded by workflow')
    assert extrafiles.n == 3
    assert extrafiles.as_dict() == [{'file_format': 'sa', 'status': 'to be uploaded by workflow'},
                                    {'file_format': 'ann', 'status': 'uploaded'},
                                    {'file_format': 'pac', 'status': 'to be uploaded by workflow'}]
    with pytest.raises(Exception) as ex_info:
        extrafiles.add_extra_file(file_format='pac', status='to be uploaded by workflow')
    assert 'Cannot add a new extra file. File format pac exists' in str(ex_info.value)

def test_ExtraFiles_check_unique_format_error():
    with pytest.raises(Exception) as ex_info:
        extrafiles = ExtraFiles([{'file_format': 'sa', 'status': 'uploaded'},
                                 {'file_format': 'sa', 'status': 'uploading'}])
    assert "Redundant formats are not allowed" in str(ex_info.value)
