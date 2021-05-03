import boto3
import json
import mimetypes
from zipfile import ZipFile
from io import BytesIO
from dcicutils.ff_utils import (
    get_metadata,
)
from tibanna.base import (
    SerializableObject
)
from collections import namedtuple
from .exceptions import (
    FdnConnectionException
)


class QCArgument(SerializableObject):
    """This is a class that represents a QC-type workflow argument which is a part of
    a workflow metadata
    """
    def __init__(self, argument_type, workflow_argument_name, argument_to_be_attached_to, qc_type=None,
                 qc_zipped=False, qc_html=False, qc_json=False, qc_table=False,
                 qc_zipped_html=None, qc_zipped_tables=None, qc_acl='public-read',
                 qc_unzip_from_ec2=False):
        if argument_type != 'Output QC file':
            raise Exception("QC Argument must be an Output QC file: %s" % argument_type)
        self.workflow_argument_name = workflow_argument_name
        self.argument_to_be_attached_to = argument_to_be_attached_to
        self.qc_type = qc_type  # qc metadata item type (e.g. quality_metric_fastqc)
        self.qc_zipped = qc_zipped
        self.qc_html = qc_html  # boolean, true if qc is unzipped html
        self.qc_json = qc_json  # boolean, true if qc is unzipped json
        self.qc_table = qc_table  # boolean, true if qc is unzipped table file (tab- or space-delimited text)
        self.qc_zipped_html = qc_zipped_html  # name of the main qc html file in the zip archive
        self.qc_zipped_tables = qc_zipped_tables  # list of suffixes of table files in the zip archive
        self.qc_acl = qc_acl
        if self.qc_table or self.qc_zipped_tables:
            if not self.qc_type:
                raise Exception("qc_type is required if qc_table or qc_zipped_table")
        self.qc_unzip_from_ec2 = qc_unzip_from_ec2
        self.qc_data_parser = None
        # The following can be added later and are required by some methods.
        # (not a part of a workflow QC argument)
        self.s3_key = None
        self.bucket = None
        self.target_accession = None
        self.qc_data_parser = None

    @property
    def target_html(self):
        if self.qc_zipped_html:
            return self.target_accession + '/' + self.qc_zipped_html
        elif self.qc_html:
            return self.target_accession + '/qc_report.html'
        else:
            return None

    def add_paths(self, bucket, s3_key):
        self.bucket = bucket
        self.s3_key = s3_key

    def add_target_accession(self, target_accession):
        """Add only one (first) target accession to be used to compose
        the qc report url and the designated location on s3."""
        self.target_accession = target_accession

    def add_qc_parser(self, qc_schema):
        """adding a qc parser based on a qc schema
        which is a dictionary describing the schema properties
        of a relevant qc type (that you can get from the properties field
        in the schema obtained from profiles/quality_metric_xxx.json"""
        self.qc_data_parser = QCDataParser(qc_schema)

    def as_dict(self):
        d_shallow = self.__dict__.copy()
        if 'qc_data_parser' in d_shallow:
            del(d_shallow['qc_data_parser'])
        del(d_shallow['s3_key'])
        del(d_shallow['bucket'])
        del(d_shallow['target_accession'])
        do = SerializableObject()
        do.update(**d_shallow)
        return do.as_dict()

    def copy_qc_files_to_s3(self):
        """copies qc files to a designated location on s3."""
        qc_item = dict()
        #qc_bucket = self.bucket(qc.workflow_argument_name)
        #qc_key = self.file_key(qc.workflow_argument_name)
        if self.qc_unzip_from_ec2:
            return None
        elif self.qc_zipped:
            unzip_s3_to_s3(self.bucket, self.s3_key, self.target_accession, acl='public-read')
        else:
            data = read_s3_data(self.bucket, self.s3_key)
            if self.qc_html:
                put_data_to_s3(data.encode(), self.bucket, self.target_html, acl='public-read')

    def create_qc_item_content(self):
        qc_item_content = dict()
        url = self.get_qc_url()
        data_fields = self.get_qc_data_fields()
        if url:
            qc_item_content.update({'url': url})
        if data_fields:
            qc_item_content.update(data_fields)
        return qc_item_content

    def get_qc_url(self):
        """Get the value for the url field of the QC item to be created.
        qc_bucket is the bucket where the final QC html will go to.
        target_accession is the accession of the first target file to which
        the QC item will be linked to.
        """
        if self.qc_unzip_from_ec2:
            return None
        if self.qc_zipped_html or self.qc_html:
            return 'https://s3.amazonaws.com/' + self.bucket + '/' + self.target_html
        else:
            return None

    def get_qc_data_fields(self):
        """Internal update function for qc per workflow qc argument"""
        if self.qc_unzip_from_ec2:
            return None
        if not self.qc_data_parser:
            raise Exception("First run add_qc_parser to activate qc_data_parser.")
        if self.qc_zipped_tables:
            # unzipped_qc_data is a list of individual file content strings
            unzipped_qc_data = unzip_s3_data(self.bucket, self.s3_key, suffixes=self.qc_zipped_tables)
            return self.qc_data_parser.parse_qc_table(unzipped_qc_data)
        elif self.qc_json:
            data = read_s3_data(self.bucket, self.s3_key)
            return self.qc_data_parser.parse_qc_json([data])
        elif self.qc_table:
            data = read_s3_data(self.bucket, self.s3_key)
            return self.qc_data_parser.parse_qc_table([data])


class QCArgumentsPerTarget(object):
    """This class represents a list of QCArgument objects that
    belong to the same target (argument_to_be_attached_to)"""

    # the following attribute works as a cache for metadata -
    # do not modify or access it directly, but use self.get_metadata
    # instead
    _metadata = dict()

    # minimal information about existing qc items of a target file item
    ExistingQCInfo = namedtuple('ExistingQCInfo', ['type', 'uuid', 'qc_list'])

    def __init__(self, qca_list):
        """qca_list is a list of QCArgument objects"""
        self.qca_list = qca_list
        self.target_argname = self.qca_list[0].argument_to_be_attached_to

        # make sure target arg is unique.
        unique_target_args = set([_.argument_to_be_attached_to for _ in self.qca_list])
        if len(unique_target_args) != 1:
            raise Exception("QCArgumentsPerTarget must contain a list of " + \
                            "QCArgument objects with the same argument_to_be_attached_to.")

        self.qc_types = set([_.qc_type for _ in self.qca_list])
        self.qc_types_no_none = set([_.qc_type for _ in self.qca_list if _.qc_type])
        self.qca_list_by_type = {qctype: [_ for _ in self.qca_list if _.qc_type == qctype]
                                 for qctype in self.qc_types}

    def add_ff_keys(self, ff_key, ff_env):
        self.ff_key = ff_key
        self.ff_env = ff_env

    def add_target_accessions(self, target_accessions):
        # target_accessions is a list of target accessions.
        # there may be multiple target accessions to link to the same new qc items
        # e.g. correlation qc for replicates.
        self.all_target_accessions = target_accessions
        for qca in self.qca_list:
            # pass only the first target accession which is used in the
            # report url field of the new qc metadata item and in the
            # designated s3 location to move the qc files to.
            qca.add_target_accession(target_accessions[0])

    def add_qc_template_generator(self, qc_template_gen):
        """let users to add custom qc template generator function.
        qc_template_func is a function that returns a dictionary
        that can be used as a template for qc item, including uuid.
        """
        self.qc_template_gen = qc_template_gen

    def add_qclist_template_generator(self, qclist_template_gen):
        """let users to add custom qclist item template generator function.
        qclist_template_func is a function that returns a dictionary
        that can be used as a template for qclist item, including uuid.
        """
        self.qclist_template_gen = qclist_template_gen

    def create_qc_items(self):
        # QC metadata items to be created
        # requires to have run self.add_target_accessions
        self.qc_items_by_type = self.create_qc_items_by_type()
        self.qclist_item = self.create_qclist_item()

    def copy_qc_files_to_s3(self):
        for qca in self.qca_list:
            qca.copy_qc_files_to_s3()

    def create_qc_items_by_type(self):
        """return what will be the qc_items_by_type attribute which is a dictionary
        with qc_types as keys and new qc items (in dictionary format) as values.
        This function does not post or patch anything to the portal.
        """
        return {qc_type: self.create_qc_item_per_type(qc_type)
                for qc_type in self.qc_types_no_none}

    def create_qc_item_per_type(self, qc_type):
        """create the a single qc metadata item (in dictionary format) for a single
        qc_type. This function is internal and is called by self.create_qc_items_by_type().
        This function does not post or patch anything to the portal.
        """
        qc_schema = self.get_schema(qc_type)
        qc_item = next(self.qc_template_gen)
        for qca in self.qca_list_by_type[qc_type]:
            qca.add_qc_parser(qc_schema)
            qc_item.update(qca.create_qc_item_content())
        return qc_item

    def create_qclist_item(self):
        """create the a single qclist metadata item (in dictionary format).
        This function does not post or patch anything to the portal.
        """
        if len(self.qc_types_no_none) > 1:
            item = next(self.qclist_template_gen)
            item['qc_list'] = []
            for qc_type in self.qc_items_by_type:
                item['qc_list'].append({'qc_type': qc_type,
                                        'value': self.qc_items_by_type[qc_type]['uuid']})
            return item
        else:
            return None

    def create_qclist_item_for_target(self, target_accession):
        """depending on the existing qc and list items on a given target accession
        the actual qclist item may be different. Each file item gets its own qclist item.
        """

        existing_qc = get_existing_qc_item_linked_to_target(target_accession)
        if existing_qc:
            if existing_qc.type == 'quality_metric_qclist':
                # add to existing qclist instead of creating a new one.
                existing_qc_list_dict = {_['qc_type']: _['value'] for _ in existing_qc.qc_list}
                for qc_type, qc_item in self.qc_items_by_type.items():
                    # overwrite existing qc of the same type
                    # add qcs of new type.
                    existing_qc_list_dict.update({qc_type: qc_item['uuid']})
                # new value for the qc_list field for existing qclist metadata item.
                new_qclist = [{'qc_type': k, 'value': v} for k, v in existing_qc_list_dict.items()]
            else:
                if existing_qc.type not in self.qc_types_no_none:
                    # add existing qc to new qclist item.
                    # every target file item has its own qclist item.
                    new_qclist_item = self.create_qclist_item()
                    new_qclist_item['qc_list'].append({'qc_type': existing_qc.type,
                                                       'value': existing_qc.uuid})


        return {'new_qclist_item': new_qclist_item,
                'existing_qclist_item': existing_qc.uuid}

    def get_existing_qc_item_linked_to_target(self, target_accession):
        """get an existing quality_metric item already linked to a target accession
        and returns the item type and uuid of the quality_metric item and
        if the type is qclist, also returns the qclist field value of the qc item.
        """
        res = self.get_metadata(target_accession)
        if 'quality_metric' not in res:
            return None
        else:
            qc_type, qc_uuid = parse_quality_metric_field_from_file_item(res['quality_metric'])
            if qc_type == 'quality_metric_qclist':
                qc_list = self.get_metadata(qc_uuid).get('qc_list')
            else:
                qc_list = None
            return self.ExistingQCInfo(qc_type, qc_uuid, qc_list)

    def get_schema(self, qc_type):
        return self.get_metadata("profiles/" + qc_type + ".json")['properties']

    def get_metadata(self, id):
        if self._metadata.get(id, ''):
            return self._metadata[id]
        else:
            try:
                self._metadata[id] = get_metadata(id,
                                                  key=self.ff_key,
                                                  ff_env=self.ff_env,
                                                  add_on='frame=object',
                                                  check_queue=True)
            except Exception as e:
                raise FdnConnectionException(e)
            return self._metadata[id]

    @staticmethod
    def parse_quality_metric_field_from_file_item(quality_metric_field):
        """quality_metric_field is the value of the quality_metric field
        of a file item dictionary obtained through get_metadata.
        returns the item type and uuid of the corresponding quality_metric item.
        """
        qc_type = quality_metric_field.split('/')[1].replace('-', '_'). \
                                       replace('quality_metrics', 'quality_metric')
        qc_uuid = quality_metric_field.split('/')[2]
        return qc_type, qc_uuid


class QCArgumentsByTarget(object):
    """This class contains a dictionary of a QCArgumentsPerTarget object as value and
    argument_to_be_attached_to (target argument name) as key"""

    def __init__(self, wf_arguments=None):
        """wf_arguments is the value of the arguments field of a workflow metadata,
        which is a list of dictionaries. Ideally, wf_arguments should be pre-filtered
        to contain only 'Output QC file' type arguments,
        but if not, the filtering will be done here.
        """
        self.qca_by_target = dict()
        if wf_arguments:
            qca_list = [QCArgument(**arg) for arg in wf_arguments
                         if arg['argument_type'] == 'Output QC file']
            for arg in set([_.argument_to_be_attached_to for _ in qca_list]):
                self.qca_by_target.update({arg: QCArgumentsPerTarget([_ for _ in qca_list if _.argument_to_be_attached_to == arg])})

    @property
    def qca_list(self):
        """generator all all QCArgument items (without going through QCArgumentsPerTarget)"""
        for arg in self.qca_by_target:
            for qca in self.qca_by_target[arg].qca_list:
                yield qca

    @property
    def qca_argname_list(self):
        for qca in self.qca_list:
            yield qca.workflow_argument_name

    def add_paths(self, path_dict, bucket):
        """path_dict is a dictionary of argument names as keys and
        s3 keys as values for all qc output files
        """
        for qca in self.qca_list:
            if qca.workflow_argument_name in path_dict:
                qca.add_paths(bucket=bucket,
                              s3_key=path_dict[qca.workflow_argument_name])

    def add_ff_keys(self, ff_key, ff_env):
        """add ff key and env to each QCArgumentPerTarget item
        """
        for arg, qca_per_target in self.qca_by_target.items():
            qca_per_target.add_ff_keys(ff_key=ff_key, ff_env=ff_env)


class QCDataParser(object):
    """This class implements a parser for QC data table files and QC json files
    in a way that depends on qc schema (dictionary describing fields)
    """
    def __init__(self, qc_schema):
        self.qc_schema = qc_schema

    def parse_qc_table(self, data_list):
        """data_list is a list of individual file content (strings).
        qc_schema is the schema dictionary for the desired qc type."""
        qc_json = dict()
        for data in data_list:
            for line in data.split('\n'):
                entry = line.strip().split('\t')
                print("entry=" + str(entry))
                # flagstat qc handling - e.g. each line could look like "0 + 0 blah blah blah"
                # blah blah blah becomes the key, 0 + 0 becomes the value.
                space_del = line.strip().split(' ')
                flagstat_entry = [' '.join(space_del[0:3]), ' '.join(space_del[3:])]
                try:
                    qc_json.update(self.match_field_type(entry[0], entry[1]))
                    qc_json.update(self.match_field_type(entry[1], entry[0]))
                    qc_json.update(self.match_field_type(flagstat_entry[1], flagstat_entry[0]))
                except IndexError:  # pragma: no cover
                    # maybe a blank line or something
                    pass
        return qc_json

    def parse_qc_json(self, data_list):
        """data_list is a list of individual file content (strings).
        qc_schema is the schema dictionary for the desired qc type.
        Allow entering fields that are not defined in the schema."""
        qc_json = dict()
        for data in data_list:
            qc_json.update(json.loads(data))
        type_matched_qc_json = dict()
        for k, v in qc_json.items():
            type_matched_qc_json.update(self.match_field_type(k, v, strict=False))
        return type_matched_qc_json

    def match_field_type(self, name, value, strict=True):
        """Add entry to qc_json if it's in the schema.
        for number type field, remove ',' from the value.
        (e.g. 20,000,000 -> 20000000)
        for string type field, convert numbers to string.
        (e.g. 20 -> "20")
        if strict is True, do not include entries that do not match
        a field in the schema.
        """
        field_type = self.qc_schema.get(name, {}).get('type', None)
        if field_type == 'string':
            return {name: str(value)}
        elif field_type == 'number':
            return {name: self.number(value.replace(',', ''))}
        else:
            if strict:
                return {}
            else:
                return {name: value}

    @staticmethod
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

def read_s3_data(bucket, key):
    """store the content of a zipped key on S3.
    suffixes is a filter (a list of suffixes) for file names inside the zip file.
    Returns a list of individual file contents.
    """
    s3_stream = boto3.client('s3').get_object(Bucket=bucket, Key=key)
    return s3_stream['Body'].read().decode('utf-8', 'backslashreplace')


def unzip_s3_data(bucket, key, suffixes=None):
    """store the content of a zipped key on S3.
    suffixes is a filter (a list of suffixes) for file names inside the zip file.
    Returns a list of individual file contents.
    """
    s3_stream = boto3.client('s3').get_object(Bucket=bucket, Key=key)['Body'].read()
    # read this badboy to memory, don't go to disk
    bytestream = BytesIO(s3_stream)
    zipstream = ZipFile(bytestream, 'r')

    contents = []
    for file_name in zipstream.namelist():
        # don't store dirs just files
        if not file_name.endswith('/'):
            if check_suffix(file_name, suffixes):
                contents.append(zipstream.open(file_name, 'r').read().decode('utf-8', 'backslashreplace'))
    return contents


def unzip_s3_to_s3(bucket, key, dest_dir, acl=None):
    """stream the content of a zipped key on S3 to another location on S3.
    The destination s3 key name is dest_dir/filename if a path in the zip
    archive is either filename or somedir/someotherdir/filename.
    Source and target buckets are the same.
    """

    if not dest_dir.endswith('/'):
        dest_dir += '/'

    s3_stream = boto3.client('s3').get_object(Bucket=bucket, Key=key)['Body'].read()
    # read this badboy to memory, don't go to disk
    bytestream = BytesIO(s3_stream)
    zipstream = ZipFile(bytestream, 'r')

    # The contents of zip can sometimes be like
    # ["foo/", "file1", "file2", "file3"]
    # and other times like
    # ["file1", "file2", "file3"]
    file_list = zipstream.namelist()
    if file_list[0].endswith('/'):
        # in case directory first name in the list
        basedir_name = file_list.pop(0)
    else:
        basedir_name = ''

    for file_name in file_list:
        # don't copy dirs just files
        if not file_name.endswith('/'):
            content = zipstream.open(file_name, 'r').read()
            if basedir_name:
                s3_file_name = file_name.replace(basedir_name, dest_dir)
            else:
                s3_file_name = dest_dir + file_name
            put_data_to_s3(content, bucket, s3_file_name, acl=acl)


def put_data_to_s3(data, bucket, key, acl=None):
    """data is bytes not string"""
    content_type = mimetypes.guess_type(key)[0]
    if content_type is None:
        content_type = 'binary/octet-stream'
    put_object_args = {'Bucket': bucket, 'Key': key, 'Body': data,
                       'ContentType': content_type}
    if acl:
        put_object_args.update({'ACL': acl})
    return boto3.client('s3').put_object(**put_object_args)


def check_suffix(x, suffixes):
    """check whether string x ends with one of the suffixes in suffixes"""
    for suffix in suffixes:
        if x.endswith(suffix):
            return True
    return False
