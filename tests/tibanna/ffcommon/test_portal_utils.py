import copy
from tibanna_ffcommon.portal_utils import (
    TibannaSettings,
    ensure_list,
    FFInputAbstract,
    WorkflowRunMetadataAbstract,
    FourfrontStarterAbstract,
    FourfrontUpdaterAbstract,
    ProcessedFileMetadataAbstract,
)
from tibanna_ffcommon.qc import (
    QCArgumentsByTarget
)
from tibanna_ffcommon.exceptions import (
    MalFormattedFFInputException
)
import pytest
import mock
import logging


def test_tibanna():
    data = {'env': 'fourfront-webdev',
            'settings': {'1': '1'}}
    tibanna = TibannaSettings(**data)
    assert tibanna
    assert tibanna.as_dict() == data


def test_ensure_list():
    assert ensure_list(5) == [5]
    assert ensure_list('hello') == ['hello']
    assert ensure_list(['hello']) == ['hello']
    assert ensure_list({'a': 'b'}) == [{'a': 'b'}]


def test_ff_input_abstract():
    data = {'workflow_uuid': 'a',
            'config': {'log_bucket': 'b'},
            'output_bucket': 'c'}
    inp = FFInputAbstract(**data)
    assert inp.workflow_uuid == 'a'
    assert inp.config.log_bucket == 'b'
    assert 'ecr' in inp.config.awsf_image

def test_ff_input_abstract_missing_field_error2():
    data = {'workflow_uuid': 'a',
            'output_bucket': 'c'}
    with pytest.raises(MalFormattedFFInputException) as excinfo:
        FFInputAbstract(**data)
    assert "missing field in input json: config" in str(excinfo.value)


def test_ff_input_abstract_missing_field_error3():
    data = {'config': {'log_bucket': 'b'},
            'output_bucket': 'c'}
    with pytest.raises(MalFormattedFFInputException) as excinfo:
        FFInputAbstract(**data)
    assert "missing field in input json: workflow_uuid" in str(excinfo.value)


def test_workflow_run_metadata_abstract():
    data = {'workflow': 'a', 'awsem_app_name': 'b', 'app_version': 'c'}
    ff = WorkflowRunMetadataAbstract(**data)
    assert ff.workflow == 'a'
    assert ff.awsem_app_name == 'b'
    assert ff.title.startswith('b c run')


def test_workflow_run_metadata_abstract_missing_field_error1(caplog):
    data = {'awsem_app_name': 'b', 'app_version': 'c'}
    WorkflowRunMetadataAbstract(**data)
    log = caplog.get_records('call')[0]
    assert log.levelno == logging.WARNING
    assert 'workflow is missing' in log.message


def test_processed_file_metadata_abstract():
    data = {'uuid': 'a'}
    pf = ProcessedFileMetadataAbstract(**data)
    assert pf.uuid == 'a'


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


def test_mock():
    updater = FourfrontUpdaterAbstract(strict=False)
    fake_wf = {'arguments': [{},{},{},qcarginfo_bamsnap]}
    with mock.patch('tibanna_ffcommon.portal_utils.FourfrontUpdaterAbstract.get_metadata', return_value=fake_wf):
        wf = updater.workflow
    assert wf == fake_wf


def test_FourfrontUpdaterAbstract_workflow_qc_arguments(qcarginfo_bamsnap):
    updater = FourfrontUpdaterAbstract(strict=False)
    fake_wf = {'arguments': [qcarginfo_bamsnap]}
    with mock.patch('tibanna_ffcommon.portal_utils.FourfrontUpdaterAbstract.get_metadata', return_value=fake_wf):
        wf_qc_arguments = updater.workflow_arguments('Output QC file')
    qcbt = QCArgumentsByTarget(wf_qc_arguments)
    assert len(qcbt.qca_by_target) == 1
    assert 'input_vcf' in qcbt.qca_by_target
    assert len(qcbt.qca_by_target['input_vcf'].qca_list) == 1
    qc1 = qcbt.qca_by_target['input_vcf'].qca_list[0]
    assert qc1.qc_zipped
    assert qc1.qc_unzip_from_ec2
    assert qc1.qc_acl == 'private'
    assert qc1.argument_to_be_attached_to == 'input_vcf'
    assert qc1.workflow_argument_name == 'bamsnap_images'
    assert qc1.qc_type is None


def test_parse_rna_strandedness():
    report_content = '468\n0\n'
    res = FourfrontUpdaterAbstract.parse_rna_strandedness_report(report_content)
    assert len(res) == 2
    assert res[0] == 468
    assert res[1] == 0


def test_parse_fastq_first_line():
    report_content = '@HWI-ST1318:469:HV2C3BCXY:1:1101:2874:1977 1:N:0:ATGTCA'
    res = [FourfrontUpdaterAbstract.parse_fastq_first_line_report(report_content)]
    assert len(res) == 1
    assert res[0] == '@HWI-ST1318:469:HV2C3BCXY:1:1101:2874:1977 1:N:0:ATGTCA'


def test_parse_re_check():
    report_content = 'clipped-mates with RE motif: 76.54 %'
    res = FourfrontUpdaterAbstract.parse_re_check(report_content)
    assert type(res) is float
    assert res == 76.54


def test_parse_custom_fields():
    custom_pf_fields = {'somearg': {'a': 'b', 'c': 'd'},
                        'arg2': {'x': 'y'},
                        'ALL': {'e': 'f'}}
    common_fields = {'g': 'h', 'i': 'j'}
    res = FourfrontStarterAbstract.parse_custom_fields(custom_pf_fields, common_fields, "somearg")
    for fld in ['a', 'c', 'e', 'g', 'i']:
        assert fld in res
    assert 'x' not in res


def test_parse_custom_fields_overwrite():
    """testing custom_pf_fields overwriting common_fields"""
    custom_pf_fields = {'somearg': {'a': 'b', 'c': 'd'},
                        'arg2': {'x': 'y'},
                        'ALL': {'e': 'f'}}
    common_fields = {'a': 'h', 'e': 'j'}
    res = FourfrontStarterAbstract.parse_custom_fields(custom_pf_fields, common_fields, "somearg")
    for fld in ['a', 'c', 'e']:
        assert fld in res
    assert res['a'] == 'b'  # common_fields overwritten by custom_pf_fields[argname]
    assert res['e'] == 'f'  # common_fields overwritten by custom_pf_fields[All]


def test_create_wfr_qc():
    """custom_qc_fields does not apply to wfr_qc, but common_fields do"""
    updater = FourfrontUpdaterAbstract(**{'config': {'log_bucket': 'some_bucket'}}, strict=False)
    updater.jobid = 'some_jobid'
    updater.custom_qc_fields = {'a': 'b', 'c': 'd'}
    updater.common_fields = {'a': 'h', 'e': 'j'}
    updater.create_wfr_qc()
    wfr_qc_uuid = list(updater.post_items['QualityMetricWorkflowrun'].keys())[0]
    wfr_qc = updater.post_items['QualityMetricWorkflowrun'][wfr_qc_uuid]
    assert 'e' in wfr_qc and wfr_qc['e'] == 'j'  # common_fields
    assert 'c' not in wfr_qc  # custom_qc_fields does NOT get into wfr qc
    assert 'a' in wfr_qc and wfr_qc['a'] == 'h'  # common_fields NOT overwritten by custom_qc_fields
