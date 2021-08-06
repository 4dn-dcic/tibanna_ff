from tibanna.stepfunction_cost_updater import StepFunctionCostUpdater as StepFunctionCostUpdater_
from .vars import SFN_TYPE


class StepFunctionCostUpdater(StepFunctionCostUpdater_):
    sfn_type = SFN_TYPE

    @property
    def iam(self):
        from .iam_utils import IAM
        return IAM(self.usergroup)
