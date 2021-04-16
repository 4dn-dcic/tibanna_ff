class FFInputFiles(object):
    """Class representation for the input_files field in The
    pony/zebra input json (job description).
    """
    def __init__(self, input_files, ff_key, ff_env):
        """input_files : list of dictionaries provided as part of
        Pony/Zebra input json as the field 'input_files'
        """
        self.input_files = [FFInputFile(**inpf, ff_key=ff_key, ff_env=ff_env) for inpf in ff_input_files]
        self.ff_key = ff_key
        self.ff_env = ff_env

    def create_unicorn_arg_input_files(self):
        inp_files = dict()
        for inpf in self.input_files:
            inp_files.update(inpf.create_unicorn_arg_input_file())
        return inp_files

    def create_unicorn_arg_secondary_input_files(self):
        sec_inp_files = dict()
        for inpf in self.input_files:
            sec_inp_files.update(inpf.create_unicorn_arg_secondary_input_file())
        return sec_inp_files


class FFInputFile(Object):
    """Class representation for each element in the input_files field in The
    pony/zebra input json (job description).
    """
    # The fields to be included in a dict form of this class object.
    dict_fields = ['uuid', 'workflow_argument_name', 'object_key',
                   'bucket_name', 'rename', 'unzip', 'mount', 'format_if_extra']

    # these fields are exactly the same between pony/zebra and unicorn
    # and can be passed directly. The field object_key exists in both
    # but the meanings are different.
    common_unicorn_fields = ['bucket_name', 'rename', 'unzip', 'mount',
                             'format_if_extra']

    # for status check - these statuses indicate the file is not ready
    not_ready_status_list = ['uploading', 'to be uploaded by workflow',
                             'upload failed', 'deleted']

    # the following two private attributes works as a cache for metadata -
    # do not modify them or access them directly, but use self.get_metadata
    # or self.fe_map or instead
    _metadata = dict()
    _fe_map = None

    def __init__(self, uuid, workflow_argument_name, object_key=None,
                 bucket_name=None, rename='', unzip='', mount=False,
                 format_if_extra='', ff_key=None, ff_env=None):
        self.uuid = uuid  # either a single value or a list
        self.workflow_argument_name = workflow_argument_name
        ## here objct key means <accession>.<extension>
        self.object_key = object_key # either a single value or a list
        self.bucket_name = bucket_name
        self.rename = rename  # either a single value or a list
        self.unzip = unzip
        self.mount = mount
        self.format_if_extra = format_if_extra
        self.ff_key = ff_key
        self.ff_env = ff_env
        if self.ff_key and self.ff_env:
            self.fill_in()

    def as_dict(self):
        return {field: getattr(self, field) for field in self.dict_fields}

    def fill_in(self):
        """fill in input_files info if object_key and bucket_name is not provided"""
        if not self.object_key':
            try:
                self.object_key = run_on_nested_arrays1(self.uuid, self.get_object_key_from_uuid)
            except Exception as e:
                raise FdnConnectionException(e)
        if not self.bucket_name':
            try:
                file_type = flatten(run_on_nested_arrays1(self.uuid, self.get_file_type_from_uuid))
                if isinstance(file_type, list):
                    file_type = file_type[0]
            except Exception as e:
                raise FdnConnectionException(e)
            # assume all file types are the same for a given argument
            self.bucket_name = BUCKET_NAME(self.ff_env, file_type)
        logger.debug("infile = " + str(self.as_dict()))

    def crate_unicorn_arg_input_file(self):
        """returns a dictionary in the unicorn args input file format"""
        key = self.workflow_argument_name
        value = {fld: getattr(self, fld) for fld in self.common_unicorn_fields}
        value.update('object_key': self.s3_key)  # do not use self.object_key here.
        return {key: value}

    def create_unicorn_arg_secondary_input_file(self):
        """returns a dictionary in the unicorn args secondary input file format
        for extra files"""
        extra_file_keys = self.extra_file_s3_keys
        if not extra_file_keys:  # no extra files
            return {}
        key = self.workflow_argument_name
        value = {'bucket_name': self.bucket_name,
                 'object_key': extra_file_keys,
                 'mount': self.mount
                 }
        if self.extra_file_renames:
            value.update({'rename': self.extra_file_renames})
        return {key: value}

    @property
    def extra_file_renames(self):
        """The string or string list to be in the rename field of the secondary_input_files,
        which corresponds to the extra files of the uuid(s) of the input_files.
        None values, '' or [] are removed from the return list.
        If the return list has a single element, it returns the element as a string.
        In a situation like [[[],[]],[],[]], None is returned instead.
        If rename is not set for the main file, None is returned.
        """
        if not self.rename:
            return None
        exf_rn = run_on_nested_arrays2(self.uuid, self.rename,
                                       self.get_extra_file_renames_from_uuid)
        # a situation like [[[],[]],[],[]] --> return None instead
        if not flatten(exf_rn):
            return None
        if exf_rn and len(exf_rn)>0:
            exf_rn = list(filter(lambda x: x, exf_rn))
        if len(exf_rn) == 1:
            exf_rn = exf_rn[0]
        return exf_rn

    @property
    def extra_file_s3_keys(self):
        """The actual object key name(s) on the S3 bucket - most of the time
        this is the same as upload_key(s) but in special cases,
        this could include prefixes (e.g in case of 4DN Open Data)
        None values or '' values are removed from the return list.
        If the return list has a single element, it returns the element as a string.
        """
        exf_keys = run_on_nested_arrays1(self.uuid, self.get_extra_file_s3_key_from_uuid)
        if not flatten(exf_keys):
            return None
        if exf_keys and len(exf_keys) > 0:
            exf_keys = list(filter(lambda x: x, exf_keys))
        if len(exf_keys) == 1:
            exf_keys = exf_keys[0]

    @property
    def s3_key(self):
        """The actual object key name(s) on the S3 bucket - most of the time
        this is the same as upload_key(s) but in special cases,
        this could include prefixes (e.g in case of 4DN Open Data)
        """
        return run_on_nested_arrays1(self.uuid, self.get_s3_key_from_uuid)

    @property
    def upload_key(self):
        """The upload_key(s) which may be different from the actual s3 key name(s)
        on the S3 bucket (e.g. in case of 4DN Open Data)
        """
        try:
            return run_on_nested_arrays1(self.uuid, self.get_upload_key_from_uuid)
        except:
            return combine_two(self.uuid, self.object_key)

    # These methods get_xx_from_uuid operate a single uuid input (not a list)
    # e.g. if self.uuid is a list, these functions could operate on an element in it.
    # if self.uuid is a 3d list, these function would still operate on an element in
    # one of the innermost lists.
    def get_extra_file_renames_from_uuid(self, uuid, rename=None):
        """The actual object key name(s) of the extra files on the S3 bucket -
        most of the time this is the same as upload_key(s) but in special cases,
        this could include prefixes (e.g in case of 4DN Open Data).
        rename is a single string from the 'rename' field of an input_file
        that matches the uuid.
        """
        if not rename:
            return None
        extra_file_formats = self.get_extra_file_formats_from_uuid(uuid)
        if not extra_file_formats
            return None
        main_file_key = self.get_s3_key_from_uuid(uuid)
        return [get_extra_file_key(main_file_format, rename, exff, self.fe_map)
                for exff in extra_file_formats]

    def get_extra_file_s3_keys_from_uuid(self, uuid):
        """The actual object key name(s) of the extra files on the S3 bucket -
        most of the time this is the same as upload_key(s) but in special cases,
        this could include prefixes (e.g in case of 4DN Open Data)
        """
        extra_file_formats = self.get_extra_file_formats_from_uuid(uuid)
        if not extra_file_formats
            return None
        main_file_format = self.get_file_format_from_uuid(uuid)
        main_file_key = self.get_s3_key_from_uuid(uuid)
        return [get_extra_file_key(main_file_format, main_file_key, exff, self.fe_map)
                for exff in extra_file_formats]

    def get_extra_file_formats_from_uuid(self, uuid):
        """returns parsed (cleaned) version of file format (e.g. 'bai') for extra files"""
        extra_files = self.get_extra_files_from_uuid(uuid)
        if not extra_files:
            return None
        return [parse_formatstr(exf['file_format']) for exf in extra_files]

    def get_extra_files_from_uuid(self, uuid):
        """returns a list of extra file dictionaries received from the server"""
        infile_meta = self.get_metadata(uuid)
        exf = infile_meta.get('extra_files')
        if exf.get('status') not in self.not_ready_status_list:
            return(infile_meta.get('extra_files'))
        else:
            return None

    def get_file_format_from_uuid(self, uuid):
        """returns parsed (cleaned) version of file format (e.g. 'bam')"""
        file_format = self.get_metadata(uuid)['file_format']
        return parse_formatstr(file_format)

    def get_s3_key_from_uuid(self, uuid):
        """The actual object key name(s) on the S3 bucket - most of the time
        this is the same as upload_key(s) but in special cases,
        this could include prefixes (e.g in case of 4DN Open Data)
        """
        open_data_url = self.get_open_data_url_from_uuid(uuid)
        if open_data_url:
            bucket, key = self.parse_s3_url(open_data_url)
            return key
        else:
            return self.get_upload_key_from_uuid(uuid)

    def get_open_data_url_from_uuid(self, uuid):
        infile_meta = self.get_metadata(uuid)
        return infile_meta('open_data_url', '')

    def get_upload_key_from_uuid(self, uuid):
        infile_meta = self.get_metadata(uuid)
        return infile_meta['upload_key']

    def get_object_key_from_uuid(self, uuid):
        infile_meta = self.get_metadata(uuid)
        return infile_meta['upload_key'].replace(uuid + '/', '')

    def get_file_type_from_uuid(self, uuid):
        infile_meta = self.get_metadata(uuid)
        return(infile_meta['@type'][0])

    @peroperty
    def fe_map(self):
        """returns a format extension map (a mapping between file format and
        file extension) retrieved from the portal. The first time it is called,
        the result is saved in a cache, to avoid sending redundant requests.
        """
        # use cache
        if self._fe_map:
            return self._fe_map
        else:
            self._fe_map = FormatExtensionMap(self.ff_key)
            return self._fe_map

    def get_metadata(self, id):
        """returns the metadata retrieved from the portal for a given id (e.g.
        uuid or accession). The first time it is called, the result is saved in
        a cache, to avoid sending redundant requests.
        """
        # use cache
        if self._metadata.get(id, ''):
            return self._metadata[id]
        else:
            self._metadata[id] = get_metadata(id,
                                              key=self.ff_key,
                                              ff_env=self.ff_env,
                                              add_on='frame=object',
                                              check_queue=True)
            return self._metadata[id]

    @staticmethod
    def parse_s3_url(url):
        """parsing "https://bucketname.s3.amazonaws.com/dir/dir2/file"
        into ("bucketname", "dir/dir2/file")
        Works for both http and http2 but only works for s3 url which is
        https anyway.
        """
        url_words = re.sub(r'https*://', '', url).split('/')
        bucket = url_words[0].split('.')[0]
        key = '/'.join(url_words[1:])
        return bucket, key


class UnicornArgsInputFiles(SerializableObject):
    """Class representation for the input_files / secondary_input_files field
    in the args section of the Unicorn input json (job description).
    """
    def __init__(self):
        """Attribute input_files is a dictionary with workflow_argument_name
        as key and a UnicornArgsInputFile object as value
        """
        self.input_files = {}

    def add_input_file(self, input_file_dict, workflow_argument_name):
        self.input_files.update({workflow_argument_name: UnicornArgsInputFile(**input_file_dict)})


class UnicornArgsInputFile(SerializableObject):
    """Class representation for each element in the input_files /
    secondary_input_files field in the args section of the Unicorn input json
    (job description).
    """
    def __init__(self, object_key, bucket_name, rename='', unzip='', mount=False):
        self.object_key = object_key
        self.bucket_name = bucket_name
        self.rename = rename
        self.unzip = unzip
        self.mount = mount
