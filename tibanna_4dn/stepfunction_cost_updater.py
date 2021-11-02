from tibanna.stepfunction_cost_updater import StepFunctionCostUpdater as StepFunctionCostUpdater_
from .vars import SFN_TYPE, LAMBDA_TYPE


class StepFunctionCostUpdater(StepFunctionCostUpdater_):
    sfn_type = SFN_TYPE

    @property
    def lambda_type(self):
        return LAMBDA_TYPE

    @property
    def sfn_state_defs(self):
        state_defs = {
            "Wait": {
            "Type": "Wait",
            "Seconds": 43200, # Check every 12h
            "Next": "UpdateCostAwsem"
            },
            "UpdateCostAwsem": {
                "Type": "Task",
                "Resource": self.lambda_arn_prefix + "update_cost_" + self.lambda_type + self.lambda_suffix,
                "ResultPath": "$.done",
                "Next": "UpdateCostDone"
            },
            "UpdateCostDone": {
              "Type": "Choice",
              "Choices": [
                {
                  "Variable": "$.done.done",
                  "BooleanEquals": True,
                  "Next": "Done"
                }
              ],
              "Default": "Wait"
            },
            "Done": {
              "Type": "Pass",
              "End": True
            }
        }
        return state_defs

    @property
    def iam(self):
        from .iam_utils import IAM
        return IAM(self.usergroup)
