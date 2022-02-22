from tibanna_ffcommon.portal_utils import (
    TibannaSettings,
    FormatExtensionMap,
)
from tibanna_cgap.zebra_utils import (
    FourfrontStarter,
    FourfrontUpdater,
    ProcessedFileMetadata,
)
import pytest
from dcicutils import ff_utils
from tests.tibanna.zebra.conftest import (
    valid_env,
)
from tests.tibanna.ffcommon.conftest import (
    minimal_postrunjson_template
)
from tests.tibanna.zebra.conftest import (
    post_new_processedfile,
    post_new_qc
)


# These are integrated tests intended to work with legacy environments.
# These need to be refactored to use cgap-wolf - Will Feb 22 2022
pytestmark = [pytest.mark.skip]


@valid_env
def test_fourfront_starter(start_run_event_md5):
    starter = FourfrontStarter(**start_run_event_md5)
    assert starter
    assert 'arguments' in starter.inp.wf_meta
    assert len(starter.inp.wf_meta['arguments']) == 2
    assert starter.inp.wf_meta['arguments'][1]['argument_type'] == 'Output report file'
    starter.run()
    assert len(starter.output_argnames) == 1


@valid_env
def test_qclist_handling():
    data = {'ff_meta': {'workflow': 'cgap:workflow_bwa-mem_no_unzip-check_v10'},
            'config': {'log_bucket': 'somelogbucket'},
            'postrunjson': minimal_postrunjson_template(),
            '_tibanna': {'env': 'fourfront-cgap', 'settings': {'1': '1'}}}
    updater = FourfrontUpdater(**data)

    new_qc_object = next(updater.qc_template_generator())

    # file w/ no quality_metric object
    new_pf_uuid = post_new_processedfile(file_format='bam', key=updater.tibanna_settings.ff_keys)
    updater.patch_qc(new_pf_uuid, new_qc_object['uuid'], 'quality_metric_bamcheck')
    assert new_pf_uuid in updater.patch_items
    assert updater.patch_items[new_pf_uuid]['quality_metric'] == new_qc_object['uuid']
    ff_utils.delete_metadata(new_pf_uuid, key=updater.tibanna_settings.ff_keys)

    # file w/ quality_metric object of same type
    existing_qc_uuid = post_new_qc('QualityMetricBamcheck', key=updater.tibanna_settings.ff_keys)
    new_pf_uuid = post_new_processedfile(file_format='bam', quality_metric=existing_qc_uuid,
                                         key=updater.tibanna_settings.ff_keys)
    updater.patch_qc(new_pf_uuid, new_qc_object['uuid'], 'quality_metric_bamcheck')
    assert new_pf_uuid in updater.patch_items
    assert updater.patch_items[new_pf_uuid]['quality_metric'] == new_qc_object['uuid']
    ff_utils.delete_metadata(new_pf_uuid, key=updater.tibanna_settings.ff_keys)
    ff_utils.delete_metadata(existing_qc_uuid, key=updater.tibanna_settings.ff_keys)

    # file w/ quality_metric object of different type
    existing_qc_uuid = post_new_qc('QualityMetricWgsBamqc', key=updater.tibanna_settings.ff_keys)
    new_pf_uuid = post_new_processedfile(file_format='bam', quality_metric=existing_qc_uuid,
                                         key=updater.tibanna_settings.ff_keys)
    updater.patch_qc(new_pf_uuid, new_qc_object['uuid'], 'quality_metric_bamcheck')
    assert new_pf_uuid in updater.patch_items
    new_qc_uuid = updater.patch_items[new_pf_uuid]['quality_metric']
    assert 'quality_metric_qclist' in updater.post_items
    assert new_qc_uuid in updater.post_items['quality_metric_qclist']
    res = updater.post_items['quality_metric_qclist'][new_qc_uuid]
    assert 'qc_list' in res
    assert len(res['qc_list']) == 2
    assert res['qc_list'][0]['qc_type'] == 'quality_metric_wgs_bamqc'
    assert res['qc_list'][1]['qc_type'] == 'quality_metric_bamcheck'
    assert res['qc_list'][0]['value'] == existing_qc_uuid
    assert res['qc_list'][1]['value'] == new_qc_object['uuid']
    ff_utils.delete_metadata(new_pf_uuid, key=updater.tibanna_settings.ff_keys)
    ff_utils.delete_metadata(existing_qc_uuid, key=updater.tibanna_settings.ff_keys)

    # file w/ qc list with only quality_metric object of different type
    existing_qc_uuid = post_new_qc('QualityMetricWgsBamqc', key=updater.tibanna_settings.ff_keys)
    existing_qclist = [{'qc_type': 'quality_metric_wgs_bamqc',
                        'value': existing_qc_uuid}]
    existing_qclist_uuid = post_new_qc('QualityMetricQclist', qc_list=existing_qclist,
                                       key=updater.tibanna_settings.ff_keys)
    new_pf_uuid = post_new_processedfile(file_format='bam', quality_metric=existing_qclist_uuid,
                                         key=updater.tibanna_settings.ff_keys)
    updater.patch_qc(new_pf_uuid, new_qc_object['uuid'], 'quality_metric_bamcheck')
    assert new_pf_uuid not in updater.patch_items
    assert existing_qclist_uuid in updater.patch_items
    assert 'qc_list' in updater.patch_items[existing_qclist_uuid]
    assert len(updater.patch_items[existing_qclist_uuid]['qc_list']) == 2
    res = updater.patch_items[existing_qclist_uuid]
    assert res['qc_list'][0]['qc_type'] == 'quality_metric_wgs_bamqc'
    assert res['qc_list'][1]['qc_type'] == 'quality_metric_bamcheck'
    assert existing_qc_uuid in res['qc_list'][0]['value']
    assert new_qc_object['uuid'] in res['qc_list'][1]['value']
    ff_utils.delete_metadata(new_pf_uuid, key=updater.tibanna_settings.ff_keys)
    ff_utils.delete_metadata(existing_qclist_uuid, key=updater.tibanna_settings.ff_keys)
    ff_utils.delete_metadata(existing_qc_uuid, key=updater.tibanna_settings.ff_keys)

    # file w/ qc list with only quality_metric object of same type
    existing_qc_uuid = post_new_qc('QualityMetricWgsBamqc', key=updater.tibanna_settings.ff_keys)
    existing_qclist = [{'qc_type': 'quality_metric_bamcheck',
                        'value': existing_qc_uuid}]
    existing_qclist_uuid = post_new_qc('QualityMetricQclist', qc_list=existing_qclist,
                                       key=updater.tibanna_settings.ff_keys)
    new_pf_uuid = post_new_processedfile(file_format='bam', quality_metric=existing_qclist_uuid,
                                         key=updater.tibanna_settings.ff_keys)
    updater.patch_qc(new_pf_uuid, new_qc_object['uuid'], 'quality_metric_bamcheck')
    assert new_pf_uuid not in updater.patch_items
    assert existing_qclist_uuid in updater.patch_items
    assert 'qc_list' in updater.patch_items[existing_qclist_uuid]
    assert len(updater.patch_items[existing_qclist_uuid]['qc_list']) == 1
    res = updater.patch_items[existing_qclist_uuid]
    assert res['qc_list'][0]['qc_type'] == 'quality_metric_bamcheck'
    assert res['qc_list'][0]['value'] == new_qc_object['uuid']
    ff_utils.delete_metadata(new_pf_uuid, key=updater.tibanna_settings.ff_keys)
    ff_utils.delete_metadata(existing_qclist_uuid, key=updater.tibanna_settings.ff_keys)
    ff_utils.delete_metadata(existing_qc_uuid, key=updater.tibanna_settings.ff_keys)
