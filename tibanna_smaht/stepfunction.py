from .vars import LAMBDA_TYPE
from tibanna_ffcommon.stepfunction import StepFunctionFFAbstract


class StepFunctionTiger(StepFunctionFFAbstract):

    @property
    def lambda_type(self):
        return LAMBDA_TYPE

    @property
    def iam(self):
        from .iam_utils import IAM
        return IAM(self.usergroup)
