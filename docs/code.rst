======================================
Overview of the Tibanna code structure
======================================

Tibanna Pony (``tibanna_4dn``) and Zebra (``tibanna_cgap``) are built upon Tibanna Unicorn (``tibanna``, independent of any data portal). Code for Pony and Zebra uses code for Unicorn by either importing or inheriting. The code shared between Pony and Zebra that are not a part of Unicorn is stored in the shared component ``tibanna_ffcommon``. All of these use AWSEM (Automonous Workflow Step Executor Machine) at the core, which is an EC2 instance that is auto-configured by Tibanna that does its job automonously and terminates itself at the end.


Repository & Directory structure
--------------------------------

- https://github.com/4dn-dcic/tibanna

    - ``tibanna`` : code for Unicorn
    - ``awsf`` : code that runs on AWSEM (commonly used by Unicorn, Pony and Zebra)

- https://github.com/4dn-dcic/tibanna_ff

    - ``tibanna_4dn`` : code for Pony
    - ``tibanna_cgap`` : code for Zebra
    - ``tibanna_ffcommon`` : code shared between Pony and Zebra that are not part of Unicorn

Each of the three variants (Unicorn, Pony or Zebra) consists of a core API (``core.py``), CLI (``__main__.py``), lambdas (``/lambdas``) and set of python modules that are used by the former three.



AWSEM
-----

The code in ``awsf`` is not a part of any Python package, but the scripts in the folder is pulled by an AWSEM EC2 instance directly from the public tibanna Github repo. Currently, ``awsf`` is still using Python 2.7, whereas all the other code is based on Python 3.6. The reason ``awsf`` uses Python 2.7 is because it runs on the pre-built Tibanna AMI which is based on Python 2.7 and we haven't updated the AMI yet.


AWS Lambda
----------

The code for individual AWS Lambda functions is defined in individual ``.py`` files inside the ``lambdas`` directory under the package directory (e.g. ``tibanna_4dn``, ``tibanna_cgap``, or in case of unicorn, ``tibanna`` in the ``tibanna`` repo.)


Unicorn
+++++++

A Unicorn consists of two AWS Lambda functions - ``run_task_awsem`` and ``check_task_awsem``.


Pony
++++

A Pony step function consists of four Lambda functions - in addition to ``run_task_pony``, ``check_task_pony``, it has ``start_run_pony`` and ``update_ffmeta_pony``. Additionally, ``tibanna_4dn``'s ``deploy_pony`` and ``deploy_core`` functions allow deploying other Lambdas that are not a part of a Pony step function. These include the following:

- ``run_workflow_pony`` : a Lambda function that triggers a workflow run on the ``tibanna_pony`` step function, that serves as a fourfront endpoint.
- ``validate_md5_s3_trigger_pony`` : a Lambda function that gets triggered upon file upload to a fourfront bucket. Once triggered, it invokes ``tibanna_initiator`` step function which in turn invokes ``validate_md5_s3_initiator_pony`` Lambda.
- ``validate_md5_s3_initiator_pony`` : a Lambda function that triggers ``md5sum`` and ``fastqc`` workflow runs on the ``tibanna_pony_tmp_md5`` step function.
- ``status_wfr_pony`` : a mysterious Lambda function that does something

The ``.py`` files for the Lambdas do not have the suffix ``pony`` in their file names, but the Lambdas do always have the suffix, to differentiate them from unicorn or zebra Lambdas.


Zebra
+++++

Like Pony, a Zebra step function consists of four Lambda functions - in addition to ``run_task_zebra``, ``check_task_zebra``, it has ``start_run_zebra`` and ``update_ffmeta_zebra``. Additionally, ``tibanna_cgap``'s ``deploy_zebra`` and ``deploy_core`` functions allow deploying other Lambdas that are not a part of a Zebra step function. These include the following:

- ``run_workflow_zebra`` : a Lambda function that triggers a workflow run on the ``tibanna_pony`` step function, that serves as a fourfront endpoint.
- ``validate_md5_s3_trigger_zebra`` : a Lambda function that gets triggered upon file upload to a cgap bucket. Once triggered, it invokes ``tibanna_initiator_zebra`` step function which in turn invokes ``validate_md5_s3_initiator_zebra`` Lambda.
- ``validate_md5_s3_initiator_zebra`` : a Lambda function that triggers ``md5sum`` and ``fastqc`` workflow runs on the ``tibanna_zebra_tmp_md5`` step function.
- ``status_wfr_zebra`` : a mysterious Lambda function that does something

The ``.py`` files for the Lambdas do not have the suffix ``zebra`` in their file names, but the Lambdas do always have the suffix, to differentiate them from unicorn or pony Lambdas.


AWS Step Functions
------------------

The code that describes a step function structure is in ``stepfunction.py`` in ``tibanna``, ``tibanna_ffcommon``, ``tibanna_4dn`` and ``tibanna_cgap``. The step function class of ``tibanna_4dn`` (class ``StepFunctionPony``) and ``tibanna_cgap`` (class ``StepFunctionZebra``) inherit from that of ``tibanna_ffcommon`` (class ``StepFunctionFFAbstract``) which in turn inherits from that of ``tibanna`` (class ``StepFunctionUnicorn``). Class ``StepFunctionFFAbstract`` is not an actually functional step function but works as a common component that both ``StepFunctionPony`` and ``StepFunctionZebra`` can inherit from.


