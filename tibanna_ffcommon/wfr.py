from uuid import uuid4
import datetime
from tibanna.base import (
    SerializableObject
)
from tibanna.nnested_array import (
    flatten,
    create_dim
)
from dcicutils.ff_utils import (
    post_metadata,
    patch_metadata
)
from tibanna import create_logger


logger = create_logger(__name__)


class WorkflowRunMetadataAbstract(SerializableObject):
    '''
    fourfront metadata
    '''

    def __init__(self, workflow=None, awsem_app_name='', app_version=None, input_files=[],
                 parameters=[], title=None, uuid=None, output_files=None,
                 run_status='started', run_platform='AWSEM', run_url='', tag=None,
                 aliases=None,  awsem_postrun_json=None, submitted_by=None, extra_meta=None,
                 awsem_job_id=None, **kwargs):
        """Class for WorkflowRun that matches the 4DN Metadata schema
        Workflow (uuid of the workflow to run) has to be given.
        Workflow_run uuid is auto-generated when the object is created.
        """
        if not workflow:
            logger.warning("workflow is missing. %s may not behave as expected" % self.__class__.__name__)
        if run_platform == 'AWSEM':
            self.awsem_app_name = awsem_app_name
            # self.app_name = app_name
            if awsem_job_id is None:
                self.awsem_job_id = ''
            else:
                self.awsem_job_id = awsem_job_id
        else:
            raise Exception("invalid run_platform {} - it must be AWSEM".format(run_platform))

        self.run_status = run_status
        self.uuid = uuid if uuid else str(uuid4())
        self.workflow = workflow
        self.run_platform = run_platform
        if run_url:
            self.run_url = run_url

        if title is None:
            if app_version:
                title = awsem_app_name + ' ' + app_version
            else:
                title = awsem_app_name
            if tag:
                title = title + ' ' + tag
            title = title + " run " + str(datetime.datetime.now())
        self.title = title

        if aliases:
            if isinstance(aliases, basestring):  # noqa
                aliases = [aliases, ]
            self.aliases = aliases
        self.input_files = input_files
        self.output_files = output_files
        self.parameters = parameters
        if awsem_postrun_json:
            self.awsem_postrun_json = awsem_postrun_json
        if submitted_by:
            self.submitted_by = submitted_by

        if extra_meta:
            for k, v in iter(extra_meta.items()):
                self.__dict__[k] = v

    def append_outputfile(self, outjson):
        self.output_files.append(outjson)

    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)

    def post(self, key, type_name=None):
        if not type_name:
            if self.run_platform == 'AWSEM':
                type_name = 'workflow_run_awsem'
            else:
                raise Exception("cannot determine workflow schema type from the run platform: should be AWSEM.")
        logger.debug("in function post: self.as_dict()= " + str(self.as_dict()))
        return post_metadata(self.as_dict(), type_name, key=key)

    def patch(self, key, type_name=None):
        return patch_metadata(self.as_dict(), key=key)


class InputFilesForWFRMeta(object):
    """This class defines the structure of input_files as part of
    the workflow_run metadata.
    """
    def __init__(self):
        self.input_files = []

    @property
    def arg_names(self):
        return list(set([_.workflow_argument_name for _ in self.input_files]))

    def add_input_files(self, uuids_for_arg, arg_name, format_if_extra=''):
        """uuids_for_arg can be a single uuid, a list of uuids or a list of
        lists of uuids, etc. that corresponds to a single argument."""
        if arg_name in self.arg_names:
            raise Exception("Arg %s already exists in the list" % arg_name)
        dim = flatten(create_dim(uuids_for_arg))
        if not dim:  # singlet
            dim = '0'
        uuid = flatten(uuids_for_arg)
        ordinal = create_ordinal(uuid)
        for d, u, o in zip(aslist(dim), aslist(uuid), aslist(ordinal)):
            infileobj = InputFileForWFRMeta(arg_name, u, o,
                                            format_if_extra, d)
            self.append(infileobj)

    def append(self, inputfileforwfrmeta):
        self.input_files.append(inputfileforwfrmeta)

    def as_dict(self):
        return [_.as_dict() for _ in self.input_files]


class InputFileForWFRMeta(object):
    """This class defines the structure of an input_file as part of
    the workflow_run metadata. It is a single element of an input file list
    defined in the InputFilesForWFRMeta class.
    """
    def __init__(self, workflow_argument_name=None, value=None, ordinal=None,
                       format_if_extra=None, dimension=None):
        """dimension is '0' for a singleton argument,
        '0', '1', '2' ... for a 1d-list argument,
        '0-0', '0-1', ... , '1-0', '1-1', ... for a 2d-list argument, and so on.
        ordinal is 1 for a singleton,
        1, 2, 3, 4, ... for an any-dimensional list argument.
        value (uuid for the input file) is never a list
        """
        self.workflow_argument_name = workflow_argument_name
        self.value = value
        self.ordinal = ordinal
        if dimension:
            self.dimension = dimension
        if format_if_extra:
            self.format_if_extra = format_if_extra

    def as_dict(self):
        return self.__dict__


class WorkflowRunOutputFiles(SerializableObject):
    def __init__(self, workflow_argument_name, argument_type, file_format=None, secondary_file_formats=None,
                 upload_key=None, uuid=None, extra_files=None):
        self.workflow_argument_name = workflow_argument_name
        self.type = argument_type
        if file_format:
            self.format = file_format
        if extra_files:
            self.extra_files = extra_files
        if secondary_file_formats:
            self.secondary_file_formats = secondary_file_formats
        if uuid:
            self.value = uuid
        if upload_key:
            self.upload_key = upload_key


def create_ordinal(a):
    if isinstance(a, list):
        return list(range(1, len(a)+1))
    else:
        return 1


def aslist(x):
    if isinstance(x, list):
        return x
    else:
        return [x]
