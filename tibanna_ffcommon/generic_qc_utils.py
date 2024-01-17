from .exceptions import GenericQcException
from typing import Any, List, Union, Optional
from pydantic import BaseModel, ConfigDict, ValidationError, RootModel
from .misc_utils import LogicalExpressionParser

# Tibanna interal QC flags
PASS = "pass"
WARN = "warn"
FAIL = "fail"


class QC_threshold(BaseModel):
    id: str
    metric: str
    operator: str
    pass_target: Union[float, int, str]
    warn_target: Union[float, int, str]
    use_as_qc_flag: Optional[bool] = None


class QC_ruleset(BaseModel):
    qc_thresholds: List[QC_threshold]
    overall_quality_status_rule: str


class QC_json_value(BaseModel):
    key: str
    value: Any

    model_config = ConfigDict(extra="allow")


class QC_json(BaseModel):
    qc_values: List[QC_json_value]


def get_qc_ruleset_model(qc_ruleset) -> QC_ruleset:
    """Validate the user supplied QC rule set again the schema and return a Pydantic model.

    Args:
        qc_ruleset (dict): QC rule set

    Raises:
        GenericQcException: The supplied QC ruleset has the wrong format

    Returns:
        QC_ruleset: Pydantic model
    """
    try:
        validated_qc_ruleset = QC_ruleset(**qc_ruleset)
    except ValidationError as e:
        raise GenericQcException(f"The supplied QC ruleset has the wrong format: {e}")
    return validated_qc_ruleset


def evaluate_qc_threshold(qc_threshold: QC_threshold, qc_json: QC_json):
    """Checks if the given metric (defined in the qc_threshold model, value extracted from qc_json)
    satisfies the QC targets.

    Args:
        qc_threshold (QC_threshold): Pydantic model
        qc_json (QC_json): Pydantic model

    Raises:
        GenericQcException: QC metric {metric} in ruleset not found in QC json
        GenericQcException: The ruleset contains an unsupported operator

    Returns:
        str: pass, warn or fail
    """
    metric = qc_threshold.metric
    qc_json_value = next(
        (item for item in qc_json.qc_values if item.key == metric), None
    )

    if not qc_json_value:
        raise GenericQcException(f"QC metric '{metric}' in ruleset not found in QC json")

    def evaluate_target(value, operator, target):
        if operator == ">":
            return value > target
        elif operator == ">=":
            return value >= target
        elif operator == "<":
            return value < target
        elif operator == "<=":
            return value <= target
        elif operator == "==":
            return value == target
        elif operator == "!=":
            return value != target
        else:
            raise GenericQcException(
                f"The ruleset contains an unsupported operator: {operator}"
            )
        
    result = FAIL
    if evaluate_target(qc_json_value.value, qc_threshold.operator, qc_threshold.pass_target):
        result = PASS
    elif evaluate_target(qc_json_value.value, qc_threshold.operator, qc_threshold.warn_target):
        result = WARN

    if qc_threshold.use_as_qc_flag:
            qc_json_value.flag = result # Update individual QC flags. This will be patched to the portal
    return result


def evaluate_qc_ruleset(qc_json_, qc_ruleset: QC_ruleset):
    """For given input file, calculated qc metrics and user defined ruleset,
     returns an updated qc_json with indivifual QC flags set and the overall QC flag

    Args:
        input_wf_arg_name (string): input workflow argument that the QCs are validated for
        qc_json_ (Dict): qc json that has been persisted as file
        qc_ruleset_ (QC_rulesets): ruleset that is defined in the workflow

    Raises:
        GenericQcException: The overall_quality_status_rule contains metric IDs that are not defined in the rulset.
    """

    try:
        qc_json = QC_json(**qc_json_)
    except ValidationError as e:
        raise GenericQcException(
            f"The contents of the QC json file has the wrong format: {e}"
        )

    evaluated_qc_thresholds = {}
    for qct in qc_ruleset.qc_thresholds:
        evaluated_qc_thresholds[qct.id] = evaluate_qc_threshold(qct, qc_json)

    # Insert the evaluated QC thresholds in the logical expression for the overall quality. Then evaluate it.
    are_all_qc_pass = True # Keep track if any of the evaluated QCs is not PASS.
    for metric_id in evaluated_qc_thresholds:
        are_all_qc_pass = (are_all_qc_pass and (evaluated_qc_thresholds[metric_id] == PASS))
        eqt_bool_str = "True" if evaluated_qc_thresholds[metric_id] in [PASS, WARN] else "False"
        qc_ruleset.overall_quality_status_rule = qc_ruleset.overall_quality_status_rule.replace(f"{{{metric_id}}}", eqt_bool_str)

    # Not all "{metric_id}"" have been replaced in the logical expression string. This would also fail
    # during evaluation but we want to return a more useful error message here.
    if "{" in qc_ruleset.overall_quality_status_rule:
        raise GenericQcException(
            f"The overall_quality_status_rule contains metric IDs that are not defined in the ruleset."
        )

    Lep = LogicalExpressionParser(qc_ruleset.overall_quality_status_rule)
    overall_quality_status = Lep.evaluate()
    # If the supplied logical expression evalutes to true, set the overall status to PASS only if all of the
    # individual QCs are also PASS. If not set it to WARN
    if overall_quality_status and are_all_qc_pass:
        overall_quality_status = PASS
    elif overall_quality_status and not are_all_qc_pass:
        overall_quality_status = WARN
    else: 
        overall_quality_status = FAIL

    return qc_json.model_dump(), overall_quality_status


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
