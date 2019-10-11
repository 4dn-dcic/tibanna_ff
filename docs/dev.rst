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




Key CLI functions
-----------------

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


There are also recommended fields for pony and zebra, even though they are not pony/zebra-specific (unicorn also supports these features).

Recommended fields for pony and zebra
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- ``"public_postrun_json" : true`` : it is recommended to set this flag to ``true`` so that the postrun json files are open to public.
- ``"key_name": "4dn-encoded"`` : for security reasons, it is recommended to use the ``4dn-encoded`` key rather than just passwords for sshing to an AWSEM instance.


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

Tibanna creates a FileProcessed item for each processed file output in the beginning of the workflow run (through ``start_run``) with status ``to be uploaded by workflow``. At the end of the run, it patches the ``FileProcessed`` objects with ``status`` (``uploaded``), ``md5`` and ``file_size`` (through ``update_ffmeta``).

If an output processed file has an extra file, likewise the metadata for the extra files will also be created in the beginning of the run, with status ``to be uploaded by workflow``. At the end of the run, the extra files will be patched with ``status`` (``uploaded``), ``md5`` and ``file_size`` (through ``update_ffmeta``). In order for an output processed file to have an extra file(s), the ``secondary_file_formats`` must be specified in the ``workflow`` ``arguments`` field for the corresponding output processed file.


Quality metric handling
~~~~~~~~~~~~~~~~~~~~~~~


For QC type output, Tibanna does not create a FileProcessed item but instead creates a QualityMetric item. The quality metric item is created at the *end* of a workflow run, not at the *beginning*, since it is linked from one of the File items (either input or output) involved and if we create a new QualityMetric object in the beginning, it would inevitably replace the existing one, and if the run failed, the new one would remain linked despite the fact that the run failed.

An example QC type output is the output of a ``fastqc`` run or a ``pairsqc`` run, which is a zipped file containing an html file, some text files and image files to be used by the html. However, a regular, non-QC workflow may also create a QC-type output. For example, each of the first few steps of the CGAP upstream pipeline creates a bam file along with a simple QC called ``bam-check`` which simply checks that the bam file has a header and is not truncated. These workflows have two (or more, in case there are additional output) output files, one ``Out processed file`` which is the ``bam`` file and one ``Output QC file`` which is the ``bam-check`` report. This ``bam-check`` report does not have any html file and is not zipped. It's a single text file, which is parsed to create a ``QualityMetricBamcheck`` object.

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

We may have multiple QC output files for a single workflow, but with restrictions. Tibanna will segregate the QC output files by ``argument_to_be_attached_to``. Let's say there are three QC output files and two of them are associated with ``out_bam`` and the third one is associated with ``out_bw``. The first two will be merged into a single ``QualityMetric`` object, and the third one will be its own ``QualityMetric`` object, i.e. Tibanna will create two ``QualityMetric`` objects even though there are three QC output files, because there are only two distinct groups based on ``argument_to_be_attached_to``. The first two QC output files must have the same ``qc_type``, but may be a different format - e.g. one of them is html and the other one is JSON. A ``File`` item is never associated with more than two ``QualityMetric`` objects of the same type.

Tibanna checks if the ``File`` item to associate a new ``QualityMetric`` object already has any ``QualityMetric`` associated with it. If it does, Tibanna does the following.

1. If the existing ``QualityMetric`` object is the same type as the new ``QualityMetric`` object, replace the old one with the new one.
2. If the existing ``QualityMetric`` object is of a different type from the new ``QualityMetric`` object, create a new ``QualityMetricQclist`` object and link it to the corresponding ``File`` object, move the old ``QualityMetric`` object to the ``QualityMetricQclist`` object, and add a new ``QualityMetric`` object to the ``QualityMetricQclist`` object.
3. If the existing ``QualityMetric`` object is of type ``QualityMetricQclist``, check the types of ``QualityMetric`` objects inthe ``QualityMetricQclist`` object, and if there exists a ``QualityMetric`` object of the same type as the new ``QualityMetric`` object, replace this one with the new one. If not, add the new ``QualityMetric`` object to the existing ``QualityMetricQclist`` object.

In theory, a single workflow run could create multiple ``QualityMetric`` types by creating a new ``QualityMetricQclist`` and adding all of the ``QualityMetric`` objects to it, but currently Tibanna does not support it. It may be implemented if we have a case where multiple types of QC is generated by a single workflow for a single file item. 


Report-type output handling
~~~~~~~~~~~~~~~~~~~~~~~~~~~

A report-type output is different from a QC-type output in that no ``QualityMetric`` object is created out of it. A good example of a report-type output is ``md5`` which calculates the ``md5sum`` of an input file and the result report output file that contains the ``md5sum`` value is parsed and the value is patched to the ``md5sum`` (and ``content_md5sum`` if the file is compressed) of the input ``File`` item.


Handling output that becomes an extra file of an input file
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

An example of an ``Output to-be-extra-input file`` is the output of workflow ``bed2beddb`` where the output ``beddb`` file will be attached as an ``extra_file`` of the input ``bed`` file, instead of creating a separate processed file with the ``beddb`` format.

By default, a second run of the same workflow run fails to start, to avoid overwriting the output extra file without any metadata log, unless ``"overwrite_input_extra": true`` is set in the ``config`` of the input json.

The extra file in the input ``File`` metadata is created at the beginning of the run (through ``start_run``) with status ``to be uploaded by workflow`` and the AWSEM instance will upload the output file to the right bucket with the right key including the right extension (the extension of the extra file). If this upload fails, ``check_task`` will throw and AWSEM error. The last step ``update_ffmeta`` will make sure that the key with the right extension exists in the right bucket, but it does *not* check that the file is new or not. If it does, it will update the status of the extra file to ``uploaded``.


Custom fields
+++++++++++++

In case we want to pass one custom fields to ``WorkflowRun``, ``FileProcessed`` or ``QualityMetric`` objects that are created by a workflow run, we can do that by adding custom fields to the input json. Common examples of custom field would be ``lab`` and ``award`` for pony and ``project`` and ``institution`` for zebra. One could also set ``genome_assembly`` to be passed to a ``FileProcessed`` object.


Custom fields for workflow run
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``wfr_meta`` field specifies custom fields to be passed to a ``WorkflowRun`` object.

::

    "wfr_meta": { "key1": "value1", "key2": "value2" ,,, }

In the above example, the ``WorkflowRun`` object will have field ``key1`` with value ``value1`` and field ``key2`` with value ``value2``.


Custom fields for processed files
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``custom_pf_fields`` field specifies custom fields to be passed to a ``FileProcessed`` object. This field has one additional level to specify whether the field should apply to all processed files (``ALL``) or a specific processed file (the argument name of the specific processed file).

::

    "custom_pf_fields": {
        "ALL": { "key1": "value1", "key2": "value2" },
        "out_bam": {"key3": "value3" }
    }
    
In the above example, if we have two output files with argument names ``out_bam`` and ``out_bw``, the processed file(s) associated with both ``out_bam`` and ``out_bw`` will have field ``key1`` with value ``value1`` and field ``key2`` with value ``value2``, but only the processed file(s) associated with ``out_bam`` will have field ``key3`` with value ``value3``.



Custom fields for quality metrics
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``custom_qc_fields`` field specifies custom fields to be passed to a ``FileProcessed`` object, and all the ``QualityMetric`` objects generated (including ``QualityMetricWorkflowrun``) will have the fields specified by ``custom_qc_fields``.

::

    "custom_qc_fields": { "key1": "value1", "key2": "value2" ,,, }


In the above example, all the ``QualityMetric`` objects will have field ``key1`` with value ``value1`` and field ``key2`` with value ``value2``.

