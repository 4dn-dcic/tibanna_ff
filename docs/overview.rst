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
    - ``tibanna_smaht`` : code for Tiger
    - ``tibanna_ffcommon`` : code shared between Pony, Zebra and Tiger that are not part of Unicorn

Each of the four variants (Unicorn, Pony, Zebra and Tiger) consists of a core API (``core.py``), CLI (``__main__.py``), lambdas (``/lambdas``) and set of python modules that are used by the former three.


Lambda code
-----------

The code for individual AWS Lambda functions is defined in individual ``.py`` files inside the ``lambdas`` directory under the package directory (e.g. ``tibanna_4dn``, ``tibanna_cgap``, or in case of unicorn, ``tibanna`` in the ``tibanna`` repo.)


Unicorn
+++++++

A Unicorn consists of two AWS Lambda functions - ``run_task_awsem`` and ``check_task_awsem``.


Pony
++++

A Pony consists of four Lambda functions - in addition to ``run_task_pony``, ``check_task_pony``, it has ``start_run_pony`` and ``update_ffmeta_pony``. Additionally, ``tibanna_4dn``'s ``deploy_pony`` and ``deploy_core`` functions allow deploying other Lambdas that are not a part of a Pony step function. These include the following:

- ``run_workflow_pony`` : a Lambda function that triggers a workflow run on the ``tibanna_pony`` step function, that serves as a fourfront endpoint.
- ``validate_md5_s3_trigger_pony`` : a Lambda function that gets triggered upon file upload to a fourfront bucket. Once triggered, it invokes ``tibanna_initiator`` step function which in turn invokes ``validate_md5_s3_initiator_pony`` Lambda.
- ``validate_md5_s3_initiator_pony`` : a Lambda function that triggers ``md5sum`` and ``fastqc`` workflow runs on the ``tibanna_pony_tmp_md5`` step function.
- ``status_wfr_pony`` : a mysterious Lambda function that does something

The ``.py`` files for the Lambdas do not have the suffix ``pony`` in their file names, but the Lambdas do always have the suffix, to differentiate them from unicorn or zebra Lambdas.


Zebra
+++++

A Zebra consists of four Lambda functions - in addition to ``run_task_zebra``, ``check_task_zebra``, it has ``start_run_zebra`` and ``update_ffmeta_zebra``. Additionally, ``tibanna_cgap``'s ``deploy_zebra`` and ``deploy_core`` functions allow deploying other Lambdas that are not a part of a Zebra step function. These include the following:

- ``run_workflow_zebra`` : a Lambda function that triggers a workflow run on the ``tibanna_pony`` step function, that serves as a fourfront endpoint.
- ``validate_md5_s3_trigger_zebra`` : a Lambda function that gets triggered upon file upload to a cgap bucket. Once triggered, it invokes ``tibanna_initiator_zebra`` step function which in turn invokes ``validate_md5_s3_initiator_zebra`` Lambda.
- ``validate_md5_s3_initiator_zebra`` : a Lambda function that triggers ``md5sum`` and ``fastqc`` workflow runs on the ``tibanna_zebra_tmp_md5`` step function.
- ``status_wfr_zebra`` : a mysterious Lambda function that does something

The ``.py`` files for the Lambdas do not have the suffix ``zebra`` in their file names, but the Lambdas do always have the suffix, to differentiate them from unicorn or pony Lambdas.
