import json
import datetime
import boto3
import copy
import random
from uuid import uuid4
import requests
from dcicutils.ff_utils import (
    get_metadata,
    post_metadata,
    patch_metadata,
    search_metadata,
    generate_rand_accession,
    convert_param
)
from tibanna.nnested_array import (
    run_on_nested_arrays1,
    run_on_nested_arrays2,
    combine_two,
    flatten,
    create_dim
)
from dcicutils.s3_utils import s3Utils
from tibanna import create_logger
from tibanna.utils import (
    does_key_exist,
    read_s3
)
from tibanna.base import (
    SerializableObject
)
from tibanna.ec2_utils import (
    Args,
    Config
)
from tibanna.awsem import (
    AwsemPostRunJson
)
from tibanna.vars import (
    METRICS_URL,
    DYNAMODB_TABLE,
    DYNAMODB_KEYNAME,
)
from .vars import BUCKET_NAME
from .config import (
    higlass_config
)
from .exceptions import (
    TibannaStartException,
    FdnConnectionException,
    MalFormattedFFInputException,
    MalFormattedWorkflowMetadataException
)


logger = create_logger(__name__)


class FFInputAbstract(SerializableObject):
    def __init__(self, workflow_uuid=None, output_bucket=None, config=None, jobid='',
                 _tibanna=None, push_error_to_end=True, **kwargs):
        if not workflow_uuid:
            raise MalFormattedFFInputException("missing field in input json: workflow_uuid")
        if not config:
            raise MalFormattedFFInputException("missing field in input json: config")
        self.config = Config(**config)
        self.jobid = jobid

        self.input_files = kwargs.get('input_files', [])
        for infile in self.input_files:
            if not infile or 'uuid' not in infile or 'workflow_argument_name' not in infile:
                raise MalFormattedFFInputException("malformed input, check input_files in your input json")

        self.workflow_uuid = workflow_uuid
        self.output_bucket = output_bucket
        self.parameters_ = kwargs.get('parameters', {})
        self.parameters = convert_param(self.parameters_, True)
        self.additional_benchmarking_parameters = kwargs.get('additional_benchmarking_parameters', {})
        self.tag = kwargs.get('tag', None)
        self.common_fields = kwargs.get('common_fields', None)  # common custom fields (PF, WFR, QC, WFR_QC, QC_LIST)
        # these three can overwrite common_fields for pf, wfr and qc respectively
        self.custom_pf_fields = kwargs.get('custom_pf_fields', None)  # custon fields for PF
        self.wfr_meta = kwargs.get('wfr_meta', None)  # custom fields for WFR
        self.custom_qc_fields = kwargs.get('custom_qc_fields', None)  # custom fields for QC (but not WFR_QC and QC_LIST)
        self.output_files = kwargs.get('output_files', [])  # for user-supplied output files
        self.dependency = kwargs.get('dependency', None)
        self.wf_meta_ = None
        self.push_error_to_end = push_error_to_end

        self._tibanna = _tibanna
        self.tibanna_settings = None
        if _tibanna:
            env = _tibanna.get('env', '')
            try:
                self.tibanna_settings = TibannaSettings(env, settings=_tibanna)
            except Exception as e:
                raise TibannaStartException("%s" % e)

        if 'overwrite_input_extra' in kwargs:
            self.config.overwrite_input_extra = kwargs['overwrite_input_extra']
        if not hasattr(self.config, 'overwrite_input_extra'):
            self.config.overwrite_input_extra = False
        if not hasattr(self.config, 'public_postrun_json'):
            self.config.public_postrun_json = True
        if not hasattr(config, 'email'):
            self.config.email = False

        def get_object_key_from_uuid(uuid):
            infile_meta = self.get_metadata(uuid)
            return infile_meta['upload_key'].replace(uuid + '/', '')

        def get_file_type_from_uuid(uuid):
            infile_meta = self.get_metadata(uuid)
            return(infile_meta['@type'][0])

        # fill in input_files info if object_key and bucket_name is not provided
        for infile in self.input_files:
            if 'object_key' not in infile:
                try:
                    infile['object_key'] = run_on_nested_arrays1(infile['uuid'], get_object_key_from_uuid)
                except Exception as e:
                    raise FdnConnectionException(e)
            if 'bucket_name' not in infile:
                try:
                    infile_type = flatten(run_on_nested_arrays1(infile['uuid'], get_file_type_from_uuid))
                    if isinstance(infile_type, list):
                        infile_type = infile_type[0]
                except Exception as e:
                    raise FdnConnectionException(e)
                # assume all file types are the same for a given argument
                infile['bucket_name'] = BUCKET_NAME(self.tibanna_settings.env, infile_type)
            logger.debug("infile = " + str(infile))

        # fill in output_bucket
        if not self.output_bucket:
            self.output_bucket = BUCKET_NAME(self.tibanna_settings.env, 'FileProcessed')

    def as_dict(self):
        d_shallow = self.__dict__.copy()
        del(d_shallow['parameters_'])
        del(d_shallow['wf_meta_'])
        del(d_shallow['tibanna_settings'])
        do = SerializableObject()
        do.update(**d_shallow)
        return do.as_dict()

    @property
    def input_file_uuids(self):
        return [_['uuid'] for _ in self.input_files]

    def get_metadata(self, id):
        return get_metadata(id,
                            key=self.tibanna_settings.ff_keys,
                            ff_env=self.tibanna_settings.env,
                            add_on='frame=object',
                            check_queue=True)

    @property
    def wf_meta(self):
        if self.wf_meta_:
            return self.wf_meta_
        try:
            self.wf_meta_ = self.get_metadata(self.workflow_uuid)
            return self.wf_meta_
        except Exception as e:
            raise FdnConnectionException(e)

    def get_accessions_from_argname(self, argname, ff_meta):
        accessions = []
        for inf in ff_meta.input_files + ff_meta.output_files:
            if inf['workflow_argument_name'] == argname:
                if 'value' not in inf:
                    continue
                if isinstance(inf['value'], dict):
                    if 'accesion' in inf['value']:
                        accessions.append(inf['value']['accession'])
                    else:
                        res = self.get_metadata(inf['value']['uuid'])
                        accessions.append(res['accession'])
                else:
                    res = self.get_metadata(inf['value'])
                    accessions.append(res['accession'])
        return accessions
 
    def add_args(self, ff_meta):
        # create args
        args = dict()
        for k in ['app_name', 'app_version', 'cwl_directory_url', 'cwl_main_filename', 'cwl_child_filenames',
                  'wdl_directory_url', 'wdl_main_filename', 'wdl_child_filenames']:
            logger.debug("wfmeta[%s]=%s" % (k, str(self.wf_meta.get(k))))
            args[k] = self.wf_meta.get(k, '')
        if self.wf_meta.get('workflow_language', '') == 'WDL_DRAFT2':
            args['language'] = 'wdl_draft2'
        elif self.wf_meta.get('workflow_language', '') == 'WDL':
            args['language'] = 'wdl'
        else:
            # switch to v1 if available
            if 'cwl_directory_url_v1' in self.wf_meta:  # use CWL v1
                args['cwl_directory_url'] = self.wf_meta['cwl_directory_url_v1']
                args['cwl_version'] = 'v1'
            else:
                args['cwl_version'] = 'draft3'

        args['input_parameters'] = self.parameters_
        args['additional_benchmarking_parameters'] = self.additional_benchmarking_parameters
        args['output_S3_bucket'] = self.output_bucket
        args['dependency'] = self.dependency

        # output target
        args['output_target'] = dict()
        args['secondary_output_target'] = dict()
        for of in ff_meta.output_files:
            arg_name = of.get('workflow_argument_name')
            if of.get('type') == 'Output processed file':
                args['output_target'][arg_name] = of.get('upload_key')
            elif of.get('type') == 'Output to-be-extra-input file':
                target_inf = ff_meta.input_files[0]  # assume only one input for now
                target_key = self.output_target_for_input_extra(target_inf, of)
                args['output_target'][arg_name] = target_key
            else:  # output QC or report file
                wf_of = [_ for _ in self.wf_meta.get('arguments') if _['workflow_argument_name'] == arg_name][0]
                if wf_of.get('qc_zipped', False) and wf_of.get('qc_unzip_from_ec2', False):
                    if 'argument_to_be_attached_to' not in wf_of:
                        raise MalFormattedWorkflowMetadataException
                    target_argument = wf_of.get('argument_to_be_attached_to')
                    target_accession = self.get_accessions_from_argname(target_argument, ff_meta)[0]
                    args['output_target'][arg_name] = {"unzip": True, "object_prefix": target_accession}
                else:
                    random_tag = str(int(random.random() * 1000000000000))
                    # add a random tag at the end for non-processed file e.g. md5 report,
                    # so that if two or more wfr are trigerred (e.g. one with parent file, one with extra file)
                    # it will create a different output. Not implemented for processed files -
                    # it's tricky because processed files must have a specific name.
                    args['output_target'][arg_name] = ff_meta.uuid + '/' + arg_name + random_tag
            if 'secondary_file_formats' in of and 'extra_files' in of and of['extra_files']:
                for ext in of.get('extra_files'):
                    logger.info("adding secondary file: %s for arg %s" % (ext.get('upload_key', ''), arg_name))
                    if arg_name not in args['secondary_output_target']:
                        args['secondary_output_target'][arg_name] = []
                    args['secondary_output_target'][arg_name].append(ext.get('upload_key'))

        # input files
        for input_file in self.input_files:
            self.process_input_file_info(input_file, args)

        args['custom_errors'] = self.wf_meta.get('custom_errors', [])

        # create Args class object
        self.args = Args(**args)

    def output_target_for_input_extra(self, target_inf, of):
        extrafileexists = False
        logger.debug("target_inf = %s" % str(target_inf))
        target_inf_meta = get_metadata(target_inf.get('value'),
                                       key=self.tibanna_settings.ff_keys,
                                       ff_env=self.tibanna_settings.env,
                                       add_on='frame=object',
                                       check_queue=True)
        target_format = parse_formatstr(of.get('format'))
        if target_inf_meta.get('extra_files'):
            for exf in target_inf_meta.get('extra_files'):
                if parse_formatstr(exf.get('file_format')) == target_format:
                    extrafileexists = True
                    if self.config.overwrite_input_extra:
                        exf['status'] = 'to be uploaded by workflow'
                    break
            if not extrafileexists:
                new_extra = {'file_format': target_format, 'status': 'to be uploaded by workflow'}
                target_inf_meta['extra_files'].append(new_extra)
        else:
            new_extra = {'file_format': target_format, 'status': 'to be uploaded by workflow'}
            target_inf_meta['extra_files'] = [new_extra]
        if self.config.overwrite_input_extra or not extrafileexists:
            # first patch metadata
            logger.debug("extra_files_to_patch: %s" % str(target_inf_meta.get('extra_files')))
            patch_metadata({'extra_files': target_inf_meta.get('extra_files')},
                           target_inf.get('value'),
                           key=self.tibanna_settings.ff_keys,
                           ff_env=self.tibanna_settings.env)
            # target key
            # NOTE : The target bucket is assume to be the same as output bucket
            # i.e. the bucket for the input file should be the same as the output bucket.
            # which is true if both input and output are processed files.
            orgfile_key = target_inf_meta.get('upload_key')
            orgfile_format = parse_formatstr(target_inf_meta.get('file_format'))
            fe_map = FormatExtensionMap(self.tibanna_settings.ff_keys)
            logger.debug("orgfile_key = %s" % orgfile_key)
            logger.debug("orgfile_format = %s" % orgfile_format)
            logger.debug("target_format = %s" % target_format)
            target_key = get_extra_file_key(orgfile_format, orgfile_key, target_format, fe_map)
            return target_key
        else:
            raise Exception("input already has extra: 'User overwrite_input_extra': true")

    def process_input_file_info(self, input_file, args):
        if not args or 'input_files' not in args:
            args['input_files'] = dict()
        if not args or 'secondary_files' not in args:
            args['secondary_files'] = dict()
        object_key = combine_two(input_file['uuid'], input_file['object_key'])
        args['input_files'].update({input_file['workflow_argument_name']: {
                                    'bucket_name': input_file['bucket_name'],
                                    'rename': input_file.get('rename', ''),
                                    'unzip': input_file.get('unzip', ''),
                                    'mount': input_file.get('mount', False),
                                    'object_key': object_key}})
        if input_file.get('format_if_extra', ''):
            args['input_files'][input_file['workflow_argument_name']]['format_if_extra'] \
                = input_file.get('format_if_extra')
        else:  # do not add this if the input itself is an extra file
            self.add_secondary_files_to_args(input_file, args)

    def get_extra_file_key_given_input_uuid_and_key(self, inf_uuid, inf_key, fe_map):
        extra_file_keys = []
        not_ready_list = ['uploading', 'to be uploaded by workflow', 'upload failed', 'deleted']
        infile_meta = get_metadata(inf_uuid,
                                   key=self.tibanna_settings.ff_keys,
                                   ff_env=self.tibanna_settings.env,
                                   add_on='frame=object')
        if infile_meta.get('extra_files'):
            infile_format = parse_formatstr(infile_meta.get('file_format'))
            for extra_file in infile_meta.get('extra_files'):
                if 'status' not in extra_file or extra_file.get('status') not in not_ready_list:
                    extra_file_format = parse_formatstr(extra_file.get('file_format'))
                    extra_file_key = get_extra_file_key(infile_format, inf_key, extra_file_format, fe_map)
                    extra_file_keys.append(extra_file_key)
        if len(extra_file_keys) == 0:
            extra_file_keys = None
        return extra_file_keys

    def add_secondary_files_to_args(self, input_file, args):
        """This function adds any existing secondary files to the args field to pass to
        run_task as part of UnicornInput. args (input) is a dictionary and must have
        'input_files' as a key. input_file (input) is an element of input_files list
        in the pony/zebra input json. This function connect to the portal to get metadata."""
        if not args or 'input_files' not in args:
            raise Exception("args must contain key 'input_files'")
        if 'secondary_files'not in args:
            args['secondary_files'] = dict()
        argname = input_file['workflow_argument_name']
        fe_map = FormatExtensionMap(self.tibanna_settings.ff_keys)
        extra_file_keys = run_on_nested_arrays2(input_file['uuid'],
                                                args['input_files'][argname]['object_key'],
                                                self.get_extra_file_key_given_input_uuid_and_key,
                                                fe_map=fe_map)
        if 'rename' in input_file and input_file['rename']:
            extra_file_renames = run_on_nested_arrays2(input_file['uuid'],
                                                       args['input_files'][argname]['rename'],
                                                       self.get_extra_file_key_given_input_uuid_and_key,
                                                       fe_map=fe_map)
        else:
            extra_file_renames = ''
        if extra_file_renames and len(extra_file_renames) > 0:
            extra_file_renames = list(filter(lambda x: x, extra_file_renames))
            if len(extra_file_renames) == 1:
                extra_file_renames = extra_file_renames[0]
        if extra_file_keys and len(extra_file_keys) > 0:
            extra_file_keys = list(filter(lambda x: x, extra_file_keys))
            if len(extra_file_keys) == 1:
                extra_file_keys = extra_file_keys[0]
            if extra_file_keys:
                args['secondary_files'].update({input_file['workflow_argument_name']: {
                                                'bucket_name': input_file['bucket_name'],
                                                'rename': extra_file_renames,
                                                'mount': input_file.get('mount', False),
                                                'object_key': extra_file_keys}})


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


class ProcessedFileMetadataAbstract(SerializableObject):

    # actual values go here for inherited classes
    accession_prefix = 'ABC'

    def __init__(self, uuid=None, accession=None, file_format='',
                 extra_files=None, status='to be uploaded by workflow',
                 md5sum=None, file_size=None, other_fields=None, **kwargs):
        self.uuid = uuid if uuid else str(uuid4())
        self.accession = accession if accession else generate_rand_accession(self.accession_prefix, 'FI')
        self.status = status
        self.file_format = parse_formatstr(file_format)
        self.extra_files = extra_files
        self.md5sum = md5sum
        self.file_size = file_size
        if other_fields:
            for field in other_fields:
                setattr(self, field, other_fields[field])

    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)

    def post(self, key):
        logger.debug("in function post: self.__dict__ = " + str(self.__dict__))
        return post_metadata(self.as_dict(), "file_processed", key=key, add_on='force_md5')

    def patch(self, key, fields=None):
        if fields:
            patch_json = {k: v for k, v in self.as_dict().items() if k in fields}
        else:
            patch_json = self.as_dict()
        logger.debug("patch_json= " + str(patch_json))
        return patch_metadata(patch_json, key=key, add_on='force_md5')

    def add_higlass_uid(self, higlass_uid):
        if higlass_uid:
            self.higlass_uid = higlass_uid


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


def parse_formatstr(file_format_str):
    if not file_format_str:
        return None
    return file_format_str.replace('/file-formats/', '').replace('/', '')


def create_ordinal(a):
    if isinstance(a, list):
        return list(range(1, len(a)+1))
    else:
        return 1


class InputFileForWFRMeta(object):
    def __init__(self, workflow_argument_name=None, value=None, ordinal=None, format_if_extra=None, dimension=None):
        self.workflow_argument_name = workflow_argument_name
        self.value = value
        self.ordinal = ordinal
        if dimension:
            self.dimension = dimension
        if format_if_extra:
            self.format_if_extra = format_if_extra

    def as_dict(self):
        return self.__dict__


def aslist(x):
    if isinstance(x, list):
        return x
    else:
        return [x]


def ensure_list(val):
    if isinstance(val, (list, tuple)):
        return val
    return [val]


def get_extra_file_key(infile_format, infile_key, extra_file_format, fe_map):
    infile_extension = fe_map.get_extension(infile_format)
    extra_file_extension = fe_map.get_extension(extra_file_format)
    if not infile_extension or not extra_file_extension:
        errmsg = "Extension not found for infile_format %s (key=%s)" % (infile_format, infile_key)
        errmsg += "extra_file_format %s" % extra_file_format
        errmsg += "(infile extension %s, extra_file_extension %s)" % (infile_extension, extra_file_extension)
        raise Exception(errmsg)
    return infile_key.replace(infile_extension, extra_file_extension)


class FormatExtensionMap(object):
    def __init__(self, ff_keys):
        try:
            logger.debug("Searching in server : " + ff_keys['server'])
            ffe_all = search_metadata("/search/?type=FileFormat&frame=object", key=ff_keys)
        except Exception as e:
            raise Exception("Can't get the list of FileFormat objects. %s\n" % e)
        self.fe_dict = dict()
        logger.debug("**ffe_all = " + str(ffe_all))
        for k in ffe_all:
            file_format = k['file_format']
            self.fe_dict[file_format] = \
                {'standard_extension': k['standard_file_extension'],
                 'other_allowed_extensions': k.get('other_allowed_extensions', []),
                 'extrafile_formats': k.get('extrafile_formats', [])
                 }

    def get_extension(self, file_format):
        if file_format in self.fe_dict:
            return self.fe_dict[file_format]['standard_extension']
        else:
            return None

    def get_other_extensions(self, file_format):
        if file_format in self.fe_dict:
            return self.fe_dict[file_format]['other_allowed_extensions']
        else:
            return []


class TibannaSettings(SerializableObject):

    def __init__(self, env=None, ff_keys=None, sbg_keys=None, settings=None):
        if not env:
            self.env = None
            self.s3 = None
            self.ff_keys = None
            self.settings = None
        else:
            self.env = env
            self.s3 = s3Utils(env=env)

            if not ff_keys:
                ff_keys = self.s3.get_access_keys('access_key_tibanna')
            self.ff_keys = ff_keys

            if not settings:
                settings = {}
            self.settings = settings

            logger.debug("in TibannaSettings.__init__ : self.as_dict() = " + str(self.as_dict()))
            logger.debug("sysbucket=" + self.s3.sys_bucket)

    def get_reporter(self):
        '''
        a reporter is a generic name for somethign that reports on the results of each step
        of the workflow.  For our immediate purposes this will return ffmetadata object
        (which is a connection to our metadata repository, eventually it should, through
        polymorphism support any type of reporter a user might develop.
        '''
        return None

    def get_runner(self):
        '''
        a runner is an object that implements a set api to run the workflow one step at a time.
        Currently this is sbg for us.
        '''
        return None

    def as_dict(self):
        return {'env': self.env,
                'settings': self.settings}


class FourfrontStarterAbstract(object):

    InputClass = FFInputAbstract
    ProcessedFileMetadata = ProcessedFileMetadataAbstract
    WorkflowRunMetadata = WorkflowRunMetadataAbstract
    output_arg_type_list = ['Output processed file',
                            'Output report file',
                            'Output QC file',
                            'Output to-be-extra-input file']

    def __init__(self, **kwargs):
        self.inp = self.InputClass(**kwargs)
        self.pfs = dict()
        self.ff = None

    def run(self):
        self.create_pfs()
        self.post_pfs()  # must preceed creat_ff
        self.create_ff()
        self.post_ff()
        self.inp.add_args(self.ff)
        self.inp.update(ff_meta=self.ff.as_dict(),
                        pf_meta=[pf.as_dict() for _, pf in self.pfs.items()])
        self.add_meta_to_dynamodb()

    @property
    def tbn(self):
        return self.inp.tibanna_settings

    def get_meta(self, uuid, check_queue=False):
        try:
            return get_metadata(uuid,
                                key=self.tbn.ff_keys,
                                ff_env=self.tbn.env,
                                add_on='frame=object',
                                check_queue=check_queue)
        except Exception as e:
            raise FdnConnectionException(e)

    @property
    def args(self):
        return self.inp.wf_meta.get('arguments', [])

    def arg(self, argname):
        return [arg for arg in self.args if arg.get('workflow_argument_name') == argname][0]

    @property
    def output_args(self):
        return [arg for arg in self.args if arg.get('argument_type') in self.output_arg_type_list]

    @property
    def output_argnames(self):
        return [arg.get('workflow_argument_name') for arg in self.output_args]

    # processed files-related functions
    def create_pfs(self):
        for argname in self.output_argnames:
            pf = self.pf(argname)
            if pf:
                self.pfs.update({argname: pf})

    def post_pfs(self):
        if self.pfs:
            for argname, pf in self.pfs.items():
                if not self.user_supplied_output_files(argname):
                    pf.post(self.tbn.ff_keys)

    def user_supplied_output_files(self, argname=None):
        if not argname:
            return self.inp.output_files
        return [outf for outf in self.inp.output_files if outf.get('workflow_argument_name') == argname]

    def pf_extra_files(self, secondary_file_formats=None, processed_extra_file_use_for=None):
        if not secondary_file_formats:
            return None
        extra_files = []
        for v in secondary_file_formats:
            file_format = parse_formatstr(v)
            extra = {"file_format": file_format}
            if processed_extra_file_use_for:
                if file_format == parse_formatstr(processed_extra_file_use_for['file_format']):
                    extra['use_for'] = processed_extra_file_use_for['use_for']
            extra_files.append(extra)
        return extra_files

    @staticmethod
    def parse_custom_fields(custom_fields, common_fields, argname):
        pf_other_fields = dict()
        if common_fields:
            pf_other_fields.update(common_fields)
        if custom_fields:
            if argname in custom_fields:
                pf_other_fields.update(custom_fields[argname])
            if 'ALL' in custom_fields:
                pf_other_fields.update(custom_fields['ALL'])
        if len(pf_other_fields) == 0:
            pf_other_fields = None
        return pf_other_fields

    def pf(self, argname, **kwargs):
        if self.user_supplied_output_files(argname):
            res = self.get_meta(self.user_supplied_output_files(argname)[0]['uuid'])
            return self.ProcessedFileMetadata(**res)
        arg = self.arg(argname)
        if arg.get('argument_type') != 'Output processed file':
            return None
        if 'argument_format' not in arg:
            raise Exception("file format for processed file must be provided")
        if 'secondary_file_formats' in arg:
            extra_files = self.pf_extra_files(arg.get('secondary_file_formats', []),
                                              arg.get('processed_extra_file_use_for', {}))
        else:
            extra_files = None
        logger.debug("appending %s to pfs" % arg.get('workflow_argument_name'))
        return self.ProcessedFileMetadata(
            file_format=arg.get('argument_format'),
            extra_files=extra_files,
            other_fields=self.parse_custom_fields(self.inp.custom_pf_fields, self.inp.common_fields, argname),
            **kwargs
        )

    # ff (workflowrun)-related functions
    def create_ff(self):
        extra_meta = dict()
        if self.inp.common_fields:
            extra_meta.update(self.inp.common_fields)
        if self.inp.wfr_meta:
            extra_meta.update(self.inp.wfr_meta)
        self.ff = self.WorkflowRunMetadata(
            workflow=self.inp.workflow_uuid,
            awsem_app_name=self.inp.wf_meta['app_name'],
            app_version=self.inp.wf_meta['app_version'],
            input_files=self.create_ff_input_files(),
            tag=self.inp.tag,
            run_url=self.tbn.settings.get('url', ''),
            output_files=self.create_ff_output_files(),
            parameters=self.inp.parameters,
            extra_meta=extra_meta,
            awsem_job_id=self.inp.jobid
        )

    def post_ff(self):
        self.ff.post(self.tbn.ff_keys)

    def create_ff_output_files(self):
        ff_outfile_list = []
        for argname in self.output_argnames:
            ff_outfile_list.append(self.ff_outfile(argname))
        return ff_outfile_list

    def ff_outfile(self, argname):
        arg = self.arg(argname)
        if arg.get('argument_type') == 'Output processed file':
            if argname not in self.pfs:
                raise Exception("processed file objects must be ready before creating ff_outfile")
            try:
                resp = self.get_meta(self.pfs[argname].uuid)
            except Exception as e:
                raise Exception("processed file must be posted before creating ff_outfile: %s" % str(e))
            return WorkflowRunOutputFiles(arg.get('workflow_argument_name'),
                                          arg.get('argument_type'),
                                          arg.get('argument_format', None),
                                          arg.get('secondary_file_formats', None),
                                          resp.get('upload_key', None),
                                          resp.get('uuid', None),
                                          resp.get('extra_files', None)).as_dict()
        else:
            return WorkflowRunOutputFiles(arg.get('workflow_argument_name'),
                                          arg.get('argument_type'),
                                          arg.get('argument_format', None),
                                          arg.get('secondary_file_formats', None)).as_dict()

    def create_ff_input_files(self):
        ff_infile_list = []
        for input_file in self.inp.input_files:
            dim = flatten(create_dim(input_file['uuid']))
            if not dim:  # singlet
                dim = '0'
            uuid = flatten(input_file['uuid'])
            ordinal = create_ordinal(uuid)
            for d, u, o in zip(aslist(dim), aslist(uuid), aslist(ordinal)):
                infileobj = InputFileForWFRMeta(input_file['workflow_argument_name'], u, o,
                                                input_file.get('format_if_extra', ''), d)
                ff_infile_list.append(infileobj.as_dict())
        logger.debug("ff_infile_list is %s" % ff_infile_list)
        return ff_infile_list

    def add_meta_to_dynamodb(self):
        dd = boto3.client('dynamodb')
        try:
            ddres = dd.update_item(
                TableName=DYNAMODB_TABLE,
                Key={
                    DYNAMODB_KEYNAME: {
                        'S': self.inp.jobid
                    }
                },
                AttributeUpdates={
                    'WorkflowRun uuid': {
                        'Value': {
                            'S': self.ff.uuid
                        },
                        'Action': 'PUT'
                    },
                    'env': {
                        'Value': {
                            'S': self.tbn.env
                        },
                        'Action': 'PUT'
                    }
                }
            )
        except Exception as e:
            logger.warning(str(e))
            pass


class QCArgumentInfo(SerializableObject):
    def __init__(self, argument_type, workflow_argument_name, argument_to_be_attached_to, qc_type=None,
                 qc_zipped=False, qc_html=False, qc_json=False, qc_table=False,
                 qc_zipped_html=None, qc_zipped_tables=None, qc_acl='public-read',
                 qc_unzip_from_ec2=False):
        if argument_type != 'Output QC file':
            raise Exception("QCArgument it not Output QC file: %s" % argument_type)
        self.workflow_argument_name = workflow_argument_name
        self.argument_to_be_attached_to = argument_to_be_attached_to
        self.qc_type = qc_type
        self.qc_zipped = qc_zipped
        self.qc_html = qc_html
        self.qc_json = qc_json
        self.qc_table = qc_table
        self.qc_zipped_html = qc_zipped_html
        self.qc_zipped_tables = qc_zipped_tables
        self.qc_acl = qc_acl
        if self.qc_table or self.qc_zipped_tables:
            if not self.qc_type:
                raise Exception("qc_type is required if qc_table or qc_zipped_table")
        self.qc_unzip_from_ec2 = qc_unzip_from_ec2


class InputExtraArgumentInfo(SerializableObject):
    def __init__(self, argument_type, workflow_argument_name, argument_to_be_attached_to,
                 extra_file_use_for=None, **kwargs):
        if argument_type != 'Output to-be-extra-input file':
            raise Exception("InputExtraArgumentInfo is not Output to-be-extra-input file: %s" % argument_type)
        self.workflow_argument_name = workflow_argument_name
        self.argument_to_be_attached_to = argument_to_be_attached_to
        self.extra_file_use_for = extra_file_use_for


class FourfrontUpdaterAbstract(object):
    """This class integrates three different sources of information:
    postrunjson, workflowrun, processed_files,
    and does the final updates necessary"""

    # replace the following with actual classes and values for inherited class
    WorkflowRunMetadata = WorkflowRunMetadataAbstract
    ProcessedFileMetadata = ProcessedFileMetadataAbstract
    default_email_sender = ''
    higlass_buckets = []

    def __init__(self, postrunjson=None, ff_meta=None, pf_meta=None, _tibanna=None,
                 common_fields=None, custom_qc_fields=None,
                 config=None, jobid=None, metadata_only=False, strict=True, **kwargs):
        self.jobid = jobid
        self.config = Config(**config) if config else None
        if not ff_meta:
            ff_meta = {}
        self.ff_meta = self.WorkflowRunMetadata(**ff_meta)
        self._postrunjson = self.get_postrunjson(postrunjson, strict=strict)
        if pf_meta:
            self.pf_output_files = {pf['uuid']: self.ProcessedFileMetadata(**pf) for pf in pf_meta}
        else:
            self.pf_output_files = {}
        # if _tibanna is not set, still proceed with the other functionalities of the class
        self.custom_qc_fields = custom_qc_fields
        self.common_fields = common_fields
        self.tibanna_settings = None
        if _tibanna and 'env' in _tibanna:
            try:
                self.tibanna_settings = TibannaSettings(_tibanna['env'], settings=_tibanna)
            except Exception as e:
                raise TibannaStartException("%s" % e)
        if config and jobid:
            self.ff_meta.awsem_postrun_json = self.get_postrunjson_url(config, jobid, metadata_only)
        self.patch_items = dict()  # a collection of patch jsons (key = uuid)
        self.post_items = dict()  # a collection of patch jsons (key = uuid)

    def get_postrunjson(self, postrunjson_in_input, strict=True):
        if not postrunjson_in_input:
            postrunjson_in_input = {}
        try:
            # it will fail here if it doesn't have Job or config.
            return AwsemPostRunJson(**postrunjson_in_input, strict=strict)
        except Exception:
            postrunjsonfilename = "%s.postrun.json" % self.jobid
            if not does_key_exist(self.config.log_bucket, postrunjsonfilename):
                return None
            postrunjsoncontent = json.loads(read_s3(self.config.log_bucket, postrunjsonfilename))
            return AwsemPostRunJson(**postrunjsoncontent)

    @property
    def postrunjson(self):
        if self._postrunjson:
            return self._postrunjson
        else:
            postrunjsonfilename = "%s.postrun.json" % self.jobid
            postrunjson_location = "https://s3.amazonaws.com/%s/%s" % (self.config.log_bucket, postrunjsonfilename)
            raise Exception("Postrun json not found at %s" % postrunjson_location)

    def create_wfr_qc(self):
        qc_item = self.create_qc_template()
        qc_item['url'] = METRICS_URL(self.config.log_bucket, self.jobid)
        self.update_post_items(qc_item['uuid'], qc_item, 'QualityMetricWorkflowrun')
        self.ff_meta.quality_metric = qc_item['uuid']

    def handle_success(self):
        # update run status in metadata first
        self.ff_meta.run_status = 'complete'
        self.patch_ffmeta()
        # send a notification email
        if self.config.email:
            self.send_notification_email(self.tibanna_settings.settings['run_name'],
                                         self.jobid,
                                         self.ff_meta.run_status,
                                         self.tibanna_settings.settings['url'])

    def handle_error(self, err_msg=''):
        # update run status in metadata first
        self.ff_meta.run_status = 'error'
        self.ff_meta.description = err_msg
        self.patch_ffmeta()
        # send a notification email before throwing error
        if self.config.email:
            self.send_notification_email(self.tibanna_settings.settings['run_name'],
                                         self.jobid,
                                         self.ff_meta.run_status,
                                         self.tibanna_settings.settings['url'])
        # raise error
        raise Exception(err_msg)

    @property
    def app_name(self):
        try:
            return self.ff_meta.awsem_app_name
        except Exception:
            try:
                return self.postrunjson.Job.App.App_name
            except Exception:
                raise Exception("Cannot retrieve app_name")

    # postrunjson-related basic functionalities
    @property
    def awsem_output_files(self):
        """this used to be called output_info"""
        return self.postrunjson.Job.Output.output_files

    @property
    def awsem_input_files(self):
        return self.postrunjson.Job.Input.Input_files_data

    # workflowrun-ralated basic functionalities
    @property
    def ff_output_files(self):
        """this used to be called output_files_meta"""
        return self.ff_meta.output_files

    @property
    def ff_input_files(self):
        return self.ff_meta.input_files

    @property
    def ff_files(self):
        return self.ff_input_files + self.ff_output_files

    def ff_output_file(self, argname=None, pf_uuid=None):
        if argname:
            pass
        elif pf_uuid:
            argname = self.pf2argname(pf_uuid)
        else:
            raise Exception("Either argname or pf_uuid must be provided")
        for v in self.ff_output_files:
            if argname == v['workflow_argument_name']:
                return v
        return None

    def ff_file(self, argname):
        for v in self.ff_files:
            if argname == v['workflow_argument_name']:
                return v
        return None

    @property
    def input_argnames(self):
        return list(self.awsem_input_files.keys())

    @property
    def output_argnames(self):
        return list(self.awsem_output_files.keys())

    def output_type(self, argname):
        for x in self.ff_output_files:
            if x['workflow_argument_name'] == argname:
                return x['type']
        return None

    # processed file-ralated basic functionalities
    def pf(self, pf_uuid):
        return self.pf_output_files.get(pf_uuid, None)

    def pf2argname(self, pf_uuid):
        for argname in self.output_argnames:
            if pf_uuid in self.pf_uuids(argname):
                return argname
        return None

    def pf_uuids(self, argname):
        uuids = []
        for of in self.ff_output_files:
            if argname == of['workflow_argument_name']:
                if of['type'] == 'Output processed file':
                    uuids.append(of['value'])
        return uuids

    def pf_extra_file(self, pf_uuid, file_format):
        for extra in self.pf(pf_uuid).extra_files:
            if cmp_fileformat(extra['file_format'], file_format):
                return extra
        return None

    # metadata object-related basic functionalities
    def get_metadata(self, id):
        return get_metadata(id,
                            key=self.tibanna_settings.ff_keys,
                            ff_env=self.tibanna_settings.env,
                            add_on='frame=object',
                            check_queue=True)

    def file_items(self, argname):
        """get the actual metadata file items for a specific argname"""
        items_list = []
        for acc in self.accessions(argname):
            try:
                res = self.get_metadata(acc)
            except Exception as e:
                raise FdnConnectionException("Can't get metadata for accession %s: %s" % (acc, str(e)))
            items_list.append(res)
        return items_list

    @property
    def workflow(self):
        try:
            res = self.get_metadata(self.ff_meta.workflow)
        except Exception as e:
            raise FdnConnectionException("Can't get metadata for workflow %s: %s" % (self.ff_meta.workflow, str(e)))
        return res

    def workflow_arguments(self, argument_types=None):
        if argument_types:
            res = []
            for arg in self.workflow['arguments']:
                if arg["argument_type"] in argument_types:
                    res.append(arg)
            return res
        else:
            return self.workflow['arguments']

    @property
    def workflow_qc_arguments(self):
        """dictionary of QCArgumentInfo object list as value and
        argument_to_be_attached_to as key"""
        wqcas = dict()
        qc_args = [QCArgumentInfo(**qc) for qc in self.workflow_arguments('Output QC file')]
        for arg in set([_.argument_to_be_attached_to for _ in qc_args]):
            wqcas.update({arg: [_ for _ in qc_args if _.argument_to_be_attached_to == arg]})
        return wqcas

    @property
    def workflow_input_extra_arguments(self):
        """dictionary of InputExtraArgumentInfo object list as value and
        argument_to_be_attached_to as key"""
        ie_args = [InputExtraArgumentInfo(**ie) for ie in self.workflow_arguments('Output to-be-extra-input file')]
        ie_args_per_attach = dict()
        for iearg in ie_args:
            if iearg.argument_to_be_attached_to not in ie_args_per_attach:
                ie_args_per_attach[iearg.argument_to_be_attached_to] = []
            ie_args_per_attach[iearg.argument_to_be_attached_to].append(iearg)
        return ie_args_per_attach

    # patch/post-related functionalities
    def post_all(self):
        logger.info("posting metadata : %s" % str(self.post_items))
        for schema, v in self.post_items.items():
            for item in v:
                logger.info("posting metadata %s to schema %s" % (str(v[item]), schema))
                try:
                    res = post_metadata(v[item], schema,
                                        key=self.tibanna_settings.ff_keys,
                                        ff_env=self.tibanna_settings.env,
                                        add_on='force_md5')
                    logger.debug("response=" + str(res))
                except Exception as e:
                    raise e

    def patch_all(self):
        for item_id, item in self.patch_items.items():
            patch_metadata(item, item_id,
                           key=self.tibanna_settings.ff_keys,
                           ff_env=self.tibanna_settings.env,
                           add_on='force_md5')

    def patch_ffmeta(self):
        try:
            self.ff_meta.patch(key=self.tibanna_settings.ff_keys)
        except Exception as e:
            raise FdnConnectionException("Failed to update ff_meta %s" % str(e))

    def update_patch_items(self, uuid, item):
        if uuid in self.patch_items:
            self.patch_items[uuid].update(item)
        else:
            self.patch_items.update({uuid: item})

    def update_post_items(self, uuid, item, schema):
        if schema not in self.post_items:
            self.post_items[schema] = dict()
        if uuid in self.post_items[schema]:
            self.post_items[schema][uuid].update(item)
        else:
            self.post_items[schema].update({uuid: item})
            if 'uuid' not in self.post_items[schema][uuid]:
                # add uuid to post item itself
                self.post_items[schema][uuid]['uuid'] = uuid

    def delete_patch_items(self, uuid):
        if uuid in self.patch_items:
            del self.patch_items[uuid]
        else:
            logger.warning("attempt to delete patch item that does not exist")
            pass

    def add_to_pf_patch_items(self, pf_uuid, fields):
        """add entries from pf object to patch_items for a later pf patch"""
        if not isinstance(fields, list):
            field_val = self.pf(pf_uuid).__getattribute__(fields)
            if field_val:
                self.update_patch_items(pf_uuid, {fields: field_val})
        else:
            for f in fields:
                self.add_to_pf_patch_items(pf_uuid, f)

    # s3-related functionalities
    @property
    def outbucket(self):
        return self.postrunjson.Job.Output.output_bucket_directory

    def bucket(self, argname=None, pf_uuid=None):
        if argname:
            pass
        elif pf_uuid:
            argname = self.pf2argname(pf_uuid)
        else:
            raise Exception("At least argname or pf_uuid must be provided to get md5sum")
        if argname in self.awsem_output_files:
            return self.outbucket
        elif argname in self.awsem_input_files:
            return self.awsem_input_files[argname].dir_

    def s3(self, argname):
        return s3Utils(self.bucket(argname), self.bucket(argname), self.bucket(argname))

    def read(self, argname):
        """This function is useful for reading md5 report of qc report"""
        return self.s3(argname).read_s3(self.file_key(argname)).decode('utf-8', 'backslashreplace')

    def s3_file_size(self, argname, secondary_format=None):
        return self.s3(argname).get_file_size(self.file_key(argname, secondary_format=secondary_format),
                                              self.bucket(argname))

    # get file features
    def md5sum(self, argname=None, pf_uuid=None, secondary_key=None):
        if argname:
            pass
        elif pf_uuid:
            argname = self.pf2argname(pf_uuid)
        else:
            raise Exception("At least argname or pf_uuid must be provided to get md5sum")
        if secondary_key:
            for sf in self.awsem_output_files[argname].secondaryFiles:
                if sf.target == secondary_key:
                    return sf.md5sum
            return None
        return self.awsem_output_files[argname].md5sum

    def filesize(self, argname=None, pf_uuid=None, secondary_key=None):
        if argname:
            pass
        elif pf_uuid:
            argname = self.pf2argname(pf_uuid)
        else:
            raise Exception("At least argname or pf_uuid must be provided to get filesize")
        if secondary_key:
            for sf in self.awsem_output_files[argname].secondaryFiles:
                if sf.target == secondary_key:
                    return sf.size
            return None
        return self.awsem_output_files[argname].size

    def file_format(self, argname, secondary_key=None):
        for pf in self.ff_output_files:
            if pf['workflow_argument_name'] == argname:
                if secondary_key:
                    if 'extra_files' in pf:
                        for pfextra in pf['extra_files']:
                            if pfextra['upload_key'] == secondary_key:
                                return parse_formatstr(pfextra['file_format'])
                        logger.debug("No extra file matching key %s" % secondary_key)
                        return None
                    logger.debug("No extra file for argname %s" % argname)
                    return None
                else:
                    return pf['format']
        logger.debug("No workflow run output file matching argname %s" % argname)
        return None

    def all_extra_formats(self, argname=None, pf_uuid=None):
        """get a list of file formats of all extra files of given argname or pf"""
        outfile = self.ff_output_file(argname=argname, pf_uuid=pf_uuid)
        extra_files = outfile.get('extra_files', [])
        if not extra_files:
            extra_files = []  # make it iterable
        return [ef.get('file_format', '') for ef in extra_files]

    def all_extra_files(self, argname=None, pf_uuid=None):
        """returns extra_files field of workflowrun given argname of pp_uuid
        the return value is a list of dictionaries.
        """
        if argname:
            pass
        elif pf_uuid:
            argname = self.pf2argname(pf_uuid)
        else:
            raise Exception("Either argname or pf_uuid must be provided")
        ffout = self.ff_output_file(argname)
        extrafiles = ffout.get('extra_files', [])
        return extrafiles if extrafiles else []

    def file_key(self, argname=None, pf_uuid=None, secondary_format=None):
        """returns file object_key on the bucket, either through argname or
        processed file uuid (pf_uuid). To get the file key of a secondary file,
        use secondary_format - this option is valid only with pf_uuid.
        Getting a file key through argname is mainly for getting non-processed files
        like md5 or qc reports"""
        if argname:
            if argname in self.awsem_output_files:
                return self.awsem_output_files[argname].target
            elif argname in self.awsem_input_files:
                return self.awsem_input_files[argname].path
        elif pf_uuid:
            of = self.ff_output_file(pf_uuid=pf_uuid)
            if of:
                if secondary_format:
                    for extra in of['extra_files']:
                        if cmp_fileformat(extra['file_format'], secondary_format):
                            return extra['upload_key']
                    raise Exception("no extra file with format %s" % secondary_format)
                else:
                    return of['upload_key']
        else:
            raise Exception("Either argname or pf must be provided to get a file_key")

    def accessions(self, argname):
        accessions = []
        # argname is output
        v = self.ff_output_file(argname)
        if v and v['type'] == 'Output processed file':
            file_name = v['upload_key'].split('/')[-1]
            accession = file_name.split('.')[0].strip('/')
            accessions.append(accession)
        # argname is input
        else:
            if argname not in self.awsem_input_files:
                return []
            paths = copy.deepcopy(self.awsem_input_files[argname].path)
            if not isinstance(paths, list):
                paths = [paths]
            for path in paths:
                file_name = path.split('/')[-1]
                accession = file_name.split('.')[0].strip('/')
                accessions.append(accession)
                # do not break - there may be multiple entries for the same argname
        return accessions

    def format_if_extras(self, argname):
        format_if_extras = []
        for v in self.ff_files:
            if argname == v['workflow_argument_name'] and 'format_if_extra' in v:
                format_if_extras.append(v['format_if_extra'])
        return format_if_extras

    def status(self, argname=None, pf_uuid=None):
        """check file existence as status either per argname or per pf object"""
        if argname:
            key = self.file_key(argname)
        elif pf_uuid:
            key = self.file_key(pf_uuid=pf_uuid)
            argname = self.pf2argname(pf_uuid)
        else:
            raise Exception("Either argname or pf_uuid must be provided to get status.")
        if not isinstance(key, list):
            key = [key]
        for k in key:
            try:
                exists = self.s3(argname).does_key_exist(k, self.bucket(argname))
                if not exists:
                    return "FAILED"
            except Exception:
                return "FAILED"
        return "COMPLETED"

    def genome_assembly(self, pf_uuid):
        if hasattr(self.pf(pf_uuid), 'genome_assembly'):
            return self.pf(pf_uuid).genome_assembly
        else:
            return None

    # update functions for PF
    def update_all_pfs(self):
        if self.pf_output_files:
            for pf_uuid in self.pf_output_files:
                self.update_pf(pf_uuid)

    def update_pf(self, pf_uuid):
        if self.status(pf_uuid=pf_uuid) == 'COMPLETED':
            self.add_updates_to_pf(pf_uuid)
            self.add_updates_to_pf_extra(pf_uuid)
            self.add_higlass_to_pf(pf_uuid)

    def add_updates_to_pf(self, pf_uuid):
        """update md5sum, file_size, status for pf itself"""
        # update the class object
        self.pf(pf_uuid).md5sum = self.md5sum(pf_uuid=pf_uuid)
        self.pf(pf_uuid).file_size = self.filesize(pf_uuid=pf_uuid)
        self.pf(pf_uuid).status = 'uploaded'
        # prepare for fourfront patch
        self.add_to_pf_patch_items(pf_uuid, ['md5sum', 'file_size', 'status'])

    def add_updates_to_pf_extra(self, pf_uuid):
        """update md5sum, file_size, status for extra file"""
        for extra in self.all_extra_files(pf_uuid=pf_uuid):
            pf_extra = self.pf_extra_file(pf_uuid, extra['file_format'])
            extra_key = extra['upload_key']
            # update the class object
            pf_extra['md5sum'] = self.md5sum(pf_uuid=pf_uuid, secondary_key=extra_key)
            pf_extra['file_size'] = self.filesize(pf_uuid=pf_uuid, secondary_key=extra_key)
            pf_extra['status'] = 'uploaded'
        # prepare for fourfront patch
        self.add_to_pf_patch_items(pf_uuid, 'extra_files')

    def add_higlass_to_pf(self, pf_uuid):
        key = None
        higlass_uid = None
        for extra_format in self.all_extra_formats(pf_uuid=pf_uuid) + [None]:
            hgcf = match_higlass_config(self.pf(pf_uuid).file_format, extra_format)
            if hgcf:
                key = self.file_key(pf_uuid=pf_uuid, secondary_format=extra_format)
                break
        if hgcf:
            higlass_uid = self.register_to_higlass(self.tibanna_settings,
                                                   self.bucket(pf_uuid=pf_uuid),
                                                   key,
                                                   hgcf['file_type'],
                                                   hgcf['data_type'],
                                                   self.genome_assembly(pf_uuid))
        if higlass_uid:
            # update the class object
            self.pf(pf_uuid).higlass_uid = higlass_uid
            # prepare for fourfront patch
            self.add_to_pf_patch_items(pf_uuid, 'higlass_uid')

    # update functions for all input extras
    def update_input_extras(self):
        """go through all input arguments that have an extra file to be attached
        and for each create a patch_item and add to patch_items.
        This allows multiple extra output files corresponding to different input
        arguments, or same input argument with different formats
        """
        for ie_arg, ie_list in self.workflow_input_extra_arguments.items():
            # ie_arg is the input arg to attach the extra file
            # ie_list is a list of InputExtraARgumentInfo class objects
            ip_items = self.file_items(ie_arg)
            if len(ip_items) > 1:  # do not allow input array in this case
                raise Exception("ambiguous input for input extra update")
            ip = ip_items[0]
            if 'extra_files' not in ip:
                raise Exception("inconsistency - extra file metadata deleted during workflow run?")
            for ie in ie_list:
                matching_extra = None
                output_extra_format = self.file_format(ie.workflow_argument_name)
                for extra in ip['extra_files']:
                    if cmp_fileformat(extra['file_format'], output_extra_format):
                        matching_extra = extra
                        break
                if not matching_extra:
                    raise Exception("inconsistency - extra file metadata deleted during workflow run?")
                if self.status(ie.workflow_argument_name) == 'COMPLETED':
                    matching_extra['md5sum'] = self.md5sum(ie.workflow_argument_name)
                    matching_extra['filesize'] = self.filesize(ie.workflow_argument_name)
                    matching_extra['status'] = 'uploaded'
                    if ie.extra_file_use_for:
                        matching_extra['use_for'] = ie.extra_file_use_for
                else:
                    matching_extra['status'] = "upload failed"
                # higlass registration
                hgcf = match_higlass_config(ip['file_format'], output_extra_format)
                higlass_uid = None
                if hgcf:
                    # register extra file not the original input file
                    higlass_uid = self.register_to_higlass(self.tibanna_settings,
                                                           self.bucket(ie.workflow_argument_name),
                                                           self.file_key(ie.workflow_argument_name),
                                                           hgcf['file_type'],
                                                           hgcf['data_type'],
                                                           ip.get('genome_assembly', None))
                if higlass_uid:
                    self.update_patch_items(ip['uuid'], {'higlass_uid': higlass_uid})
            self.update_patch_items(ip['uuid'], {'extra_files': ip['extra_files']})

    def _update_a_qc(self, qc, qc_target_accession, qc_schema, qc_type, qc_item_uuid):
        """Internal update function for qc per workflow qc argument"""
        qc_item = dict()
        qc_bucket = self.bucket(qc.workflow_argument_name)
        qc_key = self.file_key(qc.workflow_argument_name)
        if qc.qc_zipped and qc.qc_unzip_from_ec2:
            qc_url = None
        elif qc.qc_zipped and not qc.qc_unzip_from_ec2:
            if qc.qc_zipped_tables:
                return_unzipped_qc_data = True
            else:
                return_unzipped_qc_data = False
            unzipped_qc_data = self.unzip_qc_data(qc, qc_key, qc_target_accession, return_unzipped_qc_data)
            if qc.qc_zipped_tables:
                qcz_datafiles = []
                for qcz in qc.qc_zipped_tables:
                    qcz_datafiles.extend(filter(lambda x: x.endswith(qcz), unzipped_qc_data))
                if qcz_datafiles:
                    data_to_parse = [unzipped_qc_data[df]['data'] for df in qcz_datafiles]
                    qc_meta_from_zip = self.parse_qc_table(data_to_parse, qc_schema)
                    qc_item.update(qc_meta_from_zip)
            # if there is an html, add qc_url for the html
            if qc.qc_zipped_html:
                target_html = qc_target_accession + '/' + qc.qc_zipped_html
                qc_url = 'https://s3.amazonaws.com/' + qc_bucket + '/' + target_html
            else:
                qc_url = None
        else:
            # if there is an html, add qc_url for the html
            if qc.qc_html:
                target_html = qc_target_accession + '/qc_report.html'
                qc_url = 'https://s3.amazonaws.com/' + qc_bucket + '/' + target_html
            else:
                qc_url = None
            data = self.read(qc.workflow_argument_name)
            if qc.qc_html:
                self.s3(qc.workflow_argument_name).s3_put(data.encode(),
                                                          target_html,
                                                          acl='public-read')
            elif qc.qc_json:
                qc_item.update(self.parse_qc_json([data]))
            elif qc.qc_table:
                qc_item.update(self.parse_qc_table([data], qc_schema))
        if qc_url:
            qc_item.update({'url': qc_url})
        if self.custom_qc_fields:
            qc_item.update(self.custom_qc_fields)
        if qc_type:
            self.ff_output_file(qc.workflow_argument_name)['value_qc'] = qc_item_uuid
        return qc_item

    def _update_qc_per_type(self, qc_type, qc_list, qc_target_accession):
        """Internal update function for QC for a given type
        returns QC metadata item to post in dictionary form"""
        qc_list_of_type = [_ for _ in qc_list if _.qc_type == qc_type]
        if qc_type:
            qc_schema = self.qc_schema(qc_type)
        else:
            qc_schema = None
        qc_item_to_be = self.create_qc_template()
        for qc in qc_list_of_type:
            qc_item_to_be.update(self._update_a_qc(qc, qc_target_accession, qc_schema,
                                                   qc_type, qc_item_to_be['uuid']))
        return qc_item_to_be

    # update functions for QC
    def update_qc(self):
        for qc_arg, qc_list in self.workflow_qc_arguments.items():
            # qc_arg is the argument (either input or output) to attach the qc file
            # qc_list is a list of QCArgumentInfo class objects
            qc_target_accessions = self.accessions(qc_arg)
            if not qc_target_accessions:
                raise Exception("QC target %s does not exist" % qc_arg)
            # The first target accession is use in the url for the report files
            qc_target_accession = qc_target_accessions[0]
            qc_types = set([_.qc_type for _ in qc_list])
            qc_types_no_none = set([_.qc_type for _ in qc_list if _])
            # create quality_metric_qclist if >1 qc types for a given qc_arg
            if len(qc_types_no_none) > 1:
                qclist_item_to_be = self.create_qc_template()
                qclist_item_to_be['qc_list'] = []
            else:
                qclist_item_to_be = None
            for qc_type in qc_types:
                qc_item_to_be = self._update_qc_per_type(qc_type, qc_list, qc_target_accession)
                if qc_type:
                    self.update_post_items(qc_item_to_be['uuid'], qc_item_to_be, qc_type)
                    if qclist_item_to_be:
                        # the uuids and types are in the same order
                        qclist_item_to_be['qc_list'].append({'qc_type': qc_type, 'value': qc_item_to_be['uuid']})

            # add quality_metric_qclist in the post items
            if qclist_item_to_be:
                self.update_post_items(qclist_item_to_be['uuid'], qclist_item_to_be, 'quality_metric_qclist')
            # allowing multiple input files to point to the same qc_item_to_be.
            for t_acc in qc_target_accessions:
                if qc_type:
                    if qclist_item_to_be:
                        self.patch_qc(t_acc, qclist_item_to_be['uuid'], 'quality_metric_qclist',
                                      qclist_array=qclist_item_to_be['qc_list'])
                    else:
                        self.patch_qc(t_acc, qc_item_to_be['uuid'], qc_type)

    def patch_qc(self, qc_target_accession, qc_uuid, qc_type, qclist_array=None):
        try:
            res = get_metadata(qc_target_accession,
                               key=self.tibanna_settings.ff_keys,
                               ff_env=self.tibanna_settings.env,
                               add_on='frame=object',
                               check_queue=True)
        except Exception as e:
            raise FdnConnectionException(e)
        if 'quality_metric' not in res:  # first qc metric for this file
            self.update_patch_items(qc_target_accession, {'quality_metric': qc_uuid})
        else:
            existing_qctype = res['quality_metric'].split('/')[1].replace('-', '_'). \
                              replace('quality_metrics', 'quality_metric')
            existing_qc_uuid = res['quality_metric'].split('/')[2]
            logger.debug("existing qc=" + res['quality_metric'] + ' ' + existing_qctype)
            logger.debug("new qc=" + qc_uuid + ' ' + qc_type)
            if qc_type == 'quality_metric_qclist':
                if qclist_array:
                    raise Exception("qclist_array must be provided to function patch_qc if qc_type is qclist")
                child_qc_uuids = [_['value'] for _ in qclist_array]
                child_qc_types = [_['qc_type'] for _ in qclist_array]
                if existing_qctype in child_qc_types:  # if existing qc metric is of the same type, overwrite.
                    self.update_patch_items(qc_target_accession, {'quality_metric': qc_uuid})
                elif existing_qctype == 'quality_metric_qclist':
                    # merge the two qclist - use the existing one and delete the new one
                    # we assume that the same qc type occurs only once per qc list
                    # and so a new workflow run can update the one with the same qc type
                    self.delete_patch_items(qc_uuid)
                    existing_qc_meta = get_metadata(existing_qc_uuid,
                                                    key=self.tibanna_settings.ff_keys,
                                                    ff_env=self.tibanna_settings.env,
                                                    add_on='frame=object',
                                                    check_queue=True)
                    existing_child_qc_types = [qc['qc_type'] for qc in existing_qc_meta['qc_list']]
                    for t, u in zip(child_qc_types, child_qc_uuids):
                        if t in existing_child_qc_types:
                            for i, qc in enumerate(existing_qc_meta['qc_list']):
                                if qc['qc_type'] == t:
                                    existing_qc_meta['qc_list'][i]['value'] = u  # just replace the one of the same type
                                    break
                        else:
                            existing_qc_meta['qc_list'].append({'qc_type': t, 'value': u})  # add a new type
                    self.update_patch_items(existing_qc_meta['uuid'], {'qc_list': existing_qc_meta['qc_list']})
                else:
                    # add the new one to the qc list
                    qclist_array.append({'qc_type': existing_qctype, 'value': existing_qc_uuid})
                    self.update_patch_items(qc_uuid, {'qc_list': qclist_array})
            else:
                if existing_qctype == qc_type:  # if existing qc metric is of the same type, overwrite.
                    self.update_patch_items(qc_target_accession, {'quality_metric': qc_uuid})
                elif existing_qctype == 'quality_metric_qclist':
                    # we assume that the same qc type occurs only once per qc list
                    # and so a new workflow run can update the one with the same qc type
                    existing_qc_meta = get_metadata(existing_qc_uuid,
                                                    key=self.tibanna_settings.ff_keys,
                                                    ff_env=self.tibanna_settings.env,
                                                    add_on='frame=object',
                                                    check_queue=True)
                    if qc_type not in [qc['qc_type'] for qc in existing_qc_meta['qc_list']]:
                        existing_qc_meta['qc_list'].append({'qc_type': qc_type, 'value': qc_uuid})
                        self.update_patch_items(existing_qc_meta['uuid'], {'qc_list': existing_qc_meta['qc_list']})
                    else:
                        for i, qc in enumerate(existing_qc_meta['qc_list']):
                            if qc['qc_type'] == qc_type:
                                existing_qc_meta['qc_list'][i]['value'] = qc_uuid
                                break
                        self.update_patch_items(existing_qc_meta['uuid'], {'qc_list': existing_qc_meta['qc_list']})
                else:
                    # new qc type is being added - create a qc list and move the existing qc to the qc list and
                    # add the new one to the qc list
                    new_qclist_object = self.create_qc_template()
                    new_qclist_object['qc_list'] = [{'qc_type': existing_qctype, 'value': existing_qc_uuid},
                                                    {'qc_type': qc_type, 'value': qc_uuid}]
                    self.update_post_items(new_qclist_object['uuid'], new_qclist_object, 'quality_metric_qclist')
                    self.update_patch_items(qc_target_accession, {'quality_metric': new_qclist_object['uuid']})

    def qc_schema(self, qc_schema_name):
        try:
            # schema. do not need to check_queue
            res = get_metadata("profiles/" + qc_schema_name + ".json",
                               key=self.tibanna_settings.ff_keys,
                               ff_env=self.tibanna_settings.env)
            return res.get('properties')
        except Exception as e:
            err_msg = "Can't get profile for qc schema %s: %s" % (qc_schema_name, str(e))
            raise FdnConnectionException(err_msg)

    def parse_qc_table(self, data_list, qc_schema):
        qc_json = dict()

        def parse_item(name, value):
            """Add item to qc_json if it's in the schema"""
            qc_type = qc_schema.get(name, {}).get('type', None)
            if qc_type == 'string':
                qc_json.update({name: str(value)})
            elif qc_type == 'number':
                qc_json.update({name: number(value.replace(',', ''))})

        for data in data_list:
            for line in data.split('\n'):
                items = line.strip().split('\t')
                # flagstat qc handling - e.g. each line could look like "0 + 0 blah blah blah"
                space_del = line.strip().split(' ')
                flagstat_items = [' '.join(space_del[0:3]), ' '.join(space_del[3:])]
                try:
                    parse_item(items[0], items[1])
                    parse_item(items[1], items[0])
                    parse_item(flagstat_items[1], flagstat_items[0])
                except IndexError:  # pragma: no cover
                    # maybe a blank line or something
                    pass
        return qc_json

    def parse_qc_json(self, data_list):
        qc_json = dict()
        for data in data_list:
            qc_json.update(json.loads(data))
        return qc_json

    def create_qc_template(self):
        qc_item = {'uuid': str(uuid4())}
        if self.common_fields:
            qc_item.update(self.common_fields)
        return qc_item

    def unzip_qc_data(self, qc, qc_key, target_accession, return_unzipped_qc_data=True):
        """qc is a QCArgumentInfo object.
        if qc is zipped, unzip it, put the files to destination s3,
        and store the content and target s3 key to a dictionary and return.
        """
        if qc.qc_zipped:
            unzipped_data = self.s3(qc.workflow_argument_name).unzip_s3_to_s3(qc_key,
                                                                              target_accession,
                                                                              acl=qc.qc_acl,
                                                                              store_results=return_unzipped_qc_data)
            if return_unzipped_qc_data:
                for k, v in unzipped_data.items():
                    v['data'] = v['data'].decode('utf-8', 'backslashreplace')
                return unzipped_data
            else:
                return None
        else:
            return None

    # rna-strandedness (hardcode it for now - later we generalize along with md5)
    def update_rna_strandedness(self):
        if self.app_name != 'rna-strandedness':
            return
        report_arg = self.output_argnames[0]  # assume one output arg
        if self.ff_output_file(report_arg)['type'] != 'Output report file':
            return
        if self.status(report_arg) == 'FAILED':
            self.ff_meta.run_status = 'error'
            return
        sense, antisense = self.parse_rna_strandedness_report(self.read(report_arg))
        input_arg = 'fastq'
        input_meta = self.file_items(input_arg)[0]  # assume one input file
        patch_content = {'beta_actin_sense_count': sense,
                         'beta_actin_antisense_count': antisense}
        self.update_patch_items(input_meta['uuid'], patch_content)

    @classmethod
    def parse_rna_strandedness_report(cls, read):
        """parses md5 report file content and returns md5, content_md5"""
        strandedness_array = read.rstrip('\n').split('\n')
        if not strandedness_array:
            raise Exception("rna-strandedness report has no content.")
        elif len(strandedness_array) != 2:
            raise Exception("rna-strandedness report must have exactly two lines.")
        else:
            return int(strandedness_array[0]), int(strandedness_array[1])

    # fastq_first_line
    def update_fastq_first_line(self):
        if self.app_name != 'fastq-first-line':
            return
        report_arg = self.output_argnames[0]  # assume one output arg
        if self.ff_output_file(report_arg)['type'] != 'Output report file':
            return
        if self.status(report_arg) == 'FAILED':
            self.ff_meta.run_status = 'error'
            return
        first_line = self.parse_fastq_first_line_report(self.read(report_arg))
        input_arg = 'fastq'
        input_meta = self.file_items(input_arg)[0]  # assume one input file
        patch_content = {'file_first_line': first_line}
        self.update_patch_items(input_meta['uuid'], patch_content)

    @classmethod
    def parse_fastq_first_line_report(cls, read):
        """parses fastq_first_line report file content and returns the content"""
        fastq_first_line_content = read.rstrip('\n').split('\n')
        if not fastq_first_line_content:
            raise Exception("fastq_first_line report has no content.")
        elif len(fastq_first_line_content) != 1:
            raise Exception("fastq_first_line report must have exactly one line.")
        else:
            return fastq_first_line_content[0]

    # bam restriction enzyme check
    def update_file_processed_format_re_check(self):
        if self.app_name != 're_checker_workflow':
            return
        report_arg = self.output_argnames[0]  # assume one output arg
        if self.ff_output_file(report_arg)['type'] != 'Output report file':
            return
        if self.status(report_arg) == 'FAILED':
            self.ff_meta.run_status = 'error'
            return
        percent = self.parse_re_check(self.read(report_arg))
        input_arg = 'bamfile'
        input_meta = self.file_items(input_arg)[0]  # assume one input file
        patch_content = {'percent_clipped_sites_with_re_motif': percent}
        self.update_patch_items(input_meta['uuid'], patch_content)

    @classmethod
    def parse_re_check(cls, read):
        """parses output of re checker to return percent clipped sites with re motif"""
        re_check_content = read.rstrip('\n').split('\n')
        if not re_check_content:
            raise Exception("bam restriction enzyme check output has no content")
        elif len(re_check_content) != 1:
            raise Exception("bam restriction enzyme check output must have exactly one line")
        content = re_check_content[0].split()
        if content[0] != "clipped-mates":
            logger.debug("parse_re_check content= " + str(content[0]))
            raise Exception("bam restriction enzyme check contains unexpected content")
        else:
            return float(content[4])

    # md5 report
    def update_md5(self):
        if self.app_name != 'md5':
            return
        md5_report_arg = self.output_argnames[0]  # assume one output arg
        if self.ff_output_file(md5_report_arg)['type'] != 'Output report file':
            return
        if self.status(md5_report_arg) == 'FAILED':
            self.ff_meta.run_status = 'error'
            return
        md5, content_md5 = self.parse_md5_report(self.read(md5_report_arg))
        input_arg = self.input_argnames[0]  # assume one input arg
        input_meta = self.file_items(input_arg)[0]  # assume one input file

        def process(meta):
            md5_patch = dict()
            md5_old, content_md5_old = self.get_existing_md5(meta)

            def compare_and_update_md5(new, old, fieldname):
                if new:
                    if old:
                        if new != old:
                            raise Exception("%s not matching the original one" % fieldname)
                    else:
                        return {fieldname: new}
                return {}

            md5_patch.update(compare_and_update_md5(md5, md5_old, 'md5sum'))
            md5_patch.update(compare_and_update_md5(content_md5, content_md5_old, 'content_md5sum'))
            return md5_patch

        matching_extra = None
        for extra_format in self.format_if_extras(input_arg):
            for ind, extra in enumerate(input_meta['extra_files']):
                if cmp_fileformat(extra['file_format'], extra_format):
                    matching_extra = extra
                    matching_extra_ind = ind
                    break
            if matching_extra:
                break
        if matching_extra:
            patch_content = input_meta['extra_files']
            patch_content[matching_extra_ind].update(process(matching_extra))
            secondary_format = matching_extra['file_format']
            patch_content[matching_extra_ind]['file_size'] = \
                self.s3_file_size(input_arg, secondary_format=secondary_format)
            patch_content[matching_extra_ind]['status'] = 'uploaded'
            self.update_patch_items(input_meta['uuid'], {'extra_files': patch_content})
        else:
            patch_content = process(input_meta)
            patch_content['file_size'] = self.s3_file_size(input_arg)
            patch_content['status'] = 'uploaded'
            self.update_patch_items(input_meta['uuid'], patch_content)

    def parse_md5_report(self, read):
        """parses md5 report file content and returns md5, content_md5"""
        md5_array = read.split('\n')
        if not md5_array:
            raise Exception("md5 report has no content")
        if len(md5_array) == 1:
            return None, md5_array[0]
        elif len(md5_array) > 1:
            return md5_array[0], md5_array[1]

    def get_existing_md5(self, file_meta):
        md5 = file_meta.get('md5sum', None)
        content_md5 = file_meta.get('content_md5sum', None)
        return md5, content_md5

    def check_md5_mismatch(self, md5a, md5b):
        return md5a and md5b and md5a != md5b

    # update all,high-level function
    def update_metadata(self):
        for arg in self.output_argnames:
            if self.status(arg) != 'COMPLETED':
                self.ff_meta.run_status = 'error'
        self.update_all_pfs()
        logger.info("updating report...")
        self.update_md5()
        self.update_rna_strandedness()
        self.update_fastq_first_line()
        self.update_file_processed_format_re_check()
        logger.info("updating qc...")
        self.update_qc()
        self.update_input_extras()
        self.create_wfr_qc()
        logger.info("posting all...")
        self.post_all()
        logger.info("patching all...")
        self.patch_all()
        self.ff_meta.run_status = 'complete'
        logger.info("patching workflow run metadata...")
        self.patch_ffmeta()

    def get_postrunjson_url(self, config, jobid, metadata_only):
        try:
            return 'https://s3.amazonaws.com/' + config['log_bucket'] + '/' + jobid + '.postrun.json'
        except Exception as e:
            # we don't need this for pseudo runs so just ignore
            if metadata_only:
                return ''
            else:
                raise e

    def send_notification_email(self, job_name, jobid, status, exec_url=None, sender=None):
        if not sender:
            sender = self.default_email_sender
        subject = '[Tibanna] job %s : %s' % (status, job_name)
        msg = 'Job %s (%s) finished with status %s\n' % (jobid, job_name, status) \
              + 'For more detail, go to %s' % exec_url
        client = boto3.client('ses')
        try:
            client.send_email(Source=sender,
                              Destination={'ToAddresses': [sender]},
                              Message={'Subject': {'Data': subject},
                                       'Body': {'Text': {'Data': msg}}})
        except Exception as e:
            logger.warning("Cannot send email: %s" % e)

    def register_to_higlass(self, tbn, bucket, key, filetype, datatype, genome_assembly=None):
        if bucket not in self.higlass_buckets:
            return None
        if not key:
            return None
        if not genome_assembly:
            return None
        payload = {"filepath": bucket + "/" + key,
                   "filetype": filetype, "datatype": datatype,
                   "coordSystem": genome_assembly}
        higlass_keys = tbn.s3.get_higlass_key()
        if not isinstance(higlass_keys, dict):
            raise Exception("Bad higlass keys found: %s" % higlass_keys)
        auth = (higlass_keys['key'], higlass_keys['secret'])
        headers = {'Content-Type': 'application/json',
                   'Accept': 'application/json'}
        try:
            res = requests.post(higlass_keys['server'] + '/api/v1/link_tile/',
                                data=json.dumps(payload), auth=auth, headers=headers)
        except:
            # do not raise error (do not fail the wrf) - will be taken care of by foursight later
            return None
        logger.info("resiter_to_higlass(POST request response): " + str(res.json()))
        return res.json()['uuid']


def cmp_fileformat(format1, format2):
    return parse_formatstr(format1) == parse_formatstr(format2)


def match_higlass_config(file_format, extra_format):
    for hc in higlass_config:
        if cmp_fileformat(hc['file_format'], file_format):
            if hc['extra']:
                if cmp_fileformat(hc['extra'], extra_format):
                    return hc
            elif not extra_format:
                return hc
    return None


def number(astring):
    """Convert a string into a float or integer
    Returns original string if it can't convert it.
    """
    try:
        num = float(astring)
        if num % 1 == 0:
            num = int(num)
        return num
    except ValueError:
        return astring
