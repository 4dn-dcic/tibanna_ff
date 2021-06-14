from tibanna_ffcommon.qc import (
    QCArgument,
    QCArgumentsByTarget,
    QCArgumentsPerTarget,
    QCDataParser
)
import pytest
import copy


@pytest.fixture
def qcarginfo_fastqc():
    return {
        "argument_type": "Output QC file",
        "workflow_argument_name": "report_zip",
        "argument_to_be_attached_to": "input_fastq",
        "qc_zipped": True,
        "qc_html": True,
        "qc_json": False,
        "qc_table": True,
        "qc_zipped_html": "fastqc_report.html",
        "qc_zipped_tables": ["summary.txt", "fastqc_data.txt"],
        "qc_type": "quality_metric_fastqc"
    }

@pytest.fixture
def qcarginfo_bamsnap():
    return {
        "argument_type": "Output QC file",
        "workflow_argument_name": "bamsnap_images",
        "argument_to_be_attached_to": "input_vcf",
        "qc_zipped": True,
        "qc_unzip_from_ec2": True,
        "qc_acl": "private"
    }

@pytest.fixture
def fake_qcarginfo1():
    return {
        "argument_type": "Output QC file",
        "workflow_argument_name": "qc1",
        "argument_to_be_attached_to": "arg1",
        "qc_type": "quality_metric_someqc",
        "qc_json": True
    }

@pytest.fixture
def fake_qcarginfo2():
    return {
        "argument_type": "Output QC file",
        "workflow_argument_name": "qc2",
        "argument_to_be_attached_to": "arg1",
        "qc_type": "quality_metric_someqc",
        "qc_html": True
    }

@pytest.fixture
def fake_qcarginfo3():
    return {
        "argument_type": "Output QC file",
        "workflow_argument_name": "qc3",
        "argument_to_be_attached_to": "arg1",
        "qc_type": "quality_metric_someotherqc",
        "qc_table": True
    }

@pytest.fixture
def fake_qcarginfo4():
    return {
        "argument_type": "Output QC file",
        "workflow_argument_name": "qc4",
        "argument_to_be_attached_to": "arg1",
        "qc_zipped_html": True
    }

@pytest.fixture
def fake_qcschemainfo():
    return {
        "fake_schema": {"match_test": {'type': 'number'}},
        "name": "match_test",
        "test_val_1": 5,
        "test_val_2": 2.04
    }


def test_QCArgumentsPerTarget(fake_qcarginfo1, fake_qcarginfo2, fake_qcarginfo3):
    qca_per_target = QCArgumentsPerTarget([QCArgument(**fake_qcarginfo1),
                                           QCArgument(**fake_qcarginfo2),
                                           QCArgument(**fake_qcarginfo3)])
    assert len(qca_per_target.qca_list) == 3
    assert qca_per_target.target_argname == 'arg1'
    assert qca_per_target.qca_list[0].workflow_argument_name == 'qc1'
    assert qca_per_target.qca_list[1].workflow_argument_name == 'qc2'
    assert qca_per_target.qca_list[2].workflow_argument_name == 'qc3'
    assert qca_per_target.qca_list[0].qc_json is True
    assert qca_per_target.qca_list[1].qc_html is True
    assert qca_per_target.qca_list[2].qc_table is True
    assert qca_per_target.qc_types == set(["quality_metric_someqc", "quality_metric_someotherqc"])
    assert qca_per_target.qc_types_no_none == set(["quality_metric_someqc", "quality_metric_someotherqc"])
    assert qca_per_target.qca_list_by_type == {'quality_metric_someqc': [qca_per_target.qca_list[0],
                                                                         qca_per_target.qca_list[1]],
                                               'quality_metric_someotherqc': [qca_per_target.qca_list[2]]}

def test_QCArgumentsPerTarget2(fake_qcarginfo3, fake_qcarginfo4):
    qca_per_target = QCArgumentsPerTarget([QCArgument(**fake_qcarginfo3),
                                           QCArgument(**fake_qcarginfo4)])
    assert len(qca_per_target.qca_list) == 2
    assert qca_per_target.target_argname == 'arg1'
    assert qca_per_target.qca_list[0].workflow_argument_name == 'qc3'
    assert qca_per_target.qca_list[1].workflow_argument_name == 'qc4'
    assert qca_per_target.qca_list[0].qc_table is True
    assert qca_per_target.qca_list[1].qc_zipped_html is True
    assert qca_per_target.qc_types == set(["quality_metric_someotherqc", None])
    assert qca_per_target.qc_types_no_none == set(["quality_metric_someotherqc"])
    assert qca_per_target.qca_list_by_type == {'quality_metric_someotherqc': [qca_per_target.qca_list[0]],
                                               None: [qca_per_target.qca_list[1]]}


def test_QCArgumentsByTarget(fake_qcarginfo1, fake_qcarginfo2):
    qca_by_target = QCArgumentsByTarget([fake_qcarginfo1, fake_qcarginfo2])
    assert len(qca_by_target.qca_by_target) == 1
    assert 'arg1' in qca_by_target.qca_by_target
    assert len(qca_by_target.qca_by_target['arg1'].qca_list) == 2
    assert qca_by_target.qca_by_target['arg1'].qca_list[0].workflow_argument_name == 'qc1'
    assert qca_by_target.qca_by_target['arg1'].qca_list[0].qc_json is True
    assert qca_by_target.qca_by_target['arg1'].qca_list[1].workflow_argument_name == 'qc2'
    assert qca_by_target.qca_by_target['arg1'].qca_list[1].qc_html is True


def test_QCArgument_bamsnap(qcarginfo_bamsnap):
    qc = QCArgument(**qcarginfo_bamsnap)
    assert qc.qc_zipped
    assert qc.qc_unzip_from_ec2
    assert qc.qc_acl == 'private'
    assert qc.argument_to_be_attached_to == 'input_vcf'
    assert qc.workflow_argument_name == 'bamsnap_images'
    assert qc.qc_type is None

def test_QCArgument(qcarginfo_fastqc):
    qc = QCArgument(**qcarginfo_fastqc)
    assert qc.qc_zipped
    assert qc.qc_html
    assert qc.qc_table
    assert qc.qc_type == "quality_metric_fastqc"

def test_wrong_QCArgument(qcarginfo_fastqc):
    qcarginfo = copy.deepcopy(qcarginfo_fastqc)
    qcarginfo['argument_type'] = 'Output processed file'
    with pytest.raises(Exception) as exec_info:
        QCArgument(**qcarginfo)
    assert exec_info
    assert 'QC Argument must be an Output QC file' in str(exec_info.value)

def test_match_field_int(fake_qcschemainfo):
    qc_dict = fake_qcschemainfo
    fake_qc = QCDataParser(qc_dict.get('fake_schema'))

    assert fake_qc.match_field_type(qc_dict.get('name'),qc_dict.get('test_val_1'))
    assert fake_qc.match_field_type(qc_dict.get('name'),qc_dict.get('test_val_2'))

