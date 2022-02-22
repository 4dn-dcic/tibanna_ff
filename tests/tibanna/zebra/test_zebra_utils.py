from tibanna_cgap.vars import (
    DEFAULT_PROJECT,
    DEFAULT_INSTITUTION
)
from tibanna_ffcommon.portal_utils import (
    TibannaSettings,
    FormatExtensionMap,
)
from tibanna_cgap.zebra_utils import (
    FourfrontStarter,
    FourfrontUpdater,
    ZebraInput
)
from tests.tibanna.zebra.conftest import valid_env, logger
import mock


# These are integrated tests intended to work with legacy environments.
# These need to be refactored to use cgap-wolf - Will Feb 22 2022
pytestmark = ['pytest.mark.skip']


@valid_env
def test_tibanna():
    data = {'env': 'fourfront-cgap',
            'settings': {'1': '1'}}
    tibanna = TibannaSettings(**data)
    assert tibanna
    assert tibanna.as_dict() == data


@valid_env
def test_format_extension_map():
    data = {'env': 'fourfront-cgap',
            'settings': {'1': '1'}}
    tibanna = TibannaSettings(**data)
    fe_map = FormatExtensionMap(tibanna.ff_keys)
    assert(fe_map)
    assert 'bwt' in fe_map.fe_dict.keys()


def test_array_uuid():
    """test for object_key and bucket name auto-filled for an array uuid"""
    # This test requires the following files to have metadata (not necessarily the physical file)
    # eda72adf-3999-4ef4-adf7-58a64a9044d8, eda9be6d-0ecd-4bad-bd07-6e1a7efc98be
    # with accessions GAPFIQNHLO6D and GAPFIZ25WPXE
    # on cgapwolf
    # the format and status of these file items should be rck_gz and uploaded as well.
    input_file_list = [
       {
          "workflow_argument_name": "input_rcks",
          "uuid": ["eda72adf-3999-4ef4-adf7-58a64a9044d8", "eda9be6d-0ecd-4bad-bd07-6e1a7efc98be"]
       }
    ]
    _tibanna = {'env': 'fourfront-cgapwolf',
                'settings': {'1': '1'}}
    inp = ZebraInput(workflow_uuid='a',
                     config={'log_bucket': 'b'},
                     output_bucket='c',
                     input_files=input_file_list,
                     _tibanna=_tibanna)
    inputfiles = inp.input_files.as_dict()
    assert 'bucket_name' in inputfiles[0]
    assert 'object_key' in inputfiles[0]
    assert inputfiles[0]['bucket_name'] == 'elasticbeanstalk-fourfront-cgapwolf-wfoutput'
    assert len(inputfiles[0]['object_key']) == 2
    assert inputfiles[0]['object_key'][0] == "GAPFIQNHLO6D.rck.gz"
    assert inputfiles[0]['object_key'][1] == "GAPFIZ25WPXE.rck.gz"


@valid_env
def test_extra_file_rename():
    """Test for rename tag working for extra files"""
    # This test requires the following files to have metadata (not necessarily the physical file)
    # eda72adf-3999-4ef4-adf7-58a64a9044d8, eda9be6d-0ecd-4bad-bd07-6e1a7efc98be
    # with accessions GAPFIQNHLO6D and GAPFIZ25WPXE
    # on cgapwolf
    # with extra files with format rck_gz_tbi and status uploaded
    # the format and status of these file items should be rck_gz and uploaded as well.
    input_file_list = [
       {
          "bucket_name": "bucket1",
          "workflow_argument_name": "input_rcks",
          "uuid": ["eda72adf-3999-4ef4-adf7-58a64a9044d8", "eda9be6d-0ecd-4bad-bd07-6e1a7efc98be"],
          "object_key": ["GAPFIQNHLO6D.rck.gz", "GAPFIZ25WPXE.rck.gz"],
          "rename": ["haha.rck.gz", "lala.rck.gz"]
       }
    ]
    _tibanna = {'env': 'fourfront-cgapwolf',
                'settings': {'1': '1'}}
    inp = ZebraInput(workflow_uuid='a',
                     config={'log_bucket': 'b'},
                     output_bucket='c',
                     input_files=input_file_list,
                     _tibanna=_tibanna)
    args = dict()
    args['input_files'] = inp.input_files.create_unicorn_arg_input_files()
    args['secondary_files'] = inp.input_files.create_unicorn_arg_secondary_files()
    assert 'input_rcks' in args['secondary_files']
    assert 'rename' in args['secondary_files']['input_rcks']
    assert len(args['secondary_files']['input_rcks']['rename']) == 2
    assert args['secondary_files']['input_rcks']['rename'][0] == ['haha.rck.gz.tbi']
    assert args['secondary_files']['input_rcks']['rename'][1] == ['lala.rck.gz.tbi']


@valid_env
def test_fourfront_starter2(start_run_event_bwa_check):
    starter = FourfrontStarter(**start_run_event_bwa_check)
    assert starter
    assert not starter.user_supplied_output_files('raw_bam')
    assert len(starter.output_argnames) == 2
    assert starter.output_argnames[0] == 'raw_bam'
    assert starter.arg('raw_bam')['argument_type'] == 'Output processed file'
    assert starter.pf('raw_bam')
    starter.create_pfs()
    assert len(starter.pfs) == 1


@valid_env
def test_fourfront_starter_custom_qc(start_run_event_vcfqc):
    starter = FourfrontStarter(**start_run_event_vcfqc)
    assert starter
    outjson = starter.inp.as_dict()
    assert 'custom_qc_fields' in outjson
    assert 'filtering_condition' in outjson['custom_qc_fields']


@valid_env
def test_bamcheck(update_ffmeta_event_data_bamcheck):
    updater = FourfrontUpdater(**update_ffmeta_event_data_bamcheck)
    updater.update_qc()
    target_accession = updater.accessions('raw_bam')[0]
    assert target_accession == '4DNFIWT3X5RU'
    assert updater.post_items
    assert len(updater.post_items['quality_metric_bamcheck']) == 1
    uuid = list(updater.post_items['quality_metric_bamcheck'].keys())[0]
    assert 'quickcheck' in updater.post_items['quality_metric_bamcheck'][uuid]


@valid_env
def test_cmphet(update_ffmeta_event_data_cmphet):
    updater = FourfrontUpdater(**update_ffmeta_event_data_cmphet)
    fake_parsed_qc_json = {"by_genes":[{"name": "ENSG00000007047"}]}
    fake_parsed_qc_table = {"check": "OK"}
    updater._metadata["GAPFI6IZ585N"] = {"accession": "GAPFI6IZ585N"}  # no quality_metric field
    with mock.patch("tibanna_ffcommon.qc.read_s3_data"):
        with mock.patch("tibanna_ffcommon.qc.QCDataParser.parse_qc_json", return_value=fake_parsed_qc_json):
            with mock.patch("tibanna_ffcommon.qc.QCDataParser.parse_qc_table", return_value=fake_parsed_qc_table):
                updater.update_qc()
    assert updater.post_items
    assert 'quality_metric_qclist' in updater.post_items
    assert 'quality_metric_cmphet' in updater.post_items
    assert 'quality_metric_vcfcheck' in updater.post_items
    logger.debug("post_items[quality_metric_qclist]=" + str(updater.post_items['quality_metric_qclist']))
    qclist_uuid = list(updater.post_items['quality_metric_qclist'].keys())[0]
    assert 'qc_list' in updater.post_items['quality_metric_qclist'][qclist_uuid]
    assert len(updater.post_items['quality_metric_qclist'][qclist_uuid]['qc_list']) == 2
    assert updater.post_items['quality_metric_qclist'][qclist_uuid]['project'] == DEFAULT_PROJECT
    assert updater.post_items['quality_metric_qclist'][qclist_uuid]['institution'] == DEFAULT_INSTITUTION


@valid_env
def test_cmphet_custom_qc_fields(update_ffmeta_event_data_cmphet):
    update_ffmeta_event_data_cmphet['custom_qc_fields'] = {
        'project': '/projects/test/',
        'institution': '/institutions/test/'
    }
    updater = FourfrontUpdater(**update_ffmeta_event_data_cmphet)
    fake_parsed_qc_json = {"by_genes":[{"name": "ENSG00000007047"}]}
    fake_parsed_qc_table = {"check": "OK"}
    updater._metadata["GAPFI6IZ585N"] = {"accession": "GAPFI6IZ585N"}  # no quality_metric field
    with mock.patch("tibanna_ffcommon.qc.read_s3_data"):
        with mock.patch("tibanna_ffcommon.qc.QCDataParser.parse_qc_json", return_value=fake_parsed_qc_json):
            with mock.patch("tibanna_ffcommon.qc.QCDataParser.parse_qc_table", return_value=fake_parsed_qc_table):
                updater.update_qc()
    assert updater.post_items
    assert 'quality_metric_qclist' in updater.post_items
    assert 'quality_metric_cmphet' in updater.post_items
    assert 'quality_metric_vcfcheck' in updater.post_items
    logger.debug("post_items[quality_metric_qclist]=" + str(updater.post_items['quality_metric_qclist']))
    qclist_uuid = list(updater.post_items['quality_metric_qclist'].keys())[0]
    assert 'qc_list' in updater.post_items['quality_metric_qclist'][qclist_uuid]
    assert len(updater.post_items['quality_metric_qclist'][qclist_uuid]['qc_list']) == 2
    # custom_qc_fields does not apply to qclist
    assert updater.post_items['quality_metric_qclist'][qclist_uuid]['project'] == DEFAULT_PROJECT
    assert updater.post_items['quality_metric_qclist'][qclist_uuid]['institution'] == DEFAULT_INSTITUTION
    qc_cmphet_uuid = list(updater.post_items['quality_metric_cmphet'].keys())[0]
    qc_vcfcheck_uuid = list(updater.post_items['quality_metric_vcfcheck'].keys())[0]
    assert updater.post_items['quality_metric_cmphet'][qc_cmphet_uuid]['project'] == "/projects/test/"
    assert updater.post_items['quality_metric_cmphet'][qc_cmphet_uuid]['institution'] == "/institutions/test/"
    assert updater.post_items['quality_metric_vcfcheck'][qc_vcfcheck_uuid]['project'] == "/projects/test/"
    assert updater.post_items['quality_metric_vcfcheck'][qc_vcfcheck_uuid]['institution'] == "/institutions/test/"


@valid_env
def test_cmphet_common_fields(update_ffmeta_event_data_cmphet):
    update_ffmeta_event_data_cmphet['common_fields'] = {
        'project': '/projects/test/',
        'institution': '/institutions/test/'
    }
    updater = FourfrontUpdater(**update_ffmeta_event_data_cmphet)
    fake_parsed_qc_json = {"by_genes":[{"name": "ENSG00000007047"}]}
    fake_parsed_qc_table = {"check": "OK"}
    updater._metadata["GAPFI6IZ585N"] = {"accession": "GAPFI6IZ585N"}  # no quality_metric field
    with mock.patch("tibanna_ffcommon.qc.read_s3_data"):
        with mock.patch("tibanna_ffcommon.qc.QCDataParser.parse_qc_json", return_value=fake_parsed_qc_json):
            with mock.patch("tibanna_ffcommon.qc.QCDataParser.parse_qc_table", return_value=fake_parsed_qc_table):
                updater.update_qc()
    assert updater.post_items
    assert 'quality_metric_qclist' in updater.post_items
    assert 'quality_metric_cmphet' in updater.post_items
    assert 'quality_metric_vcfcheck' in updater.post_items
    logger.debug("post_items[quality_metric_qclist]=" + str(updater.post_items['quality_metric_qclist']))
    qclist_uuid = list(updater.post_items['quality_metric_qclist'].keys())[0]
    assert 'qc_list' in updater.post_items['quality_metric_qclist'][qclist_uuid]
    assert len(updater.post_items['quality_metric_qclist'][qclist_uuid]['qc_list']) == 2
    # common fields do apply to qclist
    assert updater.post_items['quality_metric_qclist'][qclist_uuid]['project'] == "/projects/test/"
    assert updater.post_items['quality_metric_qclist'][qclist_uuid]['institution'] == "/institutions/test/"
    qc_cmphet_uuid = list(updater.post_items['quality_metric_cmphet'].keys())[0]
    qc_vcfcheck_uuid = list(updater.post_items['quality_metric_vcfcheck'].keys())[0]
    assert updater.post_items['quality_metric_cmphet'][qc_cmphet_uuid]['project'] == "/projects/test/"
    assert updater.post_items['quality_metric_cmphet'][qc_cmphet_uuid]['institution'] == "/institutions/test/"
    assert updater.post_items['quality_metric_vcfcheck'][qc_vcfcheck_uuid]['project'] == "/projects/test/"
    assert updater.post_items['quality_metric_vcfcheck'][qc_vcfcheck_uuid]['institution'] == "/institutions/test/"


@valid_env
def test_md5_common_fields(start_run_event_md5):
    start_run_event_md5['common_fields'] = {
        'project': '/projects/test/',
        'institution': '/institutions/test/'
    }
    starter = FourfrontStarter(**start_run_event_md5)
    # common fields apply to wfr (ff)
    starter.create_ff()
    assert starter.ff.project == '/projects/test/'
    assert starter.ff.institution == '/institutions/test/'


@valid_env
def test_md5_wfr_meta_common_fields(start_run_event_md5):
    start_run_event_md5['common_fields'] = {
        'project': '/projects/test/',
        'institution': '/institutions/test/'
    }
    start_run_event_md5['wfr_meta'] = {
        'project': '/projects/test2/',
        'institution': '/institutions/test2/'
    }
    starter = FourfrontStarter(**start_run_event_md5)
    # common fields apply to wfr (ff)
    starter.create_ff()
    assert starter.ff.project == '/projects/test2/'  # wfr_meta overwrites common_fields
    assert starter.ff.institution == '/institutions/test2/'  # wfr_meta overwrites common_fields
