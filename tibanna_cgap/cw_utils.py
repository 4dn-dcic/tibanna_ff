from tibanna.utils import (
    upload,
    read_s3
)
from tibanna.cw_utils import TibannaResource as TibannaResource_

# instance_id = 'i-0167a6c2d25ce5822'
# filesystem = "/dev/xvdb"
# filesystem = "/dev/nvme1n1"


class TibannaResource(TibannaResource_):
    @classmethod
    def create_html(cls):
        return super(TibannaResource, cls).create_html(report_title='Pipeline Run Metrics')
