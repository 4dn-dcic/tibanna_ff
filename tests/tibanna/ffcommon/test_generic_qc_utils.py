
import pytest
import copy

from tibanna_ffcommon.vars import (
    GENERIC_QC_FILE,
    INPUT_FILE
)
from tibanna_ffcommon.generic_qc_utils import (
    filter_workflow_args_by_property,
    check_qc_workflow_args
)
from tibanna_ffcommon.exceptions import (
    GenericQcException
)

INPUT_1 = {
    "argument_format": "bam",
    "argument_type": INPUT_FILE,
    "workflow_argument_name": "input_1"
}

QC_JSON_INPUT_1 = {
    "argument_format": "json",
    "argument_to_be_attached_to": "input_1",
    "argument_type": GENERIC_QC_FILE,
    "qc_json": True,
    "qc_zipped": False,
    "workflow_argument_name": "qc_input_json_1"
}

QC_ZIP_INPUT_1 = {
    "argument_format": "zip",
    "argument_to_be_attached_to": "input_1",
    "argument_type": GENERIC_QC_FILE,
    "qc_json": False,
    "qc_zipped": True,
    "workflow_argument_name": "qc_input_zip_1"
}

QC_JSON_INPUT_2 = {
    "argument_format": "json",
    "argument_to_be_attached_to": "input_2",
    "argument_type": GENERIC_QC_FILE,
    "qc_json": True,
    "qc_zipped": False,
    "workflow_argument_name": "qc_input_json_2"
}

QC_JSON_INPUT_3 = {
    "argument_format": "json",
    "argument_type": GENERIC_QC_FILE,
    "qc_json": True,
    "qc_zipped": False,
    "workflow_argument_name": "qc_input_json_3"
}

QC_JSON_INPUT_4 = {
    "argument_format": "json",
    "argument_type": GENERIC_QC_FILE,
    "argument_to_be_attached_to": "input_1",
    "qc_json": False,
    "qc_zipped": False,
    "workflow_argument_name": "qc_input_json_4"
}

@pytest.fixture
def wf_arg_set_1():
    return [INPUT_1, QC_JSON_INPUT_1, QC_ZIP_INPUT_1]

@pytest.fixture
def wf_input_arg():
    return [INPUT_1]

@pytest.fixture
def wf_qc_arg_1():
    return [QC_JSON_INPUT_1, QC_ZIP_INPUT_1]

@pytest.fixture
def wf_qc_arg_2():
    return [QC_JSON_INPUT_3]

@pytest.fixture
def wf_qc_arg_3():
    return [QC_JSON_INPUT_2]

@pytest.fixture
def wf_qc_arg_4():
    return [QC_JSON_INPUT_4]

@pytest.fixture
def wf_qc_arg_5():
    return [QC_ZIP_INPUT_1]

@pytest.fixture
def wf_qc_arg_6():
    return [QC_JSON_INPUT_1, QC_JSON_INPUT_1]

@pytest.fixture
def wf_qc_arg_7():
    return [QC_JSON_INPUT_1, QC_ZIP_INPUT_1, QC_JSON_INPUT_1]


def test_check_qc_workflow_args_1(wf_input_arg, wf_qc_arg_1):
    check_qc_workflow_args(wf_input_arg, wf_qc_arg_1) # Asserts that there is no error

def test_check_qc_workflow_args_2(wf_input_arg, wf_qc_arg_2):
    with pytest.raises(GenericQcException, match="does not have argument_to_be_attached_to specified"):
       check_qc_workflow_args(wf_input_arg, wf_qc_arg_2) 

def test_check_qc_workflow_args_3(wf_input_arg, wf_qc_arg_3):
    with pytest.raises(GenericQcException, match="qc_input_json_2's argument_to_be_attached_to does not exist"):
       check_qc_workflow_args(wf_input_arg, wf_qc_arg_3) 

def test_check_qc_workflow_args_4(wf_input_arg, wf_qc_arg_4):
    with pytest.raises(GenericQcException, match="Exactly one of qc_json or qc_zipped must be true."):
       check_qc_workflow_args(wf_input_arg, wf_qc_arg_4) 

def test_check_qc_workflow_args_5(wf_input_arg, wf_qc_arg_5):
    with pytest.raises(GenericQcException, match="There is no QC JSON associated with input"):
       check_qc_workflow_args(wf_input_arg, wf_qc_arg_5) 

def test_check_qc_workflow_args_6(wf_input_arg, wf_qc_arg_6):
    with pytest.raises(GenericQcException, match="There are 2 Generic QC files associated with input"):
       check_qc_workflow_args(wf_input_arg, wf_qc_arg_6) 

def test_check_qc_workflow_args_7(wf_input_arg, wf_qc_arg_7):
    with pytest.raises(GenericQcException, match="There are more than 2 Generic QC files for input"):
       check_qc_workflow_args(wf_input_arg, wf_qc_arg_7) 

def test_filter_workflow_args_by_property(wf_arg_set_1):

    inputs = filter_workflow_args_by_property(wf_arg_set_1, "argument_type", INPUT_FILE)
    assert len(inputs) == 1
    assert inputs[0]["workflow_argument_name"] == "input_1"

    qcs = filter_workflow_args_by_property(wf_arg_set_1, "argument_type", GENERIC_QC_FILE)
    assert len(qcs) == 2

    qc_json = filter_workflow_args_by_property(qcs, "qc_json", True)
    assert len(qc_json) == 1
    assert qc_json[0]["workflow_argument_name"] == "qc_input_json_1"

    qc_zip = filter_workflow_args_by_property(qcs, "qc_zipped", True)
    assert len(qc_zip) == 1
    assert qc_zip[0]["workflow_argument_name"] == "qc_input_zip_1"
    