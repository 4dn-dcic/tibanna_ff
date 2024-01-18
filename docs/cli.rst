=================
Key CLI functions
=================

CLI entrypoints for unicorn, pony and zebra are as follows. With ``-h`` option, one can see the list of subcommands available for each.

::

    tibanna -h
    tibanna_4dn -h
    tibanna_cgap -h
    tibanna_smaht -h


Tibanna Deployment
++++++++++++++++++

::

    tibanna deploy_unicorn [options]


::

    tibanna_4dn deploy_pony [options]


::

    tibanna_cgap deploy_zebra [options]

::

    tibanna_smaht deploy_tiger [options]



The above three are *not* interchangeable and each should be used to deploy a tibanna step function, lambdas and IAM permissions of its own kind.

Even for deploying a single lambda function, we should use the right entry point as below.


::

    tibanna deploy_core -n <lambda_name> [options]


::

    tibanna_4dn deploy_core -n <lambda_name> [options]


::

    tibanna_cgap deploy_core -n <lambda_name> [options]

::

    tibanna_samht deploy_core -n <lambda_name> [options]




Running Workflow
++++++++++++++++

::

    tibanna run_workflow -i <input_json> --sfn=<stepfunctionname>


::

    tibanna_4dn run_workflow -i <input_json> --sfn=<stepfunctionname>


::

    tibanna_cgap run_workflow -i <input_json> --sfn=<stepfunctionname>


::

    tibanna_smaht run_workflow -i <input_json> --sfn=<stepfunctionname>



