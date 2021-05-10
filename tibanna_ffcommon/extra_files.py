from tibanna.base import (
    SerializableObject
)
from .file_format import (
    parse_formatstr,
    cmp_fileformat
)


class ExtraFiles(object):
    extra_files = []

    def __init__(self, extra_files=None):
        if extra_files:
            self.extra_files = [ExtraFile(**exf) for exf in extra_files]
            if not self.check_unique_formats():
                raise Exception("Redundant formats are not allowed in extra files.")

    @property
    def n(self):
        return len(self.extra_files)

    @property
    def file_formats(self):
        return [exf.file_format for exf in self.extra_files]

    def check_unique_formats(self):
        """Return true if all file formats are unique in the extra files"""
        if len(self.file_formats) == len(set(self.file_formats)):
            return True
        else:
            return False

    def select(self, file_format):
        selected = [exf for exf in self.extra_files if cmp_fileformat(exf.file_format, file_format)]
        if selected:
            return selected[0]
        else:
            return None

    def add_extra_file(self, **kwargs):
        self.append(ExtraFile(**kwargs))

    def append(self, extrafile):
        if extrafile.file_format in self.file_formats:
            raise Exception("Cannot add a new extra file. File format %s exists" % extrafile.file_format)
        self.extra_files.append(extrafile)

    def as_dict(self):
        return [exf.as_dict() for exf in self.extra_files]


class ExtraFile(SerializableObject):
    def __init__(self, file_format, status, **kwargs):
        self.file_format = parse_formatstr(file_format)
        self.status = status


def get_extra_file_key(infile_format, infile_key, extra_file_format, fe_map):
    infile_extension = fe_map.get_extension(infile_format)
    extra_file_extension = fe_map.get_extension(extra_file_format)
    if not infile_extension or not extra_file_extension:
        errmsg = "Extension not found for infile_format %s (key=%s)" % (infile_format, infile_key)
        errmsg += "extra_file_format %s" % extra_file_format
        errmsg += "(infile extension %s, extra_file_extension %s)" % (infile_extension, extra_file_extension)
        raise Exception(errmsg)
    return infile_key.replace(infile_extension, extra_file_extension)
