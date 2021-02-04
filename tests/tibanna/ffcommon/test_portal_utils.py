import copy
from tibanna_ffcommon.portal_utils import (
    TibannaSettings,
    ensure_list,
    FFInputAbstract,
    WorkflowRunMetadataAbstract,
    FourfrontStarterAbstract,
    FourfrontUpdaterAbstract,
    ProcessedFileMetadataAbstract,
    QCArgumentInfo,
)
from tibanna_ffcommon.exceptions import (
    MalFormattedFFInputException
)
import pytest
import mock


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


def test_ff_input_abstract_missing_field_error2():
    data = {'workflow_uuid': 'a',
            'output_bucket': 'c'}
    with pytest.raises(MalFormattedFFInputException) as excinfo:
        FFInputAbstract(**data)
    assert "missing field in input json: config" in str(excinfo)


def test_ff_input_abstract_missing_field_error3():
    data = {'config': {'log_bucket': 'b'},
            'output_bucket': 'c'}
    with pytest.raises(MalFormattedFFInputException) as excinfo:
        FFInputAbstract(**data)
    assert "missing field in input json: workflow_uuid" in str(excinfo)


def test_workflow_run_metadata_abstract():
    data = {'workflow': 'a', 'awsem_app_name': 'b', 'app_version': 'c'}
    ff = WorkflowRunMetadataAbstract(**data)
    assert ff.workflow == 'a'
    assert ff.awsem_app_name == 'b'
    assert ff.title.startswith('b c run')


def test_workflow_run_metadata_abstract_missing_field_error1():
    data = {'awsem_app_name': 'b', 'app_version': 'c'}
    with pytest.raises(Exception) as excinfo:
        WorkflowRunMetadataAbstract(**data)
    assert 'missing' in str(excinfo)


def test_processed_file_metadata_abstract():
    data = {'uuid': 'a'}
    pf = ProcessedFileMetadataAbstract(**data)
    assert pf.uuid == 'a'


def test_create_ff_input_files():
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
    starter = FourfrontStarterAbstract(input_files=input_file_list,
                                       workflow_uuid='a',
                                       config={'log_bucket': 'b'},
                                       output_bucket='c')
    res = starter.create_ff_input_files()
    assert len(res) == 6
    assert 'dimension' in res[0]
    assert res[0]['dimension'] == '0-0'
    assert 'dimension' in res[1]
    assert res[1]['dimension'] == '0-1'
    assert res[1]['ordinal'] == 2
    assert 'dimension' in res[4]
    assert res[4]['dimension'] == '0'


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


def test_QCArgumentInfo_bamsnap(qcarginfo_bamsnap):
    qc = QCArgumentInfo(**qcarginfo_bamsnap)
    assert qc.qc_zipped
    assert qc.qc_unzip_from_ec2
    assert qc.qc_acl == 'private'
    assert qc.argument_to_be_attached_to == 'input_vcf'
    assert qc.workflow_argument_name == 'bamsnap_images'
    assert qc.qc_type is None


def test_FourfrontUpdaterAbstract_workflow_qc_arguments(qcarginfo_bamsnap):
    updater = FourfrontUpdaterAbstract()


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
        qc = updater.workflow_qc_arguments
    assert len(qc) == 1
    assert 'input_vcf' in qc
    assert len(qc['input_vcf']) == 1
    qc1 = qc['input_vcf'][0]
    assert qc1.qc_zipped
    assert qc1.qc_unzip_from_ec2
    assert qc1.qc_acl == 'private'
    assert qc1.argument_to_be_attached_to == 'input_vcf'
    assert qc1.workflow_argument_name == 'bamsnap_images'
    assert qc1.qc_type is None


def test_QCArgumentInfo(qcarginfo_fastqc):
    qc = QCArgumentInfo(**qcarginfo_fastqc)
    assert qc.qc_zipped
    assert qc.qc_html
    assert qc.qc_table
    assert qc.qc_type == "quality_metric_fastqc"


def test_wrong_QCArgumentInfo(qcarginfo_fastqc):
    qcarginfo = copy.deepcopy(qcarginfo_fastqc)
    qcarginfo['argument_type'] = 'Output processed file'
    with pytest.raises(Exception) as exec_info:
        QCArgumentInfo(**qcarginfo)
    assert exec_info
    assert 'QCArgument it not Output QC file' in str(exec_info)


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
