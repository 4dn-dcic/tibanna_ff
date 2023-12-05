import pytest
import copy

from tibanna_ffcommon.vars import GENERIC_QC_FILE, INPUT_FILE
from tibanna_ffcommon.generic_qc_utils import (
    filter_workflow_args_by_property,
    check_qc_workflow_args,
    validate_qc_ruleset,
    evaluate_qc_threshold,
    evaluate_qc_ruleset,
    QC_threshold,
    QC_json,
    QC_ruleset,
    PASS,
    WARN,
    FAIL,
)
from tibanna_ffcommon.exceptions import GenericQcException

INPUT_1 = {
    "argument_format": "bam",
    "argument_type": INPUT_FILE,
    "workflow_argument_name": "input_1",
}

QC_JSON_INPUT_1 = {
    "argument_format": "json",
    "argument_to_be_attached_to": "input_1",
    "argument_type": GENERIC_QC_FILE,
    "qc_json": True,
    "qc_zipped": False,
    "workflow_argument_name": "qc_input_json_1",
}

QC_ZIP_INPUT_1 = {
    "argument_format": "zip",
    "argument_to_be_attached_to": "input_1",
    "argument_type": GENERIC_QC_FILE,
    "qc_json": False,
    "qc_zipped": True,
    "workflow_argument_name": "qc_input_zip_1",
}

QC_JSON_INPUT_2 = {
    "argument_format": "json",
    "argument_to_be_attached_to": "input_2",
    "argument_type": GENERIC_QC_FILE,
    "qc_json": True,
    "qc_zipped": False,
    "workflow_argument_name": "qc_input_json_2",
}

QC_JSON_INPUT_3 = {
    "argument_format": "json",
    "argument_type": GENERIC_QC_FILE,
    "qc_json": True,
    "qc_zipped": False,
    "workflow_argument_name": "qc_input_json_3",
}

QC_JSON_INPUT_4 = {
    "argument_format": "json",
    "argument_type": GENERIC_QC_FILE,
    "argument_to_be_attached_to": "input_1",
    "qc_json": False,
    "qc_zipped": False,
    "workflow_argument_name": "qc_input_json_4",
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
    check_qc_workflow_args(wf_input_arg, wf_qc_arg_1)  # Asserts that there is no error


def test_check_qc_workflow_args_2(wf_input_arg, wf_qc_arg_2):
    with pytest.raises(
        GenericQcException, match="does not have argument_to_be_attached_to specified"
    ):
        check_qc_workflow_args(wf_input_arg, wf_qc_arg_2)


def test_check_qc_workflow_args_3(wf_input_arg, wf_qc_arg_3):
    with pytest.raises(
        GenericQcException,
        match="qc_input_json_2's argument_to_be_attached_to does not exist",
    ):
        check_qc_workflow_args(wf_input_arg, wf_qc_arg_3)


def test_check_qc_workflow_args_4(wf_input_arg, wf_qc_arg_4):
    with pytest.raises(
        GenericQcException, match="Exactly one of qc_json or qc_zipped must be true."
    ):
        check_qc_workflow_args(wf_input_arg, wf_qc_arg_4)


def test_check_qc_workflow_args_5(wf_input_arg, wf_qc_arg_5):
    with pytest.raises(
        GenericQcException, match="There is no QC JSON associated with input"
    ):
        check_qc_workflow_args(wf_input_arg, wf_qc_arg_5)


def test_check_qc_workflow_args_6(wf_input_arg, wf_qc_arg_6):
    with pytest.raises(
        GenericQcException, match="There are 2 Generic QC files associated with input"
    ):
        check_qc_workflow_args(wf_input_arg, wf_qc_arg_6)


def test_check_qc_workflow_args_7(wf_input_arg, wf_qc_arg_7):
    with pytest.raises(
        GenericQcException, match="There are more than 2 Generic QC files for input"
    ):
        check_qc_workflow_args(wf_input_arg, wf_qc_arg_7)


def test_filter_workflow_args_by_property(wf_arg_set_1):
    inputs = filter_workflow_args_by_property(wf_arg_set_1, "argument_type", INPUT_FILE)
    assert len(inputs) == 1
    assert inputs[0]["workflow_argument_name"] == "input_1"

    qcs = filter_workflow_args_by_property(
        wf_arg_set_1, "argument_type", GENERIC_QC_FILE
    )
    assert len(qcs) == 2

    qc_json = filter_workflow_args_by_property(qcs, "qc_json", True)
    assert len(qc_json) == 1
    assert qc_json[0]["workflow_argument_name"] == "qc_input_json_1"

    qc_zip = filter_workflow_args_by_property(qcs, "qc_zipped", True)
    assert len(qc_zip) == 1
    assert qc_zip[0]["workflow_argument_name"] == "qc_input_zip_1"


@pytest.fixture
def valid_ruleset_1a():
    return {
            "qc_thresholds": [
                {
                    "id": "c1",
                    "metric": "Coverage",
                    "operator": ">=",
                    "pass_target": 100,
                    "warn_target": 80,
                    "use_as_qc_flag": True,
                },
                {
                    "id": "rl",
                    "metric": "read_length",
                    "operator": ">",
                    "pass_target": 120,
                    "warn_target": 80,
                    "use_as_qc_flag": True,
                },
                {
                    "id": "ts",
                    "metric": "Total Sequences [Samtools]",
                    "operator": ">",
                    "pass_target": 547993296,
                    "warn_target": 527993296,
                },
                {
                    "id": "test0",
                    "metric": "test0",
                    "operator": "<=",
                    "pass_target": 10,
                    "warn_target": 10,
                },
                {
                    "id": "test1",
                    "metric": "test0",
                    "operator": "<",
                    "pass_target": 10,
                    "warn_target": 10,
                },
                {
                    "id": "test2",
                    "metric": "test0",
                    "operator": "==",
                    "pass_target": 10,
                    "warn_target": 10,
                },
                {
                    "id": "test3",
                    "metric": "test0",
                    "operator": "<>",  # invalid
                    "pass_target": 10,
                    "warn_target": 10,
                },
            ],
            "overall_quality_status_rule": "{c1} and {ts}"
        }


@pytest.fixture
def valid_ruleset_1b():
    return {
            "qc_thresholds": [
                {
                    "id": "c1",
                    "metric": "coverage",
                    "operator": ">=",
                    "pass_target": 150,
                    "warn_target": 80,
                    "use_as_qc_flag": True,
                },
            ],
            "overall_quality_status_rule": "{c1}"
        }


@pytest.fixture
def valid_ruleset_2a():
    return {
            "qc_thresholds": [
                {
                    "id": "c1",
                    "metric": "Coverage",
                    "operator": ">=",
                    "pass_target": 100,
                    "warn_target": 80,
                    "use_as_qc_flag": True,
                },
                {
                    "id": "ts",
                    "metric": "Total Sequences [Samtools]",
                    "operator": ">",
                    "pass_target": 527993296,
                    "warn_target": 527993296,
                },
            ],
            "overall_quality_status_rule": "{c1} and {ts}"
        }


@pytest.fixture
def valid_ruleset_2b():
    return {
            "qc_thresholds": [
                {
                    "id": "c1",
                    "metric": "Coverage",
                    "operator": ">=",
                    "pass_target": 150,
                    "warn_target": 80,
                    "use_as_qc_flag": True,
                },
            ],
            "overall_quality_status_rule": "{c1}"
        }


@pytest.fixture
def valid_ruleset_2c():
    return {
            "qc_thresholds": [
                {
                    "id": "c1",
                    "metric": "Coverage",
                    "operator": ">=",
                    "pass_target": 150,
                    "warn_target": 80,
                    "use_as_qc_flag": True,
                },
            ],
            "overall_quality_status_rule": "{c1} and {ts}",  # invalid since ts not define
        }



@pytest.fixture
def invalid_ruleset():
    return {
            "qc_thresholds": [
                {
                    "id": "c1",
                    "metric": "coverage",
                    "operator": ">=",
                    "pass_target": 100,  # warn_target missing
                },
            ],
            "overall_quality_status_rule": "{c1}",
            "applies_to": ["input_1"],
        }


@pytest.fixture
def qc_json():
    return {
        "name": "BAM Quality Metrics",
        "qc_values": [
            {
                "key": "Total Sequences [Samtools]",
                "tooltip": "Total number of reads in a file, excluding supplementary and secondary reads",
                "value": 537993296,
            },
            {
                "key": "Coverage",
                "tooltip": "Average coverage",
                "value": 130.5,
            },
            {
                "key": "test0",
                "value": 10,
            },
        ],
    }


def test_validate_qc_ruleset_1a(valid_ruleset_1a):
    validate_qc_ruleset(valid_ruleset_1a)  # Asserts that there is no error

def test_validate_qc_ruleset_1b(valid_ruleset_1b):
    validate_qc_ruleset(valid_ruleset_1b)  # Asserts that there is no error


def test_validate_qc_ruleset_2(invalid_ruleset):
    with pytest.raises(
        GenericQcException, match="The supplied QC ruleset has the wrong format"
    ):
        validate_qc_ruleset(invalid_ruleset)


def test_evaluate_qc_threshold(valid_ruleset_1a, qc_json):
    qc_json_model = QC_json(**qc_json)
    ruleset = QC_ruleset(**valid_ruleset_1a)
    qc_thresholds = ruleset.qc_thresholds
    qc_threshold = next((item for item in qc_thresholds if item.id == "c1"))
    result = evaluate_qc_threshold(qc_threshold, qc_json_model)
    assert result == "pass"
    assert qc_json_model.qc_values[1].flag == "pass"

    qc_threshold.pass_target = 150
    result = evaluate_qc_threshold(qc_threshold, qc_json_model)
    assert result == "warn"
    assert qc_json_model.qc_values[1].flag == "warn"

    qc_threshold.warn_target = 150
    result = evaluate_qc_threshold(qc_threshold, qc_json_model)
    assert result == "fail"
    assert qc_json_model.qc_values[1].flag == "fail"


def test_evaluate_qc_threshold_2(valid_ruleset_1b, qc_json):
    qc_json_model = QC_json(**qc_json)
    ruleset = QC_ruleset(**valid_ruleset_1b)
    qc_thresholds = ruleset.qc_thresholds
    qc_threshold = next((item for item in qc_thresholds if item.id == "c1"))
    with pytest.raises(
        GenericQcException, match="QC metric 'coverage' in ruleset not found in QC json"
    ):
        evaluate_qc_threshold(qc_threshold, qc_json_model)


def test_evaluate_qc_threshold_3(valid_ruleset_1a, qc_json):
    qc_json_model = QC_json(**qc_json)
    ruleset = QC_ruleset(**valid_ruleset_1a)
    qc_thresholds = ruleset.qc_thresholds
    qc_threshold = next((item for item in qc_thresholds if item.id == "test0"))
    result = evaluate_qc_threshold(qc_threshold, qc_json_model)
    assert result == "pass"

    qc_threshold = next((item for item in qc_thresholds if item.id == "test1"))
    result = evaluate_qc_threshold(qc_threshold, qc_json_model)
    assert result == "fail"

    qc_threshold = next((item for item in qc_thresholds if item.id == "test2"))
    result = evaluate_qc_threshold(qc_threshold, qc_json_model)
    assert result == "pass"

    with pytest.raises(
        GenericQcException, match="The ruleset contains an unsupported operator"
    ):
        qc_threshold = next((item for item in qc_thresholds if item.id == "test3"))
        result = evaluate_qc_threshold(qc_threshold, qc_json_model)


def test_evaluate_qc_ruleset(valid_ruleset_1a, qc_json):
    ruleset = QC_ruleset(**valid_ruleset_1a)
    with pytest.raises(
        GenericQcException,
        match="QC metric 'read_length' in ruleset not found in QC json",
    ):
        evaluate_qc_ruleset(qc_json, ruleset)


def test_evaluate_qc_ruleset_2a(valid_ruleset_2a, qc_json):
    ruleset = QC_ruleset(**valid_ruleset_2a)

    qc_json_new, overall_quality_status = evaluate_qc_ruleset(
        qc_json, ruleset
    )
    assert overall_quality_status == PASS
    assert qc_json_new["qc_values"][1]["flag"] == PASS

    ruleset.qc_thresholds[1].pass_target = 547993296
    qc_json_new, overall_quality_status = evaluate_qc_ruleset(
        qc_json, ruleset
    )
    assert overall_quality_status == WARN
    assert qc_json_new["qc_values"][1]["flag"] == PASS

   
def test_evaluate_qc_ruleset_2b(valid_ruleset_2b, qc_json):
    ruleset = QC_ruleset(**valid_ruleset_2b)

    qc_json_new, overall_quality_status = evaluate_qc_ruleset(
        qc_json, ruleset
    )
    assert overall_quality_status == WARN
    assert qc_json_new["qc_values"][1]["flag"] == WARN


def test_evaluate_qc_ruleset_2c(valid_ruleset_2c, qc_json):
    ruleset = QC_ruleset(**valid_ruleset_2c)

    with pytest.raises(
        GenericQcException,
        match="The overall_quality_status_rule contains metric IDs that are not defined in the rulset.",
    ):
        evaluate_qc_ruleset(qc_json, ruleset)

