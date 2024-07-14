import boto3
import gzip
import json
import copy
from uuid import uuid4
from dcicutils.ff_utils import (
    patch_metadata,
    post_metadata,
    generate_rand_accession,
)
from tibanna_ffcommon.file_format import (
    parse_formatstr,
)
from tibanna_ffcommon.input_files import FFInputFiles, FFInputFile
from tibanna.nnested_array import (
    flatten,
)
from .vars import (
    DEFAULT_SUBMISSION_CENTER,
    DEFAULT_CONSORTIUM,
    ACCESSION_PREFIX,
    HIGLASS_BUCKETS,
)
from tibanna_ffcommon.wfr import WorkflowRunMetadataAbstract, aslist
from tibanna_ffcommon.portal_utils import (
    ProcessedFileMetadataAbstract,
    FourfrontStarterAbstract,
    FourfrontUpdaterAbstract,
    QualityMetricsGenericMetadataAbstract,
    FFInputAbstract,
    QualityMetricGenericModel,
    OUTPUT_REPORT_FILE
)
from tibanna import create_logger

logger = create_logger(__name__)


class TigerInputFile(FFInputFile):
    def get_file_format_from_uuid(self, uuid):
        """returns parsed (cleaned) version of file format (e.g. 'bam')"""
        file_format_uuid = parse_formatstr(self.get_metadata(uuid)["file_format"])
        file_format = self.get_metadata(file_format_uuid)["identifier"]
        return file_format

    def get_extra_file_formats_from_uuid(self, uuid):
        """returns parsed (cleaned) version of file format (e.g. 'bai') for extra files"""
        extra_files = self.get_extra_files_from_uuid(uuid)
        if not extra_files:
            return None
        file_formats = []
        for exf in extra_files:
            file_format_uuid = parse_formatstr(exf["file_format"])
            file_formats.append(self.get_metadata(file_format_uuid)["identifier"])
        return file_formats


class TigerInputFiles(FFInputFiles):
    def __init__(self, input_files, ff_key=None, ff_env=None):
        """input_files : list of dictionaries provided as part of
        Tiger input json as the field 'input_files'
        """
        self.input_files = [
            TigerInputFile(**inpf, ff_key=ff_key, ff_env=ff_env) for inpf in input_files
        ]
        self.ff_key = ff_key
        self.ff_env = ff_env


class TigerInput(FFInputAbstract):
    InputFiles = TigerInputFiles

    def __init__(
        self,
        workflow_uuid=None,
        output_bucket=None,
        config=None,
        jobid="",
        _tibanna=None,
        push_error_to_end=True,
        **kwargs,
    ):
        # Some Tibanna configurations have been renamed in the SMaHT schema. Deal with it here.
        mapping = {
            "ebs_optimized": "EBS_optimized",
            "memory": "mem",
        }
        for new_name, old_name in mapping.items():
            if new_name in config:
                config[old_name] = config[new_name]
                config.pop(new_name)

        super().__init__(
            workflow_uuid,
            output_bucket,
            config,
            jobid,
            _tibanna,
            push_error_to_end,
            **kwargs,
        )

    @property
    def wf_meta(self):
        wf = self.get_metadata(self.workflow_uuid)

        # SMaHT workflows don't have workflow language specific fields. Handle this here
        if wf.get("language", "") in [
            "WDL",
            "CWL",
        ]:  # workflow_language is called language in SMaHT
            lang = str(wf.get("language")).lower()
            wf["workflow_language"] = lang
            if "directory_url" in wf:
                wf[f"{lang}_directory_url"] = wf["directory_url"]
            if "main_file_name" in wf:
                wf[f"{lang}_main_filename"] = wf["main_file_name"]
            if "child_file_names" in wf:
                wf[f"{lang}_child_filenames"] = wf["child_file_names"]
            if lang == "cwl":
                wf["cwl_directory_url_v1"] = wf[
                    "cwl_directory_url"
                ]  # This makes sure CWL v1 is used

        logger.warning(f"Workflow metadata used for Tibanna: {json.dumps(wf)}")
        return wf


class WorkflowRunMetadata(WorkflowRunMetadataAbstract):
    """
    smaht metadata
    """

    def __init__(
        self,
        workflow=None,
        input_files=[],
        output_files=None,
        postrun_json=None,
        run_status="started",
        run_url="",
        job_id=None,
        uuid=None,
        parameters=[],
        aliases=None,
        title="",
        extra_meta=None,
        **kwargs,
    ):
        """
        Class for WorkflowRun that matches the SMaHT Metadata schema
        Workflow (uuid of the workflow to run) has to be given.
        Workflow_run uuid is auto-generated when the object is created.
        We have to accept kwargs here, as this class is instantiated with variables
        that are not in the schema (portal_utils:create_ff) for backwards compatibility
        """
        self.submission_centers = kwargs.get(
            "submission_centers", [DEFAULT_SUBMISSION_CENTER]
        )
        self.consortia = kwargs.get("consortia", [DEFAULT_CONSORTIUM])

        if not workflow:
            logger.warning(
                "workflow is missing. %s may not behave as expected"
                % self.__class__.__name__
            )

        # The job_id could either come in through awsem_job_id or job_id
        self.job_id = job_id
        self.run_status = run_status
        self.uuid = uuid if uuid else str(uuid4())
        self.workflow = workflow
        if run_url:
            self.run_url = run_url
        self.title = title
        if aliases:
            self.aliases = aliases
        self.input_files = input_files
        self.output_files = output_files
        self.parameters = parameters
        if postrun_json:
            self.postrun_json = postrun_json
        if extra_meta:
            for k, v in iter(extra_meta.items()):
                self.__dict__[k] = v

    def set_postrun_json_url(self, url):
        self.postrun_json = url

    def post(self, key, type_name=None):
        type_name = type_name or "workflow_run"
        patch_dict = self.as_dict()
        patch_dict = self.restrict_parameters(patch_dict)
        patch_dict = self.restrict_output_file_properties(patch_dict)
        logger.debug("Posting workflow_run: patch_dict= " + str(patch_dict))
        return post_metadata(patch_dict, type_name, key=key)

    def patch(self, key, type_name=None):
        patch_dict = self.as_dict()
        patch_dict = self.restrict_parameters(patch_dict)
        patch_dict = self.restrict_output_file_properties(patch_dict)
        logger.debug("Patching workflow_run: patch_dict= " + str(patch_dict))
        return patch_metadata(patch_dict, key=key)

    def restrict_parameters(self, patch_dict):
        # If there are no parameters remove the key,
        # so that we don't try to patch an empty list to the portal
        if not patch_dict["parameters"]:
            del patch_dict["parameters"]
        return patch_dict

    def restrict_output_file_properties(self, patch_dict):
        output_files = copy.deepcopy(patch_dict["output_files"])
        restricted_output_files = []
        for of in output_files:
            if of['type'] == OUTPUT_REPORT_FILE:
                continue
            restricted_output_files.append(
                {
                    "workflow_argument_name": of["workflow_argument_name"],
                    "value": of["value"],
                }
            )
        if len(restricted_output_files) == 0:
            del patch_dict["output_files"]
        else:
            patch_dict["output_files"] = restricted_output_files
        return patch_dict


class ProcessedFileMetadata(ProcessedFileMetadataAbstract):
    accession_prefix = ACCESSION_PREFIX

    def __init__(self, **kwargs):
        self.submission_centers = kwargs.get(
            "submission_centers", [DEFAULT_SUBMISSION_CENTER]
        )
        self.consortia = kwargs.get("consortia", [DEFAULT_CONSORTIUM])

        # data_category and data_type come in through other_fields when the file is first posted,
        # in the UpdateFFMeta step they come in through kwargs
        self.data_category = kwargs.get("data_category", [])
        self.data_type = kwargs.get("data_type", [])

        other_fields = kwargs.get("other_fields", {})
        if other_fields and "data_category" in other_fields and "data_type" in other_fields:
            # Convert to array if these were passed as strings
            dc = other_fields["data_category"]
            other_fields["data_category"] = [dc] if type(dc) is str else dc
            dt = other_fields["data_type"]
            other_fields["data_type"] = [dt] if type(dt) is str else dt

        super().__init__(**kwargs)

    def post(self, key):
        logger.debug("in function post: self.__dict__ = " + str(self.__dict__))
        return post_metadata(self.as_dict(), "output_file", key=key, add_on="force_md5")


class QualityMetricsGenericMetadata(QualityMetricsGenericMetadataAbstract):
    def __init__(self, **kwargs):
        self.submission_centers = kwargs.get(
            "submission_centers", [DEFAULT_SUBMISSION_CENTER]
        )
        self.consortia = kwargs.get("consortia", [DEFAULT_CONSORTIUM])
        super().__init__(**kwargs)

    def update(self, qmg: QualityMetricGenericModel):
        if qmg.overall_quality_status:
            self.overall_quality_status = qmg.overall_quality_status.capitalize()  # This is, e.g., "Pass" as in the SMaHT data model
        if qmg.url:
            self.url = qmg.url
        #self.name = qmg.name
        qc_values = []
        for qcv in qmg.qc_values:
            qc_value = {}
            # There does not seem to be a better way to get all keys (including extra fields) from a Pydantic model
            # We are patching everything to the portal that we obtain from qc-parser and that is added by tibanna_ff
            # in previous steps.
            available_keys = list(qcv.model_dump().keys()) 
            for key in available_keys:
                qc_value[key] = getattr(qcv, key)

            # flag come from the Tibanna internal model and needs to be converted to the SMaHT data model.
            # This is, e.g., "Pass" as in the SMaHT data model
            if "flag" in available_keys:
                qc_value["flag"] = qcv.flag.capitalize() 

            qc_values.append(qc_value)

        self.qc_values = qc_values


class FourfrontStarter(FourfrontStarterAbstract):
    InputClass = TigerInput
    ProcessedFileMetadata = ProcessedFileMetadata
    WorkflowRunMetadata = WorkflowRunMetadata

    def create_ff(self):
        extra_meta = dict()
        if self.inp.common_fields:
            extra_meta.update(self.inp.common_fields)

        self.ff = self.WorkflowRunMetadata(
            workflow=self.inp.workflow_uuid,
            title=self.inp.wf_meta["title"],
            input_files=self.inp.input_files.create_input_files_for_wfrmeta(),
            run_url=self.tbn.settings.get("url", ""),
            output_files=self.create_ff_output_files(),
            parameters=self.inp.parameters,
            job_id=self.inp.jobid,
            extra_meta=extra_meta,
        )


class FourfrontUpdater(FourfrontUpdaterAbstract):
    """This class integrates three different sources of information:
    postrunjson, workflowrun, processed_files,
    and does the final updates necessary"""

    WorkflowRunMetadata = WorkflowRunMetadata
    ProcessedFileMetadata = ProcessedFileMetadata
    QualityMetricsGenericMetadata = QualityMetricsGenericMetadata
    default_email_sender = "smaht.everyone@gmail.com"
    higlass_buckets = HIGLASS_BUCKETS

    def get_portal_specific_item_name(self, item):
        # Note: Updates to this function probably need to be made in the other portal versions as well
        mapping = {"quality_metric": "quality_metric"}
        if item not in mapping:
            raise Exception(f"Could not find the item name for '{item}'")
        return mapping[item]

    @property
    def app_name(self):
        if self.ff_meta.title and self.ff_meta.title.startswith("md5"):
            return "md5"
        return self.ff_meta.title

    def update_metadata(self):
        for arg in self.output_argnames:
            if self.status(arg) != "COMPLETED":
                self.ff_meta.run_status = "error"
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
        self.ff_meta.run_status = "complete"
        logger.info("Patching workflow run metadata...")
        self.patch_ffmeta()

    def set_ff_output_files(self):
        output_files = []
        for of in self.ff_meta.output_files:
            
            if of['type'] == OUTPUT_REPORT_FILE:
                output_files.append(
                    {
                        "workflow_argument_name": of["workflow_argument_name"],
                        "type": of["type"],
                    }
                )
            else:
                # We need additional infos from the portal
                uuid = of["value"]
                of_metadata = self.get_metadata(uuid)
                output_files.append(
                    {
                        "workflow_argument_name": of["workflow_argument_name"],
                        "type": of["type"],
                        "upload_key": of_metadata["upload_key"],
                        "format": of_metadata["file_format"],
                        "extra_files": of_metadata["extra_files"]
                        if "extra_files" in of_metadata
                        else [],
                        "value": uuid,
                    }
                )

        return output_files


def post_random_file(
    bucket,
    ff_key,
    file_format="bam",
    extra_file_format="bam_bai",
    file_extension="bam",
    extra_file_extension="bam.bai",
    schema="output_file",
    extra_status=None,
):
    """Generates a fake file with random uuid and accession
    and posts it to smaht-portal. The content is unique since it contains
    its own uuid. The file metadata does not contain md5sum or
    content_md5sum.
    Uses the given fourfront keys
    """
    uuid = str(uuid4())
    accession = generate_rand_accession(ACCESSION_PREFIX, "FI")
    newfile = {
        "accession": accession,
        "file_format": file_format,
        "submission_centers": [DEFAULT_SUBMISSION_CENTER],
        "consortia": [DEFAULT_CONSORTIUM],
        "uuid": uuid,
    }
    upload_key = uuid + "/" + accession + "." + file_extension
    tmpfilename = "alsjekvjf"
    with gzip.open(tmpfilename, "wb") as f:
        f.write(uuid.encode("utf-8"))
    s3 = boto3.resource("s3")
    s3.meta.client.upload_file(tmpfilename, bucket, upload_key)

    # extra file
    if extra_file_format:
        newfile["extra_files"] = [
            {"file_format": extra_file_format, "accession": accession, "uuid": uuid}
        ]
        if extra_status:
            newfile["extra_files"][0]["status"] = extra_status
        extra_upload_key = uuid + "/" + accession + "." + extra_file_extension
        extra_tmpfilename = "alsjekvjf-extra"
        with open(extra_tmpfilename, "w") as f:
            f.write(uuid + extra_file_extension)
        s3.meta.client.upload_file(extra_tmpfilename, bucket, extra_upload_key)
    response = post_metadata(newfile, schema, key=ff_key)
    print(response)
    return newfile
