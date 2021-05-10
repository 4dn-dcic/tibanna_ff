
from dcicutils.ff_utils import (
    search_metadata,
)
from tibanna import create_logger


logger = create_logger(__name__)


class FormatExtensionMap(object):
    def __init__(self, ff_keys=None, ffe_all=None):
        """connect to the server and get all fileformat search result if ff_keys
        if given. If not, use user-specified ffe_all
        """
        if not ff_keys and not ffe_all:
            raise Exception("Either ff_keys or ffe_all must be specified" + \
                            "to create a FormatExtensionMap object")
        if ff_keys and ffe_all:
            raise Exception("Either ff_keys or ffe_all must be specified but not both" + \
                            "to create a FormatExtensionMap object")
        if ff_keys and not ffe_all:
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


def parse_formatstr(file_format_str):
    if not file_format_str:
        return None
    return file_format_str.replace('/file-formats/', '').replace('/', '')


def cmp_fileformat(format1, format2):
    return parse_formatstr(format1) == parse_formatstr(format2)
