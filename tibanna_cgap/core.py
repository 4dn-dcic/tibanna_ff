from tibanna_ffcommon.core import API as _API
from .stepfunction import StepFunctionZebra
from .stepfunction_cost_updater import StepFunctionCostUpdater
from .vars import (
    TIBANNA_DEFAULT_STEP_FUNCTION_NAME,
    LAMBDA_TYPE,
    IAM_BUCKETS,
    DEV_ENV,
    PROD_ENV
)
from tibanna.utils import create_tibanna_suffix


class API(_API):

    # This one cannot be imported in advance, because it causes circular import.
    # lambdas run_workflow / validate_md5_s3_initiator needs to import this API
    # to call run_workflow
    @property
    def lambdas_module(self):
        from . import lambdas as zebra_lambdas
        return zebra_lambdas

    @property
    def tibanna_packages(self):
        import tibanna
        import tibanna_ffcommon
        import tibanna_cgap
        return [tibanna, tibanna_ffcommon, tibanna_cgap]

    StepFunction = StepFunctionZebra
    StepFunctionCU = StepFunctionCostUpdater
    default_stepfunction_name = TIBANNA_DEFAULT_STEP_FUNCTION_NAME
    default_env = DEV_ENV
    sfn_type = LAMBDA_TYPE
    lambda_type = LAMBDA_TYPE

    @property
    def TibannaResource(self):
        from .cw_utils import TibannaResource
        return TibannaResource

    @property
    def IAM(self):
        from .iam_utils import IAM
        return IAM

    def __init__(self):
        pass

    def deploy_core(self, name, suffix=None, usergroup='', subnets=None, security_groups=None,
                    env=None, quiet=False):
        default_stepfunction_name = self.default_stepfunction_name
        if env:
            usergroup = env + '_' + usergroup if usergroup else env
        else:
            if usergroup:
                env = DEV_ENV
            else:
                env = PROD_ENV
        self.default_stepfunction_name += create_tibanna_suffix(suffix, usergroup)
        super().deploy_core(name=name, suffix=suffix, usergroup=usergroup, subnets=subnets,
                            security_groups=security_groups, quiet=quiet)
        self.default_stepfunction_name = default_stepfunction_name

    def deploy_zebra(self, suffix=None, usergroup='', subnets=None, security_groups=None, env=None):
        if env:
            usergroup = env + '_' + usergroup if usergroup else env
        else:
            if usergroup:
                env = DEV_ENV
            else:
                env = PROD_ENV
        self.deploy_tibanna(suffix=suffix, usergroup=usergroup, setup=True, default_usergroup_tag='',
                            do_not_delete_public_access_block=True, no_randomize=True,
                            buckets=','.join(IAM_BUCKETS(env)), deploy_costupdater=True,
                            subnets=subnets, security_groups=security_groups)
