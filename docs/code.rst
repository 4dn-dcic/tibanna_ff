======================================
Overview of the Tibanna code structure
======================================

Tibanna Pony (``tibanna_4dn``), Zebra (``tibanna_cgap``) and Tiger (``tibanna_smaht``)  are built upon Tibanna Unicorn (``tibanna``, independent of any data portal). Code for Pony, Zebra and Tiger uses code for Unicorn by either importing or inheriting. The code shared between Pony, Zebra and Tiger that are not a part of Unicorn is stored in the shared component ``tibanna_ffcommon``. All of these use AWSEM (Automonous Workflow Step Executor Machine) at the core, which is an EC2 instance that is auto-configured by Tibanna that does its job automonously and terminates itself at the end.


Repository & Directory structure
--------------------------------

- https://github.com/4dn-dcic/tibanna

    - ``tibanna`` : code for Unicorn
    - ``awsf3`` : code that runs on AWSEM (commonly used by Unicorn, Pony, Zebra and Tiger)

- https://github.com/4dn-dcic/tibanna_ff

    - ``tibanna_4dn`` : code for Pony
    - ``tibanna_cgap`` : code for Zebra
    - ``tibanna_smaht`` : code for SMaHT
    - ``tibanna_ffcommon`` : code shared between Pony and Zebra that are not part of Unicorn

Each of the four variants (Unicorn, Pony, Zebra, Tiger) consists of a core API (``core.py``), CLI (``__main__.py``), lambdas (``/lambdas``) and set of python modules.



AWSEM
-----

The code in ``awsf3`` is not a part of any Python package, but the scripts in the folder is pulled by an AWSEM EC2 instance directly from the public Tibanna Github repo. 


AWS Lambda
----------

The code for individual AWS Lambda functions is defined in individual ``.py`` files inside the ``lambdas`` directory under the package directory (e.g. ``tibanna_4dn``, ``tibanna_cgap``, ``tibanna_smaht``)


Unicorn
+++++++

A Unicorn consists of two AWS Lambda functions - ``run_task_awsem`` and ``check_task_awsem``.


Pony
++++

A Pony step function consists of four Lambda functions - in addition to ``run_task_pony``, ``check_task_pony``, it has ``start_run_pony`` and ``update_ffmeta_pony``. 

The ``.py`` files for the Lambdas do not have the suffix ``pony`` in their file names, but the Lambdas do always have the suffix, to differentiate them from unicorn or zebra Lambdas.


Zebra
+++++

Like Pony, a Zebra step function consists of four Lambda functions - in addition to ``run_task_zebra``, ``check_task_zebra``, it has ``start_run_zebra`` and ``update_ffmeta_zebra``.

The ``.py`` files for the Lambdas do not have the suffix ``zebra`` in their file names, but the Lambdas do always have the suffix, to differentiate them from unicorn or pony Lambdas.


Tiger
+++++

Like Zebra, where ``zebra`` is replaced with ``tiger`` in the everywhere.


AWS Step Functions
------------------

The code that describes a step function structure is in ``stepfunction.py`` in ``tibanna``, ``tibanna_ffcommon`` and ``tibanna_{4dn,cgap,smaht}``. The step function class of ``tibanna_4dn`` (class ``StepFunctionPony``), ``tibanna_cgap`` (class ``StepFunctionZebra``) and ``tibanna_smaht`` (class ``StepFunctionTiger``) inherit from that of ``tibanna_ffcommon`` (class ``StepFunctionFFAbstract``) which in turn inherits from that of ``tibanna`` (class ``StepFunctionUnicorn``). Class ``StepFunctionFFAbstract`` is not an actually functional step function but works as a common component that ``StepFunction{Pony,Zebra,Tiger}`` can inherit from.


