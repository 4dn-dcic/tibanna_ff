import boto3
import gzip
from uuid import uuid4
from dcicutils.ff_utils import (
    get_metadata,
    post_metadata,
    generate_rand_accession,
)
from tibanna.nnested_array import (
    flatten,
)
from .vars import (
    DEFAULT_SUBMISSION_CENTER,
    DEFAULT_CONSORTIUM,
    ACCESSION_PREFIX,
    HIGLASS_BUCKETS
)
from tibanna_ffcommon.wfr import (
    WorkflowRunMetadataAbstract,
    aslist
)
from tibanna_ffcommon.portal_utils import (
    ProcessedFileMetadataAbstract,
    FourfrontStarterAbstract,
    FourfrontUpdaterAbstract,
    QualityMetricsGenericMetadataAbstract,
    FFInputAbstract,
)


class TigerInput(FFInputAbstract):
    pass


class WorkflowRunMetadata(WorkflowRunMetadataAbstract):
    """
    smaht metadata
    """

    def __init__(self, **kwargs):
        self.submission_center = kwargs.get('submission_centers', [DEFAULT_SUBMISSION_CENTER])[0]
        self.consortium = kwargs.get('consortia', [DEFAULT_CONSORTIUM])[0]
        super().__init__(**kwargs)


class ProcessedFileMetadata(ProcessedFileMetadataAbstract):

    accession_prefix = ACCESSION_PREFIX

    def __init__(self, **kwargs):
        self.submission_center = kwargs.get('submission_centers', [DEFAULT_SUBMISSION_CENTER])[0]
        self.consortium = kwargs.get('consortia', [DEFAULT_CONSORTIUM])[0]
        self.source_samples = kwargs.get('source_samples', None)
        super().__init__(**kwargs)


class QualityMetricsGenericMetadata(QualityMetricsGenericMetadataAbstract):

    def __init__(self, **kwargs):
        self.submission_center = kwargs.get('submission_centers', [DEFAULT_SUBMISSION_CENTER])[0]
        self.consortium = kwargs.get('consortia', [DEFAULT_CONSORTIUM])[0]
        super().__init__(**kwargs)


class FourfrontStarter(FourfrontStarterAbstract):

    InputClass = TigerInput
    ProcessedFileMetadata = ProcessedFileMetadata
    WorkflowRunMetadata = WorkflowRunMetadata

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.source_samples_ = None

    def pf(self, argname):
        return super().pf(argname, source_samples=self.source_samples)

    def get_source_sample(self, input_file_uuid):
        """
        Connects to smaht-portal and get source sample info as a unique list
        Takes a single input file uuid.
        """
        # pf_source_samples_set = set()
        # inf_uuids = aslist(flatten(input_file_uuid))
        # for inf_uuid in inf_uuids:
        #     infile_meta = get_metadata(inf_uuid,
        #                                key=self.tbn.ff_keys,
        #                                ff_env=self.tbn.env,
        #                                add_on='frame=object&datastore=database')
        #     if infile_meta.get('samples'):
        #         for exp in infile_meta.get('samples'):
        #             exp_obj = get_metadata(exp,
        #                                    key=self.tbn.ff_keys,
        #                                    ff_env=self.tbn.env,
        #                                    add_on='frame=raw&datastore=database')
        #             pf_source_samples_set.add(exp_obj['uuid'])
        #     if infile_meta.get('source_samples'):
        #         # this field is an array of strings, not linkTo's
        #         pf_source_samples_set.update(infile_meta.get('source_samples'))
        # return list(pf_source_samples_set)
        # TODO: implement this in more meaningful way once data model is complete
        return []

    def merge_source_samples(self):
        """
        Connects to smaht-portal and get source sample info as a unique list
        Takes a list of input file uuids (from class field).
        """
        # pf_source_samples = set()
        # for input_file_uuid in self.inp.input_file_uuids:
        #     pf_source_samples.update(self.get_source_sample(input_file_uuid))
        # return list(pf_source_samples)
        return []

    @property
    def source_samples(self):
        if self.source_samples_:
            return self.source_samples_
        else:
            self.source_samples_ = self.merge_source_samples()
            return self.source_samples_


class FourfrontUpdater(FourfrontUpdaterAbstract):
    """This class integrates three different sources of information:
    postrunjson, workflowrun, processed_files,
    and does the final updates necessary"""

    WorkflowRunMetadata = WorkflowRunMetadata
    ProcessedFileMetadata = ProcessedFileMetadata
    default_email_sender = 'smaht.everyone@gmail.com'
    higlass_buckets = HIGLASS_BUCKETS

    def qc_template_generator(self, add_custom_qc_fields=False):
        while True:
            res = next(super().qc_template_generator(add_custom_qc_fields=add_custom_qc_fields))
            if 'submission_centers' not in res:
                res.update({"submission_centers": DEFAULT_SUBMISSION_CENTER})
            if 'consortia' not in res:
                res.update({"consortia": [DEFAULT_CONSORTIUM]})
            yield res


def post_random_file(bucket, ff_key,
                     file_format='pairs', extra_file_format='pairs_px2',
                     file_extension='pairs.gz', extra_file_extension='pairs.gz.px2',
                     schema='file_processed', extra_status=None):
    """Generates a fake file with random uuid and accession
    and posts it to smaht-portal. The content is unique since it contains
    its own uuid. The file metadata does not contain md5sum or
    content_md5sum.
    Uses the given fourfront keys
    """
    uuid = str(uuid4())
    accession = generate_rand_accession(ACCESSION_PREFIX, 'FI')
    newfile = {
      "accession": accession,
      "file_format": file_format,
      "submission_centers": [DEFAULT_SUBMISSION_CENTER],
      "consortia": [DEFAULT_CONSORTIUM],
      "uuid": uuid
    }
    upload_key = uuid + '/' + accession + '.' + file_extension
    tmpfilename = 'alsjekvjf'
    with gzip.open(tmpfilename, 'wb') as f:
        f.write(uuid.encode('utf-8'))
    s3 = boto3.resource('s3')
    s3.meta.client.upload_file(tmpfilename, bucket, upload_key)

    # extra file
    if extra_file_format:
        newfile["extra_files"] = [
            {
               "file_format": extra_file_format,
               "accession": accession,
               "uuid": uuid
            }
        ]
        if extra_status:
            newfile["extra_files"][0]['status'] = extra_status
        extra_upload_key = uuid + '/' + accession + '.' + extra_file_extension
        extra_tmpfilename = 'alsjekvjf-extra'
        with open(extra_tmpfilename, 'w') as f:
            f.write(uuid + extra_file_extension)
        s3.meta.client.upload_file(extra_tmpfilename, bucket, extra_upload_key)
    response = post_metadata(newfile, schema, key=ff_key)
    print(response)
    return newfile
