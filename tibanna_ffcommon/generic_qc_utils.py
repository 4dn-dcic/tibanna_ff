from .exceptions import GenericQcException
from collections import deque
from typing import Any, List, Union, Optional
from pydantic import BaseModel, ConfigDict, ValidationError, RootModel
from misc_utils import LogicalExpressionParser


class QC_threshold(BaseModel):
    id: str
    metric: str
    operator: str
    pass_target: Union[float, int]
    warn_target: Union[float, int]
    use_as_qc_flag: Optional[bool] = None


class QC_ruleset(BaseModel):
    qc_thresholds: List[QC_threshold]
    overall_quality_status_rule: str
    applies_to: List[str]


class QC_rulesets(RootModel):
    root: List[QC_ruleset]

    def __iter__(self):
        return iter(self.root)

    def __getitem__(self, item):
        return self.root[item]


class QC_json_value(BaseModel):
    key: str
    value: Any

    model_config = ConfigDict(extra="allow")


class QC_json(BaseModel):
    name: str
    qc_values: List[QC_json_value]


def validate_qc_rulesets(qc_rulesets):
    """Validate the user supplied QC rule sets again the schema and return a Pydantic model.

    Args:
        qc_rulesets (List): List of QC rule sets

    Raises:
        GenericQcException: The supplied QC ruleset has the wrong format

    Returns:
        QC_rulesets: Pydantic model
    """
    try:
        validated_qc_rulesets = QC_rulesets(qc_rulesets)
    except ValidationError as e:
        raise GenericQcException(f"The supplied QC ruleset has the wrong format: {e}")
    return validated_qc_rulesets


def evaluate_qc_ruleset(input_wf_arg_name, qc_json_, qc_rulesets: QC_rulesets):
    """_summary_

    Args:
        input_wf_arg_name (string): input workflow argument that the QCs are validated for
        qc_json_ (Dict): _description_
        qc_ruleset_ (QC_rulesets): _description_

    Raises:
        GenericQcException: _description_
    """

    # Find the rule set that is relevant for the current input file
    qc_ruleset = next(
        (item for item in qc_rulesets if input_wf_arg_name in item.applies_to), None
    )

    if not qc_ruleset:  # No rules have been defined for this file - do nothing
        return qc_json_, None

    try:
        qc_json = QC_json(**qc_json_)
    except ValidationError as e:
        raise GenericQcException(
            f"The contents of the QC json file has the wrong format: {e}"
        )

    # for qc_value in qc_json.qc_values:

    overall_quality_status = True

    return dict(qc_json), overall_quality_status


def evaluate_qc_threshold(qc_threshold: QC_threshold, qc_json: QC_json):
    # Get the relevant metric from the QC Json
    metric = qc_threshold.metric
    metric_value = next(
        (item.value for item in qc_json.qc_values if item.key == metric), None
    )

    if not metric_value:
        raise GenericQcException(f"QC metric {metric} in ruleset not found in QC json")


def check_qc_workflow_args(input_file_args: List[Any], generic_qc_args: List[Any]):
    """This function performs basic sanity checks on the QC and input files

    Args:
        input_file_args (list): List of workflow arguments (input files)
        generic_qc_args (list): List of workflow arguments (Generic QC files)

    Raises:
        GenericQcException: workflow argument does not have argument_to_be_attached_to specified.
        GenericQcException: workflow argument's argument_to_be_attached_to does not exist.
        GenericQcException: Exactly one of qc_json or qc_zipped must be true.
        GenericQcException: There is no QC JSON associated with input workflow argument
        GenericQcException: There are 2 Generic QC files associated with input workflow argument. One must have `qc_json` and the other `qc_zipped` set to true.
        GenericQcException: There are more than 2 Generic QC files for input workflow argument
    """

    workflow_argument_name_inputs = list(
        map(lambda inp: inp["workflow_argument_name"], input_file_args)
    )
    for generic_qc_arg in generic_qc_args:
        wf_arg_name = generic_qc_arg["workflow_argument_name"]
        arg_to_be_attached_to = generic_qc_arg.get("argument_to_be_attached_to", None)
        qc_json = generic_qc_arg.get("qc_json", False)
        qc_zipped = generic_qc_arg.get("qc_zipped", False)

        if not arg_to_be_attached_to:
            raise GenericQcException(
                f"{wf_arg_name} does not have argument_to_be_attached_to specified."
            )
        elif arg_to_be_attached_to not in workflow_argument_name_inputs:
            raise GenericQcException(
                f"{wf_arg_name}'s argument_to_be_attached_to does not exist."
            )
        elif int(qc_json) + int(qc_zipped) != 1:
            raise GenericQcException(
                f"Exactly one of qc_json or qc_zipped must be true."
            )

    for input_file_arg in input_file_args:
        # Get the associated QC args
        input_wf_arg_name = input_file_arg["workflow_argument_name"]
        qc_args = filter_workflow_args_by_property(
            generic_qc_args, "argument_to_be_attached_to", input_wf_arg_name
        )
        if len(qc_args) == 0:
            continue
        # If there is only one Generic QC file, make sure it is the JSON with QC values
        elif len(qc_args) == 1 and not qc_args[0].get("qc_json"):
            raise GenericQcException(
                f"There is no QC JSON associated with input {input_wf_arg_name}"
            )
        elif len(qc_args) == 2:
            # There must be one qc_json and one qc_zipped
            qc_args_json = filter_workflow_args_by_property(qc_args, "qc_json", True)
            qc_args_zipped = filter_workflow_args_by_property(
                qc_args, "qc_zipped", True
            )
            if len(qc_args_json) != 1 or len(qc_args_zipped) != 1:
                raise GenericQcException(
                    f"There are 2 Generic QC files associated with input {input_wf_arg_name}. One must have `qc_json` and the other `qc_zipped` set to true."
                )
        elif len(qc_args) > 2:
            raise GenericQcException(
                f"There are more than 2 Generic QC files for input {input_wf_arg_name}"
            )


def filter_workflow_args_by_property(
    workflow_args: List[Any], property: str, property_value: Any
) -> List[Any]:
    """Takes a list of dictionaries and returns a filtered list of those dicts where
    dict[property]==property_value

    Args:
        workflow_args (list): List of workflow arguments
        property (str): property to filter for
        property_value (any): property value to filter for

    Returns:
        list: Filtered list of dictionaries
    """
    return [arg for arg in workflow_args if arg.get(property, None) == property_value]
