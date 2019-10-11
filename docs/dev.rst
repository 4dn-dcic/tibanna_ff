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

Metadata (overview)
+++++++++++++++++++

Pony and Zebra behave in a very similar way, with just a few very specific differences (see below). For every workflow run, they create a ``WorkflowRun`` object (``WorkflowRunAwsem`` more specifically, which inherits from ``WorkflowRun``) with a new ``uuid`` and an ``awsem_job_id`` that matches the job id of the run. They also create ``FileProcessed`` items for output files that we want to keep (``Output processed file``) that has a legit file format defined in the portal (e.g. ``bam``), sometimes has an accompanying file (``extra_file``), again with a legit file format (e.g. ``bai``). Not all workflow runs create a processed file output and depending on the type of output, a ``QualityMetric`` object may be created (``Output QC file``) or some field of the input file may be filled (e.g. ``md5sum`` and ``file_size``) (``Output report file``) or a new extra file of an input file (``Output to-be-extra-input file``) may be created. Each of the ``FileProcessed`` and ``QualityMetric`` objects created is assigned a new ``uuid``. Input files, processed files and ``QualityMetric`` objects are linked from the current ``WorkflowRun`` object and the ``QualityMetric`` objects are linked from a specified file (either input or processed).

If you rerun the same workflow run, it will not overwrite the existing ``WorkflowRun``, ``FileProcessed`` or ``QualityMetric`` objects, but will create new ones. However, if a ``QualityMetric`` item is linked from any input file, this link would be replaced by the new ``QualityMetric``. The old ``QualityMetric`` will still exist but just not linked from the input file any more. However, if the workflow run creates a new ``extra_file`` of an input file, a rerun will replace the file on ``S3`` without changing the metadata of the input file. This is harder to trace, so to be safe, one can use an option ``"overwrite_input_extra" : true`` to allow the overwrite - without this option, by default, the rerun will fail to start.

The metadata are created at the beginning of a workflow run except ``QualityMetric`` objects. At the end of a run, they are patched with the status. If the run is successful, the ``WorkflowRun`` object is patched a status ``complete``. If there was an error, it is patched a status ``error``.

A resource metric report is linked from ``WorkflowRun`` at the end of each run as a ``QualityMetricWorkflowrun`` object. 


Config
++++++

The ``config`` of pony/zebra input json is directly passed to unicorn and is pretty much the same. There are some additional ``fields`` for pony and zebra that can be specified in ``config``.

Additional fields for pony and zebra
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- ``"overwrite_input_extra" : true|false`` (default ``false``) : if an output file type is ``Output to-be-extra-input file``, a rerun of the same workflow run will fail to start unless this flag is set to be ``true``, to protect an existing extra file of an input file created by a previous run or an existing run that will create an extra file of an input file. One should use this flag only if one is sure that the previous or the current run has a problem and the output needs to be overwritten.

- ``"email" : true|false`` (default ``false``) : if this flag is set to be ``true``, it will send an email from ``4dndcic@gmail.com`` to itself (in case of ``pony``) or ``cgap.everyone@gmail.com`` to itself (in case of ``zebra``). To enable this to work, I had manually registered and verified these two emails on AWS Simple Email Service (SES). Since, it requires a manual registration of an email, it is not currently supported by Unicorn.


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


Output file handling
++++++++++++++++++++

There are four types of output - ``processed file``, ``QC file``, ``report file`` and ``to-be-extra-input file``.


Output processed file handling
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Tibanna creates a FileProcessed item for each processed file output in the beginning of the workflow run (through ``start_run``) and patches the object at the end of the run for ``status``, ``md5`` and ``file_size`` (through ``update_ffmeta``).


Quality metric handling
~~~~~~~~~~~~~~~~~~~~~~~


For QC type output, Tibanna does not create a FileProcessed item but instead creates a QualityMetric item. The quality metric item is created at the *end* of a workflow run, not at the *beginning*, since it is linked from one of the File items (either input or output) involved and if we create a new QualityMetric object in the beginning, it would inevitably replace the existing one, and if the run failed, the new one would remain linked despite the fact that the run failed.

An example QC type output is the output of a ``fastqc`` run or a ``pairsqc`` run, which is a zipped file containing an html file, some text files and image files to be used by the html. However, a regular, non-QC workflow may also create a QC-type output. For example, each of the first few steps of the CGAP upstream pipeline creates a bam file along with a simple QC called ``bam-check`` which simply checks that the bam file has a header and is not truncated. These workflows have two (or more, in case there are additional output) output files, one ``Out processed file`` which is the ``bam`` file and one ``Output QC file`` which is the ``bam-check` report. This ``bam-check`` report does not have any html file and is not zipped. It's a single text file, which is parsed to create a ``QualityMetricBamcheck`` object.

To allow flexibility in the format of QC type output, certain qc flags are specified in the ``Workflow`` object (*not* in the tibanna input json), in the ``arguments`` field. There may be multiple QC type output files for a single workflow run, and for each, the following must be specified

- ``"qc_zipped": true|false`` : the output file is zipped
- ``"qc_html": true|false`` : the output file is an html file
- ``"qc_json": true|false`` : the output file is a json file
- ``"qc_table": true|false`` : the output file is a table file (tab-delimited text file)
- ``"qc_zipped_html": <name_of_html_file>`` : the name of the html file in case the output zipped file contains an html file
- ``"qc_zipped_tables": <array_of_name(or_suffix)_of_table_files>`` : the name of the table files in case the output zipped file contains table files.
- ``"qc_type": <name_of_quality_metric_type>`` : name of the QC metric type (e.g. ``quality_metric_fastqc``, ``quality_metric_bamcheck``)
- ``"argument_to_be_attached_to": <argument>`` : the workflow argument name of the file (either input or output) from which the ``QualityMetric`` object should be linked. (e.g. if the QualityMetric object will be link to the processed bam file whose argument name is ``raw_bam``, this field can be set to ``raw_bam``.) 


As you can see above, a text-style QC output can either be a JSON or a TSV format. The main difference is that if the output is a TSV format, the corresponding fields must exist and be specified in the schema of the QualityMetric item. A JSON-format output goes directly to the QualityMetric item, and to allow this, the schema must have ``additional_properties`` to be set ``true``.



Report-type output handling
~~~~~~~~~~~~~~~~~~~~~~~~~~~

A report-type output is different from a QC-type output in that no ``QualityMetric`` object is created out of it. A good example of a report-type output is ``md5`` which calculates the ``md5sum`` of an input file and the result report output file that contains the ``md5sum`` value is parsed and the value is patched to the ``md5sum`` (and ``content_md5sum`` if the file is compressed) of the input ``File`` item.


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

