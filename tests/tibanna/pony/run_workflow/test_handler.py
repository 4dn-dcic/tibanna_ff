import pytest
from tibanna_4dn.lambdas.run_workflow import handler
from ..conftest import valid_env
import mock


@pytest.fixture
def run_workflow_input():
    return {
          "app_name": "hi-c-processing-bam",
          "parameters": {
                  "nthreads_merge": 16,
                  "nthreads_parse_sort": 16
                },
          "_tibanna": {
                  "run_type": "hic-bam-run_workflow_test",
                  "env": "fourfront-webdev"
                },
          "output_bucket": "elasticbeanstalk-fourfront-webdev-wfoutput",
          "tag": "0.2.5",
          "config": {
                  "ebs_iops": "",
                  "shutdown_min": "30",
                  "ebs_type": "gp2",
                  "key_name": "4dn-encode",
                  "log_bucket": "tibanna-output"
                },
          "workflow_uuid": "023bfb3e-9a8b-42b9-a9d4-216079526f68",
          "input_files": [
                  {
                            "object_key": [
                                        "4DNFI9H51IRL.bam",
                                        "4DNFIP16HHGH.bam"
                                      ],
                            "bucket_name": "elasticbeanstalk-fourfront-webdev-wfoutput",
                            "workflow_argument_name": "input_bams",
                            "uuid": [
                                        "68f38e45-8c66-41e2-99ab-b0b2fcd20d45",
                                        "7420a20a-aa77-4ea8-b0b0-32a8e80c9bcb"
                                      ]
                          },
                  {
                            "object_key": "4DNFI823LSII.chrom.sizes",
                            "bucket_name": "elasticbeanstalk-fourfront-webprod-files",
                            "workflow_argument_name": "chromsize",
                            "uuid": "4a6d10ee-2edb-4402-a98f-0edb1d58f5e9"
                          }
                ],
          "metadata_only": True,
          "env_name": "fourfront-webdev",
          "output_files": [
                  {
                            "workflow_argument_name": "annotated_bam",
                            "uuid": "ecabab05-3738-47fe-8b55-b08334463c43"
                          },
                  {
                            "workflow_argument_name": "filtered_pairs",
                            "uuid": "7054061b-e87d-4ca4-9693-d186348f5206"
                          }
                ]
    }


@valid_env
@pytest.mark.webtest
def test_run_workflow(run_workflow_input):
    with mock.patch('tibanna.core.API') as mock_run:
        res = handler(run_workflow_input, '')
        env = run_workflow_input['env_name']
        #mock_run.assert_called_once()
        #assert(res)  # will take care of it later
