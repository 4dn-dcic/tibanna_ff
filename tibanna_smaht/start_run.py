import boto3
import json
from .tiger_utils import FourfrontStarter
from tibanna import create_logger


logger = create_logger(__name__)


def start_run(input_json):
    """
    this is generic function to run awsem workflow
    based on the data passed in

    workflow_uuid : for now, pass this on. Later we can add a code to automatically retrieve this from app_name.
    Note multiple workflow_uuids can be available for an app_name
    (different versions of the same app could have a different uuid)
    """
    starter = FourfrontStarter(**input_json)
    logger.debug("starter.inp.as_dict() = " + str(starter.inp.as_dict()))
    if starter.inp.config.log_bucket and starter.inp.jobid:
        s3 = boto3.client('s3')
        kwargs = {}
        if starter.inp.config.encrypt_s3_upload and starter.inp.config.kms_key_id:
            kwargs.update({
                'ServerSideEncryption': 'aws:kms',
                'SSEKMSKeyId': starter.inp.config.kms_key_id,
            })
        s3.put_object(Body=json.dumps(input_json, indent=4).encode('ascii'),
                      Key=starter.inp.jobid + '.input.json',
                      Bucket=starter.inp.config.log_bucket, **kwargs)
    starter.run()
    return(starter.inp.as_dict())
