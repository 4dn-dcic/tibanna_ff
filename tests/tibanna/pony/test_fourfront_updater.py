import boto3
from dcicutils import ff_utils
from tibanna_4dn.pony_utils import (
    FourfrontUpdater,
)
from tests.tibanna.pony.conftest import (
    valid_env,
)
import pytest
import mock


def test_FourfrontUpdater(update_ffmeta_event_data_fastqc2):
    updater = FourfrontUpdater(**update_ffmeta_event_data_fastqc2)
    assert updater
    assert updater.ff_meta
    assert updater.postrunjson
    assert updater.ff_output_files


def test_postrunjson_link(update_ffmeta_event_data_repliseq):
    updater = FourfrontUpdater(**update_ffmeta_event_data_repliseq)
    assert updater.ff_meta.awsem_postrun_json == 'https://s3.amazonaws.com/tibanna-output/Gkx8WiCOHJPq.postrun.json'


def test_get_postrunjson(update_ffmeta_event_data_repliseq):
    # get postrun json from the input json of update_ffmeta
    updater = FourfrontUpdater(**update_ffmeta_event_data_repliseq)
    assert updater.postrunjson.Job.App.App_name == 'repliseq-parta'


def test_get_postrunjson2(update_ffmeta_event_data_repliseq):
    # postrun json is truncated in the input json of update_ffmeta
    # get it from actual s3 bucket
    data = update_ffmeta_event_data_repliseq
    data['postrunjson'] = {'log': 'postrunjson is too long'}
    updater = FourfrontUpdater(**update_ffmeta_event_data_repliseq)
    assert updater.postrunjson.Job.App.App_name == 'repliseq-parta'


@valid_env
def test_post_patch(update_ffmeta_event_data_fastqc2):
    updater = FourfrontUpdater(**update_ffmeta_event_data_fastqc2)
    item = next(updater.qc_template_generator())
    item_uuid = item['uuid']
    updater.update_post_items(item_uuid, item, 'quality_metric_fastqc')
    assert 'uuid' in updater.post_items['quality_metric_fastqc'][item_uuid]
    assert updater.post_items['quality_metric_fastqc'][item_uuid]['uuid'] == item_uuid
    updater.create_wfr_qc()
    wfr_qc_uuid = updater.ff_meta.quality_metric
    assert updater.post_items['QualityMetricWorkflowrun'][wfr_qc_uuid]['lab'] == '4dn-dcic-lab'
    updater.post_all()
    updater.update_patch_items(item_uuid, {'Per base sequence content': 'PASS'})
    updater.patch_all()
    res = ff_utils.get_metadata(item_uuid, key=updater.tibanna_settings.ff_keys, add_on='?datastore=database')
    assert res['Per base sequence content'] == 'PASS'
    updater.update_patch_items(item_uuid, {'status': 'deleted'})
    updater.patch_all()
    res = ff_utils.get_metadata(item_uuid, key=updater.tibanna_settings.ff_keys, add_on='?datastore=database')
    assert res['status'] == 'deleted'


@valid_env
def test_rna_strandedness(update_ffmeta_event_data_rna_strandedness):
    report_key = 'lalala/match_count'
    s3 = boto3.client('s3')
    s3.put_object(Body='1234\n5'.encode('utf-8'),
                  Bucket='elasticbeanstalk-fourfront-webdev-wfoutput', Key=report_key)
    updater = FourfrontUpdater(**update_ffmeta_event_data_rna_strandedness)
    updater.update_rna_strandedness()
    sense, antisense = updater.parse_rna_strandedness_report(updater.read('match_count'))
    assert sense == 1234
    assert antisense == 5
    assert '4c3be0d1-cd00-4a14-85ed-43269591fe41' in updater.patch_items
    assert 'beta_actin_sense_count' in updater.patch_items['4c3be0d1-cd00-4a14-85ed-43269591fe41']
    assert 'beta_actin_antisense_count' in updater.patch_items['4c3be0d1-cd00-4a14-85ed-43269591fe41']
    assert updater.patch_items['4c3be0d1-cd00-4a14-85ed-43269591fe41']['beta_actin_sense_count'] == 1234
    assert updater.patch_items['4c3be0d1-cd00-4a14-85ed-43269591fe41']['beta_actin_antisense_count'] == 5
    s3.delete_object(Bucket='elasticbeanstalk-fourfront-webdev-wfoutput', Key=report_key)


@valid_env
def test_fastq_first_line(update_ffmeta_event_data_fastq_first_line):
    report_key = 'lalala/first_line'
    s3 = boto3.client('s3')
    s3.put_object(Body='@HWI-ST1318:469:HV2C3BCXY:1:1101:2874:1977 1:N:0:ATGTCA'.encode('utf-8'),
                  Bucket='elasticbeanstalk-fourfront-webdev-wfoutput', Key=report_key)
    updater = FourfrontUpdater(**update_ffmeta_event_data_fastq_first_line)
    updater.update_fastq_first_line()
    first_line = updater.parse_fastq_first_line_report(updater.read('first_line'))
    assert first_line == "@HWI-ST1318:469:HV2C3BCXY:1:1101:2874:1977 1:N:0:ATGTCA"
    assert '4c3be0d1-cd00-4a14-85ed-43269591fe41' in updater.patch_items
    assert 'file_first_line' in updater.patch_items['4c3be0d1-cd00-4a14-85ed-43269591fe41']
    assert updater.patch_items['4c3be0d1-cd00-4a14-85ed-43269591fe41']['file_first_line'] == \
        "@HWI-ST1318:469:HV2C3BCXY:1:1101:2874:1977 1:N:0:ATGTCA"
    s3.delete_object(Bucket='elasticbeanstalk-fourfront-webdev-wfoutput', Key=report_key)


@valid_env
def test_update_file_processed_format_re_check(update_ffmeta_event_data_re_check):
    report_key = 'lalala/re_report'
    s3 = boto3.client('s3')
    s3.put_object(Body='clipped-mates with RE motif: 76.54 %'.encode('utf-8'),
                  Bucket='elasticbeanstalk-fourfront-webdev-wfoutput', Key=report_key)
    updater = FourfrontUpdater(**update_ffmeta_event_data_re_check)
    input_uuid = updater.ff_meta.input_files[0]['value']
    updater.update_file_processed_format_re_check()
    precent_re = updater.parse_re_check(updater.read('motif_percent'))
    assert precent_re == 76.54
    assert input_uuid in updater.patch_items
    assert 'percent_clipped_sites_with_re_motif' in updater.patch_items[input_uuid]
    assert updater.patch_items[input_uuid]['percent_clipped_sites_with_re_motif'] == 76.54
    s3.delete_object(Bucket='elasticbeanstalk-fourfront-webdev-wfoutput', Key=report_key)


@valid_env
def test_md5(update_ffmeta_event_data_newmd5):
    report_key = 'lalala/md5_report'
    s3 = boto3.client('s3')
    s3.put_object(Body='1234\n5678'.encode('utf-8'),
                  Bucket='elasticbeanstalk-fourfront-webdev-wfoutput', Key=report_key)
    updater = FourfrontUpdater(**update_ffmeta_event_data_newmd5)
    assert updater.app_name == 'md5'
    with pytest.raises(Exception) as exec_info:
        updater.update_md5()
    assert 'md5sum not matching the original one' in str(exec_info.value)
    real_md5_content = 'bc75002f8a473bc6854d562789525a90\n6bb2dfa5b435ed03105cb59c32442d23'
    s3.put_object(Body=real_md5_content.encode('utf-8'),
                  Bucket='elasticbeanstalk-fourfront-webdev-wfoutput', Key=report_key)
    updater.update_md5()
    md5, content_md5 = updater.parse_md5_report(updater.read('report'))
    assert md5 == 'bc75002f8a473bc6854d562789525a90'
    assert content_md5 == '6bb2dfa5b435ed03105cb59c32442d23'
    assert 'f4864029-a8ad-4bb8-93e7-5108f462ccaa' in updater.patch_items
    assert 'md5sum' not in updater.patch_items['f4864029-a8ad-4bb8-93e7-5108f462ccaa']  # already in
    assert 'file_size' in updater.patch_items['f4864029-a8ad-4bb8-93e7-5108f462ccaa']
    s3.delete_object(Bucket='elasticbeanstalk-fourfront-webdev-wfoutput', Key=report_key)


@valid_env
def test_md5_for_extra(update_ffmeta_event_data_extra_md5):
    updater = FourfrontUpdater(**update_ffmeta_event_data_extra_md5)
    assert updater.input_argnames[0] == 'input_file'
    assert 'format_if_extra' in updater.ff_file('input_file')
    format_if_extras = updater.format_if_extras(updater.input_argnames[0])
    assert len(format_if_extras) == 1
    assert format_if_extras[0] == 'bed'
    updater.update_md5()
    assert updater.bucket('report') == 'elasticbeanstalk-fourfront-webprod-wfoutput'
    assert updater.file_key('report') == '00c8aca8-0e40-4ac7-9ef1-33d5c5652402/report473488522031'
    assert updater.status('report') == 'COMPLETED'
    assert 'd52b1206-f2a7-439a-ac17-c442e3bafe1d' in updater.patch_items
    # these no longer show up because the extra_file is fully patched? - Will Oct 17 2022
    # assert 'md5sum' in updater.patch_items['d52b1206-f2a7-439a-ac17-c442e3bafe1d']['extra_files'][0]
    # assert 'content_md5sum' in updater.patch_items['d52b1206-f2a7-439a-ac17-c442e3bafe1d']['extra_files'][0]
    # assert 'file_size' in updater.patch_items['d52b1206-f2a7-439a-ac17-c442e3bafe1d']['extra_files'][0]


@valid_env
def test_input_extra(update_ffmeta_event_data_bed2multivec):
    updater = FourfrontUpdater(**update_ffmeta_event_data_bed2multivec)
    assert 'bedfile' in updater.workflow_input_extra_arguments
    assert len(updater.workflow_input_extra_arguments['bedfile']) == 1
    ie = updater.workflow_input_extra_arguments['bedfile'][0]
    assert ie.workflow_argument_name == 'multivec_file'
    updater.update_input_extras()
    assert 'a7015222-390c-4e6f-8c94-77625f7b6bf7' in updater.patch_items
    assert 'extra_files' in updater.patch_items['a7015222-390c-4e6f-8c94-77625f7b6bf7']
    extra = updater.patch_items['a7015222-390c-4e6f-8c94-77625f7b6bf7']['extra_files'][0]
    assert extra['md5sum'] == '076ea000a803357f2a88f725ffeff435'
    assert extra['file_size'] == 8688344
    assert extra['status'] == 'uploaded'


@valid_env
def test_pf(update_ffmeta_hicbam):
    updater = FourfrontUpdater(**update_ffmeta_hicbam)
    updater.update_all_pfs()
    assert updater.patch_items
    assert 'eacc2a43-9fe8-41a7-89f4-7093619fde31' in updater.patch_items
    assert '5bded0bb-e429-48a2-bb85-e558111924e7' in updater.patch_items
    assert 'md5sum' in updater.patch_items['eacc2a43-9fe8-41a7-89f4-7093619fde31']
    assert 'file_size' in updater.patch_items['eacc2a43-9fe8-41a7-89f4-7093619fde31']
    assert 'status' in updater.patch_items['eacc2a43-9fe8-41a7-89f4-7093619fde31']
    outbam_patch = updater.patch_items['eacc2a43-9fe8-41a7-89f4-7093619fde31']
    assert outbam_patch['md5sum'] == 'eeff1f1bad00c0b386a3ce5f5751e1cc'
    assert outbam_patch['file_size'] == 313108291
    assert outbam_patch['status'] == 'uploaded'
    outpairs_patch = updater.patch_items['5bded0bb-e429-48a2-bb85-e558111924e7']
    assert outpairs_patch['extra_files'][0]['md5sum'] == '82ae753a21a52886d1e303c525208332'
    assert outpairs_patch['extra_files'][0]['file_size'] == 3300298
    assert outpairs_patch['extra_files'][0]['status'] == 'uploaded'


@valid_env
def test_fastqc(update_ffmeta_event_data_fastqc2):
    updater = FourfrontUpdater(**update_ffmeta_event_data_fastqc2)
    # pretend that this is the content of the zipped table file.
    fake_unzipped_data = ["Per sequence quality scores\t23.45\n" +
                          "Per base sequence content\t12.34\n" +
                          "Per sequence GC content\t45.67"]
    with mock.patch("tibanna_ffcommon.qc.unzip_s3_data", return_value=fake_unzipped_data):
        with mock.patch("tibanna_ffcommon.qc.unzip_s3_to_s3"):  # skip file copying
            updater.update_qc()
    target_accession = updater.accessions('input_fastq')[0]
    assert target_accession == '4DNFIRSRJH45'
    assert updater.post_items
    assert len(updater.post_items['quality_metric_fastqc']) == 1
    uuid = list(updater.post_items['quality_metric_fastqc'].keys())[0]
    print(str(updater.post_items['quality_metric_fastqc'][uuid]))
    assert 'url' in updater.post_items['quality_metric_fastqc'][uuid]
    assert 'Per sequence quality scores' in updater.post_items['quality_metric_fastqc'][uuid]
    assert 'Per base sequence content' in updater.post_items['quality_metric_fastqc'][uuid]
    assert 'Per sequence GC content' in updater.post_items['quality_metric_fastqc'][uuid]
    assert 'value_qc' in updater.ff_output_file('report_zip')
    assert updater.ff_output_file('report_zip')['value_qc'] == uuid


@valid_env
def test_pairsqc(update_ffmeta_event_data_pairsqc):
    updater = FourfrontUpdater(**update_ffmeta_event_data_pairsqc)
    fake_unzipped_data = ["Total reads\t651,962\nShort cis reads (<20kb)\t221,017\n" +
                          "Cis reads (>20kb)\t276,411\nTrans reads\t154,534\n" +
                          "Cis/Trans ratio\t67.89\n"]
    with mock.patch("tibanna_ffcommon.qc.unzip_s3_data", return_value=fake_unzipped_data):
        with mock.patch("tibanna_ffcommon.qc.unzip_s3_to_s3"):  # skip file copying
            updater.update_qc()
    target_accession = updater.accessions('input_pairs')[0]
    assert target_accession == '4DNFI1ZLO9D7'
    assert updater.post_items
    assert len(updater.post_items['quality_metric_pairsqc']) == 1
    uuid = list(updater.post_items['quality_metric_pairsqc'].keys())[0]
    assert 'Cis reads (>20kb)' in updater.post_items['quality_metric_pairsqc'][uuid]
    assert 'Trans reads' in updater.post_items['quality_metric_pairsqc'][uuid]
    assert 'Cis/Trans ratio' in updater.post_items['quality_metric_pairsqc'][uuid]

@valid_env
def test_madqc(update_ffmeta_event_data_madqc):
    updater = FourfrontUpdater(**update_ffmeta_event_data_madqc)
    updater.update_qc()
    target_accessions = updater.accessions('mad_qc.quantfiles')
    assert len(target_accessions) == 3
    assert target_accessions[0] == '4DNFIRV6DRTJ'
    assert target_accessions[1] == '4DNFILGR8Q3P'
    assert target_accessions[2] in updater.patch_items
    assert updater.post_items
    assert len(updater.post_items['quality_metric_rnaseq_madqc']) == 1
    uuid = list(updater.post_items['quality_metric_rnaseq_madqc'].keys())[0]
    assert len(updater.post_items['quality_metric_rnaseq_madqc'][uuid]['MAD QC']) == 3
    first_pair = list(updater.post_items['quality_metric_rnaseq_madqc'][uuid]['MAD QC'].keys())[0]
    assert len(updater.post_items['quality_metric_rnaseq_madqc'][uuid]['MAD QC'][first_pair]) == 4


@pytest.mark.skip  # refactor for prod data later
@valid_env
def test_repliseq(update_ffmeta_event_data_repliseq):
    updater = FourfrontUpdater(**update_ffmeta_event_data_repliseq)
    updater.update_all_pfs()
    updater.update_qc()
    target_accession = updater.accessions('filtered_sorted_deduped_bam')[0]
    assert target_accession == '4DNFIP2T7ANW'
    assert updater.post_items
    assert len(updater.post_items['quality_metric_dedupqc_repliseq']) == 1
    uuid = list(updater.post_items['quality_metric_dedupqc_repliseq'].keys())[0]
    assert 'Proportion of removed duplicates' in updater.post_items['quality_metric_dedupqc_repliseq'][uuid]
    assert updater.patch_items
    assert '050c9382-61d7-49e8-8598-1a6734dda5d2' in updater.patch_items
    bam_patch = updater.patch_items['050c9382-61d7-49e8-8598-1a6734dda5d2']  # filtered bam
    assert 'md5sum' in bam_patch
    assert 'file_size' in bam_patch
    assert 'status' in bam_patch
    assert bam_patch['md5sum'] == '908488c3d8bea2875551c67c9fd1b3dc'
    assert bam_patch['file_size'] == 11061946
    assert bam_patch['status'] == 'uploaded'
    assert 'quality_metric' in updater.patch_items['4DNFIP2T7ANW']  # qc_metric is patched by accession
    assert '4127ad92-16cf-4716-ab68-dc9b352658eb' in updater.patch_items
    bg_patch = updater.patch_items['4127ad92-16cf-4716-ab68-dc9b352658eb']  # count_bg
    assert 'extra_files' in bg_patch
    assert len(bg_patch['extra_files']) == 2
    assert bg_patch['extra_files'][1]['file_format'] == 'bw'
    assert bg_patch['extra_files'][1]['md5sum'] == 'f08575a366c14dbc949d35e415151cfd'
    assert bg_patch['extra_files'][1]['file_size'] == 3120059
    assert bg_patch['extra_files'][1]['status'] == 'uploaded'
    assert bg_patch['extra_files'][0]['file_format'] == 'bg_px2'
    assert bg_patch['extra_files'][0]['md5sum'] == 'aa8e2848e1f022b197fe31c804de08bf'
    assert bg_patch['extra_files'][0]['file_size'] == 991610
    assert bg_patch['extra_files'][0]['status'] == 'uploaded'


@pytest.mark.skip  # refactor for prod data later
@valid_env
def test_imargi(update_ffmeta_event_data_imargi):
    updater = FourfrontUpdater(**update_ffmeta_event_data_imargi)
    updater.update_all_pfs()
    updater.update_qc()
    target_accession = updater.accessions('out_pairs')[0]
    assert target_accession == '4DNFI2H7T6NP'
    assert updater.post_items
    assert len(updater.post_items['quality_metric_margi']) == 1
    uuid = list(updater.post_items['quality_metric_margi'].keys())[0]
    assert 'total_read_pairs' in updater.post_items['quality_metric_margi'][uuid]
    assert updater.patch_items
    assert 'aca7c203-f476-410f-b3bb-4965c9f5e411' in updater.patch_items
    pairs_patch = updater.patch_items['aca7c203-f476-410f-b3bb-4965c9f5e411']
    assert 'md5sum' in pairs_patch
    assert 'file_size' in pairs_patch
    assert 'status' in pairs_patch
    assert pairs_patch['md5sum'] == 'ec98b56a98249b85ee6a99a7f43f2884'
    assert pairs_patch['file_size'] == 22199565
    assert pairs_patch['status'] == 'uploaded'
    assert 'quality_metric' in updater.patch_items[target_accession]


@pytest.mark.skip  # refactor for prod data later
@valid_env
def test_chipseq(update_ffmeta_event_data_chipseq):
    updater = FourfrontUpdater(**update_ffmeta_event_data_chipseq)
    updater.update_all_pfs()
    updater.update_qc()
    target_accession = updater.accessions('chip.first_ta_ctl')[0]
    assert target_accession == '4DNFI8B19NWU'
    assert updater.post_items
    assert len(updater.post_items['quality_metric_chipseq']) == 1
    uuid = list(updater.post_items['quality_metric_chipseq'].keys())[0]
    assert 'ctl_dup_qc' in updater.post_items['quality_metric_chipseq'][uuid]
    assert updater.patch_items
    assert 'd3caa9c8-9e67-4d64-81d1-8039569dc6ce' in updater.patch_items
    bed_patch = updater.patch_items['d3caa9c8-9e67-4d64-81d1-8039569dc6ce']
    assert 'status' in bed_patch
    assert bed_patch['status'] == 'uploaded'
    assert 'quality_metric' in updater.patch_items[target_accession]
