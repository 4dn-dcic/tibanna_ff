import boto3
import gzip
from uuid import uuid4
import datetime
from dcicutils.ff_utils import (
    get_metadata,
    post_metadata,
    generate_rand_accession,
)
from tibanna_ffcommon.file_format import (
    parse_formatstr,
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
    PROCESSED_FILE_TYPES
)
from tibanna import create_logger

logger = create_logger(__name__)

class TigerInput(FFInputAbstract):
    
    def __init__(self, workflow_uuid=None, output_bucket=None, config=None, jobid='',
                 _tibanna=None, push_error_to_end=True, **kwargs):
        # Some Tibanna configurations have been renamed in SMaHT deal with it here
        mapping = {
            "behavior_on_capacity" : "behavior_on_capacity_limit",
            "ebs_optimized" : "EBS_optimized",
            "memory" : "mem",
        }
        for new_name, old_name in mapping.items():
            config[old_name] = new_name
            config.pop(new_name)

        super().__init__(workflow_uuid, output_bucket, config, jobid,
                 _tibanna, push_error_to_end, **kwargs)
    


class WorkflowRunMetadata(WorkflowRunMetadataAbstract):
    """
    smaht metadata
    """

    def __init__(self, workflow=None, input_files=[], output_files=None, postrun_json=None, 
                 run_status='started', run_url='', job_id=None, uuid=None, parameters=[], aliases=None,
                 title='', name='', **kwargs):
        """
        Class for WorkflowRun that matches the SMaHT Metadata schema
        Workflow (uuid of the workflow to run) has to be given.
        Workflow_run uuid is auto-generated when the object is created.
        We have to accept kwargs here, as this class is instantiated with variables 
        that are not in the schema (portal_utils:create_ff) for backwards compatibility
        """ 
        self.submission_centers = kwargs.get('submission_centers', [DEFAULT_SUBMISSION_CENTER])
        self.consortia = kwargs.get('consortia', [DEFAULT_CONSORTIUM])

        if not workflow:
            logger.warning("workflow is missing. %s may not behave as expected" % self.__class__.__name__)

        # The job_id could either come in through awsem_job_id or job_id
        self.job_id = job_id
        self.run_status = run_status
        self.uuid = uuid if uuid else str(uuid4())
        self.workflow = workflow
        if run_url:
            self.run_url = run_url
        self.name = name
        self.title = title + " run " + str(datetime.datetime.now())
        if aliases:
            self.aliases = aliases
        self.input_files = input_files
        self.output_files = output_files
        self.parameters = parameters
        if postrun_json:
            self.postrun_json = postrun_json

    def post(self, key, type_name=None):
        type_name = type_name or 'workflow_run'
        logger.debug("Posting workflow_run: self.as_dict()= " + str(self.as_dict()))
        return post_metadata(self.as_dict(), type_name, key=key)


class ProcessedFileMetadata(ProcessedFileMetadataAbstract):

    def __init__(self, **kwargs):
        self.submission_centers = kwargs.get('submission_centers', [DEFAULT_SUBMISSION_CENTER])
        self.consortia = kwargs.get('consortia', [DEFAULT_CONSORTIUM])

        if 'data_category' not in kwargs or 'data_type' not in kwargs:
            raise Exception("data_category and data_type are required for output files")

        self.data_category = kwargs.get('data_category') 
        self.data_type = kwargs.get('data_type')

        super().__init__(**kwargs)

    def post(self, key):
        logger.debug("in function post: self.__dict__ = " + str(self.__dict__))
        return post_metadata(self.as_dict(), "output_file", key=key, add_on='force_md5')


class QualityMetricsGenericMetadata(QualityMetricsGenericMetadataAbstract):

    def __init__(self, **kwargs):
        self.submission_centers = kwargs.get('submission_centers', [DEFAULT_SUBMISSION_CENTER])
        self.consortia = kwargs.get('consortia', [DEFAULT_CONSORTIUM])
        super().__init__(**kwargs)


class FourfrontStarter(FourfrontStarterAbstract):

    InputClass = TigerInput
    ProcessedFileMetadata = ProcessedFileMetadata
    WorkflowRunMetadata = WorkflowRunMetadata

    def create_ff(self):
        self.ff = self.WorkflowRunMetadata(
            workflow=self.inp.workflow_uuid,
            title=self.inp.wf_meta['title'],
            name=self.inp.wf_meta['name'],
            input_files=self.inp.input_files.create_input_files_for_wfrmeta(),
            run_url=self.tbn.settings.get('url', ''),
            output_files=self.create_ff_output_files(),
            parameters=self.inp.parameters,
            job_id=self.inp.jobid
        )

    # def pf(self, argname, **kwargs):
    #     if self.user_supplied_output_files(argname):
    #         res = self.get_meta(self.user_supplied_output_files(argname)[0]['uuid'])
    #         return self.ProcessedFileMetadata(**res)
    #     arg = self.arg(argname)
    #     if arg.get('argument_type') not in PROCESSED_FILE_TYPES:
    #         return None
    #     required_keys = set(['argument_format', 'data_category', 'data_type'])
    #     if not required_keys.issubset(arg.keys()):
    #         raise Exception(f"{', '.join(list(required_keys))} are required for an output file")
    #     if 'secondary_file_formats' in arg:
    #         extra_files = self.pf_extra_files(arg.get('secondary_file_formats', []),
    #                                           arg.get('processed_extra_file_use_for', {}))
    #     else:
    #         extra_files = None
    #     logger.debug("appending %s to pfs" % arg.get('workflow_argument_name'))
    #     other_fields = self.parse_custom_fields(self.inp.custom_pf_fields, self.inp.common_fields, argname)
    #     return self.ProcessedFileMetadata(
    #         file_format=arg.get('argument_format'),
    #         data_category=arg.get('data_category'),
    #         data_type=arg.get('data_type'),
    #         extra_files=extra_files,
    #         other_fields=other_fields,
    #         **kwargs
    #     )

 
class FourfrontUpdater(FourfrontUpdaterAbstract):
    """This class integrates three different sources of information:
    postrunjson, workflowrun, processed_files,
    and does the final updates necessary"""

    WorkflowRunMetadata = WorkflowRunMetadata
    ProcessedFileMetadata = ProcessedFileMetadata
    default_email_sender = 'smaht.everyone@gmail.com'
    higlass_buckets = HIGLASS_BUCKETS

    def get_portal_specific_item_name(self, item):
        # Note: Updates to this function probably need to be made in the other portal versions as well
        mapping = {
            "quality_metric": "quality_metric"
        }
        if item not in mapping:
            raise Exception(f"Could not find the item name for '{item}'")
        return mapping[item]
    
    @property
    def app_name(self):
        return self.ff_meta.name
    
    def update_metadata(self):
        for arg in self.output_argnames:
            if self.status(arg) != 'COMPLETED':
                self.ff_meta.run_status = 'error'
        self.update_all_pfs()
        logger.info("Updating md5...")
        self.update_md5()
        logger.info("Updating QC...")
        self.update_generic_qc()
        logger.info("Updating Extra files...")
        self.update_input_extras()
        logger.info("Posting everything...")
        self.post_all()
        logger.info("Patching everything...")
        self.patch_all()
        self.ff_meta.run_status = 'complete'
        logger.info("Patching workflow run metadata...")
        self.patch_ffmeta()


def post_random_file(bucket, ff_key,
                     file_format='bam', extra_file_format='bam_bai',
                     file_extension='bam', extra_file_extension='bam.bai',
                     schema='output_file', extra_status=None):
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
