=============================
Installation and dependencies
=============================

Installation
++++++++++++

To install ``tibanna``,

::

    pip install tibanna


If ``tibanna`` is installed correctly, you can do the following.

::

    > import tibanna


::

    # this requires AWS credential set up as well
    tibanna -h



To install ``tibanna_4dn`` and ``tibanna_cgap``,

::

    pip install tibanna_ff
    # or pip install tibanna-ff

If you install ``tibanna_ff``, ``tibanna`` will also be installed as its dependency. (no need to install ``tibanna`` separately)

If ``tibanna_ff`` is installed correctly, you can do the following.

::

    > import tibanna
    > import tibanna_4dn
    > import tibanna_cgap
    > import tibanna_ffcommon


::

    # these require AWS credential set up as well
    tibanna -h
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


Optionally, for both cases, the following environment variable can be set up to be able to skip specifying ``--sfn <step_function_name>`` for most functions including ``run_workflow`` and ``stat``.


::

    export TIBANNA_DEFAULT_STEP_FUNCTION_NAME=<step_function_name>


For example,

::

    export TIBANNA_DEFAULT_STEP_FUNCTION_NAME=tibanna_unicorn_monty

