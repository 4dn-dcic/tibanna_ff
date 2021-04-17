
from dcicutils.ff_utils import (
    search_metadata,
)
from tibanna import create_logger


logger = create_logger(__name__)


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


def parse_formatstr(file_format_str):
    if not file_format_str:
        return None
    return file_format_str.replace('/file-formats/', '').replace('/', '')
