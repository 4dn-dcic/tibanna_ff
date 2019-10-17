=============================
Installation and dependencies
=============================

Installation
++++++++++++

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
