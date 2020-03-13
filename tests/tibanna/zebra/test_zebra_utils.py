from tibanna_ffcommon.portal_utils import (
    TibannaSettings,
    FormatExtensionMap,
)
from tibanna_cgap.zebra_utils import (
    FourfrontStarter,
    FourfrontUpdater,
    ZebraInput
)
from tests.tibanna.zebra.conftest import valid_env


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


@valid_env
def test_extra_file_rename():
    """Test for rename tag working for extra files"""
    # This test requires the following files to have metadata (not necessarily the physical file)
    # eda72adf-3999-4ef4-adf7-58a64a9044d8, eda9be6d-0ecd-4bad-bd07-6e1a7efc98be
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
    inp.process_input_file_info(input_file_list[0], args)
    assert 'input_files' in args
    assert 'secondary_files' in args
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
def test_bamcheck(update_ffmeta_event_data_bamcheck):
    updater = FourfrontUpdater(**update_ffmeta_event_data_bamcheck)
    assert updater.workflow
    assert 'arguments' in updater.workflow
    assert updater.workflow_qc_arguments
    assert 'raw_bam' in updater.workflow_qc_arguments
    assert updater.workflow_qc_arguments['raw_bam'][0].qc_type == 'quality_metric_bamcheck'
    updater.update_qc()
    qc = updater.workflow_qc_arguments['raw_bam'][0]
    target_accession = updater.accessions('raw_bam')[0]
    assert qc.workflow_argument_name == 'raw_bam-check'
    assert qc.qc_table
    assert target_accession == '4DNFIWT3X5RU'
    assert updater.post_items
    assert len(updater.post_items['quality_metric_bamcheck']) == 1
    uuid = list(updater.post_items['quality_metric_bamcheck'].keys())[0]
    assert 'quickcheck' in updater.post_items['quality_metric_bamcheck'][uuid]
