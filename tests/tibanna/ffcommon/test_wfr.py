from tibanna_ffcommon.wfr import (
    InputFilesForWFRMeta,
    InputFileForWFRMeta,
    create_ordinal,
    aslist
)
import pytest


@pytest.fixture
def fake_wfrmeta_input_dict():
    return {'workflow_argument_name': 'somearg',
            'value': 'someuuid',
            'ordinal': 1,
            'dimension': '0',
            'format_if_extra': 'bai'}

@pytest.fixture
def fake_wfrmeta_input_dict2():
    return {'workflow_argument_name': 'somearg',
            'value': 'someuuid2',
            'ordinal': 2,
            'dimension': '1',
            'format_if_extra': 'bai'}


def test_create_ordinal():
    assert create_ordinal('a') == 1

def test_create_ordinal_list():
    assert create_ordinal(['a', 'b', 'c']) == [1, 2, 3]

def test_aslist():
    assert aslist('a') == ['a']
    assert aslist(['a']) == ['a']
    assert aslist(['a', 'b']) == ['a', 'b']

def test_InputFileForWFRMeta(fake_wfrmeta_input_dict):
    ipfw = InputFileForWFRMeta(**fake_wfrmeta_input_dict)
    assert ipfw.workflow_argument_name == 'somearg'
    assert ipfw.value == 'someuuid'
    assert ipfw.ordinal == 1
    assert ipfw.dimension == '0'
    assert ipfw.format_if_extra == 'bai'
    assert ipfw.as_dict() == fake_wfrmeta_input_dict


def test_InputFilesForWFRMeta(fake_wfrmeta_input_dict,
                              fake_wfrmeta_input_dict2):
    ipfws = InputFilesForWFRMeta()
    assert ipfws
    assert ipfws.input_files == []
    ipfws.append(InputFileForWFRMeta(**fake_wfrmeta_input_dict))
    assert ipfws.input_files[0].as_dict() == fake_wfrmeta_input_dict
    assert ipfws.as_dict() == [fake_wfrmeta_input_dict]
    ipfws.append(InputFileForWFRMeta(**fake_wfrmeta_input_dict2))
    assert ipfws.input_files[1].as_dict() == fake_wfrmeta_input_dict2
    assert ipfws.as_dict() == [fake_wfrmeta_input_dict,
                               fake_wfrmeta_input_dict2]


def test_InputFilesForWFRMeta_add_input_file():
    ipfws = InputFilesForWFRMeta()

    # add a singleton
    ipfws.add_input_files('u1', 'arg1')
    expected = {'value': 'u1', 'workflow_argument_name': 'arg1',
                'ordinal': 1, 'dimension': '0'}
    assert ipfws.input_files[0].as_dict() == expected

    # add a 1d list
    ipfws.add_input_files(['u2', 'u3'], 'arg2')
    expected2 = {'value': 'u2', 'workflow_argument_name': 'arg2',
                 'ordinal': 1, 'dimension': '0'}
    expected3 = {'value': 'u3', 'workflow_argument_name': 'arg2',
                 'ordinal': 2, 'dimension': '1'}
    assert ipfws.input_files[1].as_dict() == expected2
    assert ipfws.input_files[2].as_dict() == expected3
    # add a 2d list
    ipfws.add_input_files([['u4', 'u5'],['u6','u7']], 'arg3', 'bai')
    expected4 = {'value': 'u4', 'workflow_argument_name': 'arg3',
                 'ordinal': 1, 'dimension': '0-0', 'format_if_extra': 'bai'}
    expected5 = {'value': 'u5', 'workflow_argument_name': 'arg3',
                 'ordinal': 2, 'dimension': '0-1', 'format_if_extra': 'bai'}
    expected6 = {'value': 'u6', 'workflow_argument_name': 'arg3',
                 'ordinal': 3, 'dimension': '1-0', 'format_if_extra': 'bai'}
    expected7 = {'value': 'u7', 'workflow_argument_name': 'arg3',
                 'ordinal': 4, 'dimension': '1-1', 'format_if_extra': 'bai'}
    assert ipfws.input_files[3].as_dict() == expected4
    assert ipfws.input_files[4].as_dict() == expected5
    assert ipfws.input_files[5].as_dict() == expected6
    assert ipfws.input_files[6].as_dict() == expected7
    # testing arg names
    assert set(ipfws.arg_names) == set(['arg1', 'arg2', 'arg3'])
    # error trying to enter the same arg name again
    with pytest.raises(Exception) as ex_info:
        ipfws.add_input_files('u8', 'arg1')
    assert 'Arg arg1 already exists in the list' in str(ex_info.value)
