from tibanna_smaht.tiger_utils import TigerInput
from tibanna_smaht.vars import DEFAULT_ROOT_EBS_SIZE


def make_input(config):
    # output_bucket is given so that no portal lookup is needed
    return TigerInput(workflow_uuid="test-uuid", output_bucket="test-bucket",
                      config=dict(config, log_bucket="test-log-bucket"))


def test_tiger_input_default_root_ebs_size():
    assert DEFAULT_ROOT_EBS_SIZE == 15
    assert make_input({}).config.root_ebs_size == 15


def test_tiger_input_keeps_explicit_root_ebs_size():
    assert make_input({"root_ebs_size": 40}).config.root_ebs_size == 40
