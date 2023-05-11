from .exceptions import (
    GenericQcException
)

def check_qc_workflow_args(input_file_args, generic_qc_args):
    """
    This function performs basic sanity checks on the QC and input files
    """

    workflow_argument_name_inputs = list(map(lambda inp:inp["workflow_argument_name"], input_file_args))
    for generic_qc_arg in generic_qc_args:
        wf_arg_name = generic_qc_arg['workflow_argument_name']
        arg_to_be_attached_to = generic_qc_arg['argument_to_be_attached_to']
        qc_json = generic_qc_arg['qc_json']
        qc_zipped = generic_qc_arg['qc_zipped']

        if not arg_to_be_attached_to:
            raise GenericQcException(f"{wf_arg_name} does not have argument_to_be_attached_to specified.")
        elif arg_to_be_attached_to not in workflow_argument_name_inputs:
            raise GenericQcException(f"{wf_arg_name}'s argument_to_be_attached_to does not exist.")
        elif int(qc_json) + int(qc_zipped) != 1:
            raise GenericQcException(f"Exactly one of qc_json or qc_zipped must be true.")
        
        
    for input_file_arg in input_file_args:
            # Get the associated QC args
            input_wf_arg_name = input_file_arg['workflow_argument_name']
            qc_args = filter_workflow_args_by_property(generic_qc_args, "argument_to_be_attached_to", input_wf_arg_name)
            if len(qc_args) == 0:
                continue
            # If there is only one Generic QC file, make sure it is the JSON with QC values
            elif len(qc_args) == 1 and not qc_args[0].get("qc_json"):
                raise GenericQcException(f"There is no QC JSON associated with input {input_wf_arg_name}")
            elif len(qc_args) == 2:
                # There must be one qc_json and one qc_zipped
                qc_args_json = filter_workflow_args_by_property(qc_args, "qc_json", True)
                qc_args_zipped = filter_workflow_args_by_property(qc_args, "qc_zipped", True)
                if len(qc_args_json) != 1 or len(qc_args_zipped) != 1:
                    raise GenericQcException(f"There are 2 Generic QC files associated with input {input_wf_arg_name}. One must have `qc_json` and the other `qc_zipped` set to true.")
            elif len(qc_args) > 2:
                raise GenericQcException(f"There are more than 2 Generic QC files for input {input_wf_arg_name}")
           

def filter_workflow_args_by_property(workflow_args, property, property_value):
    return [arg for arg in workflow_args if arg[property] == property_value]
    

