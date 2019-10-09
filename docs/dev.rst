=================
Developers' guide
=================

This section is for developers who want to understand the structure of the code arragements and details of the features and behaviors that are intended for Tibanna Unicorn, Pony and Zebra (the latter two specifically designed for 4DNucleome and CGAP (Clinical Genome Analysis Platform) data portals).


Overview of the Tibanna code structure
--------------------------------------

Tibanna Pony (``tibanna_4dn``) and Zebra (``tibanna_cgap``) are built upon Tibanna Unicorn (``tibanna``, independent of any data portal). Code for Pony and Zebra uses code for Unicorn by either importing or inheriting. The code shared between Pony and Zebra that are not a part of Unicorn is stored in the shared component ``tibanna_ffcommon``. All of these use AWSEM (Automonous Workflow Step Executor Machine) at the core, which is an EC2 instance that is auto-configured by Tibanna that does its job automonously and terminates itself at the end.


Repository & Directory structure
++++++++++++++++++++++++++++++++

- https://github.com/4dn-dcic/tibanna

    - ``tibanna`` : code for Unicorn
    - ``awsf`` : code that runs on AWSEM (commonly used by Unicorn, Pony and Zebra)

- https://github.com/4dn-dcic/tibanna_ff

    - ``tibanna_4dn`` : code for Pony
    - ``tibanna_cgap`` : code for Zebra
    - ``tibanna_ffcommon`` : code shared between Pony and Zebra that are not part of Unicorn

Each of the three variants (Unicorn, Pony or Zebra) consists of a core API (``core.py``), CLI (``__main__.py``), lambdas (``/lambdas``) and set of python modules that are used by the former three.


Installation
------------

Installation and dependencies
+++++++++++++++++++++++++++++

To install ``tibanna``,

::

    pip install tibanna


::

    > import tibanna


::

    tibanna -h



To install ``tibanna_4dn`` and ``tibanna_cgap``,

::

    pip install tibanna_ff
    # or pip install tibanna-ff

::

    > import tibanna_4dn
    > import tibanna_cgap
    > import tibanna_ffcommon


::

    tibanna_4dn -h
    tibanna_cgap -h



Environment variables
+++++++++++++++++++++

The following environment variables are required for ``tibanna``, unless ``.aws/credentials`` and ``.aws/config`` are set up.


::

    export AWS_ACCESS_KEY_ID=<aws_key>
    export AWS_SECRET_ACCESS_KEY=<aws_secret_key>
    export AWS_DEFAULT_REGION=<aws_region>


To use ``tibanna_4dn`` or ``tibanna_cgap``, the following environment variable is additionally required. (This is available only for the 4DN/CGAP developer team.)


::

    export S3_ENCRYPT_KEY=<fourfront_s3_encrypt_key>




Key functions
-------------

Tibanna Deployment
++++++++++++++++++

::

    tibanna deploy_unicorn [options]


::

    tibanna_4dn deploy_pony [options]


::

    tibanna_cgap deploy_zebra [options]



The above three are *not* interchangeable and each should be used to deploy a tibanna stepfunction of its own kind.

Even for deploying a single lambda function, we should use the right entry point as below.


::

    tibanna deploy_core -n <lambda_name> [options]


::

    tibanna_4dn deploy_core -n <lambda_name> [options]


::

    tibanna_cgap deploy_core -n <lambda_name> [options]




Running Workflow
++++++++++++++++

::

    tibanna run_workflow -i <input_json> --sfn=<stepfunctionname>


::

    tibanna_4dn run_workflow -i <input_json> --sfn=<stepfunctionname>


::

    tibanna_cgap run_workflow -i <input_json> --sfn=<stepfunctionname>



The above three can be used interchageably, as long as the correct step function name is used. i.e. the following command still works and would submit a job to ``tibanna_pony`` even if the entry point ``tibanna_cgap`` was used.


::

    tibanna_cgap run_workflow -i <input_json> --sfn=tibanna_pony




Behaviors
---------

Config
++++++

The `config` of pony/zebra input json is directly passed to unicorn and is pretty much the same.


Input file handling
+++++++++++++++++++



Dimension
~~~~~~~~~

An input file may have dimension 0~3 (single element, a 1D array, a 2D array, or a 3D array).


Extra files
~~~~~~~~~~~

An input file may have extra files. Extra files are equivalent to secondary files in CWL, and usually includes index files (e.g. ``px2``, ``idx``, ``tbi``, ``bai``, ``fai``, ...). If there are multiple extra files, they should have different formats (extensions). The workflow objects and Tibanna input jsons do not have to specify any extra files and all the extra files associated with a specified input file's File object is automatically transferred along with the file itself to the AWSEM instance.

However, it is required that the input file's File object does contain a corresponding extra file, if CWL requires a secondary file for that input.


Renaming files
~~~~~~~~~~~~~~

The file key on S3 follows the convention ``<uuid>/<accession>.<extension>``. Some workflows require some input files to have specific names and to handle this problem, we use the field ``rename`` in the individual input file dictionary in the input json to specify the target name. When the file is downloaded to the AWSEM instance, before running the workflow, the file will be renamed to this target name. By default, it will be the same as the key on S3.


Output handling
+++++++++++++++

There are four types of output - ``processed file``, ``QC file``, ``report file`` and ``to-be-input-extra file``.


Output processed file handling
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Quality metric handling
~~~~~~~~~~~~~~~~~~~~~~~

Report-type output handling
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Handling output that becomes an extra file of an input file
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


Custom fields
+++++++++++++

Custom fields for processed files
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Custom fields for quality metrics
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Custom fields for workflow run
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

