=====
Tests
=====

Whenever changes are made, we need to run tests.


Prerequisites
+++++++++++++

To run tests, first do

::

    pip install -r reqirements-test.txt


Also, before running any tests, make sure to first build based on the current repo content.

::

    python setup.py install
    


Test portals
++++++++++++

Currently ``fourfront-webdev`` is used as a main Tibanna test portal for 4DN, and ``fourfront-cgap`` is for CGAP.


Local tests
+++++++++++

Local tests run test scripts in the ``tests`` directory using ``pytest``.

Local tests do not involve spinning up any EC2 instance, but some of them involve uploading small files to S3 and posting minimal objects to test portals. After each such test, the files and posted items are deleted.

Local tests are a good starting point, but they're not comprehensive, because it doesn't involve any real EC2 instance, and the code is not run on an actual AWS Lambda environment. So this way, we cannot catch any Lambda deployment error or IAM permission setup error.

Running all local tests can be done by ``invoke test``. Some ``flake8`` tests are going to fail that we're not going to fix, so it is recommended to run this test without ``flake8``.

::

    invoke test --no-flake


To run your code through ``flake8``, it would be nice to do it script by script after modification, e.g.

::

    flake8 tibanna_4dn/check_task.py


To run individual test (to save time for testing while still working on the code), one could directly use ``pytest``, e.g.

::

    pytest tests/tibanna/pony/test_fourfrontupdater.py
    
    
Travis test
+++++++++++

Travis test is currently set up to run at every push and every PR. Travis test currently runs only local tests.


Tests on deployed dev tibanna
+++++++++++++++++++++++++++++

Testing on a dev tibanna requires spinning up EC2 instances and it costs $$. So this test should be done only when we're confident about our modifications and after all the local tests already passed.

To run a deployment-based test, do the following.

Pony
~~~~

::

   tibanna_4dn deploy_pony -s dev
   tibanna_4dn run_workflow -s tibanna_pony_dev -i test_json/pony/md5.json
   tibanna_4dn run_workflow -s tibanna_pony_dev -i test_json/pony/fastqc.json
   tibanna_4dn run_workflow -s tibanna_pony_dev -i test_json/pony/bwa-mem.json
   tibanna_4dn run_workflow -s tibanna_pony_dev -i test_json/pony/bed2beddb.json


Zebra
~~~~~

::
   
   tibanna_cgap deploy_zebra -s dev
   tibanna_cgap run_workflow -s tibanna_zebra_dev -i test_json/zebra/md5.json
   tibanna_cgap run_workflow -s tibanna_zebra_dev -i test_json/zebra/fastqc.json
   tibanna_cgap run_workflow -s tibanna_zebra_dev -i test_json/zebra/bwa-check.json


Integrated test (coming soon)
+++++++++++++++++++++++++++++

The following run_workflow tests are added as part of more rigorous automatic tests.

Four different output types
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Pony
----

- ``md5``, ``fastqc``, ``bwa-mem`` (with a small reference index file), ``bed2beddb`` (or ``bedgraph2bw``)
- ``QCList`` is not available for Fourfront.

Zebra
-----

- ``md5``, ``fastqc``, ``bwa-check`` (with a small reference index file).
  - We don't have to-be-extra-input type on CGAP yet.
- ``QCList`` test by running ``bamqc`` on top of ``bwa-check`` and then rerunning ``bamqc`` (must replace the first one).


Input array types
~~~~~~~~~~~~~~~~~

Pony
----

- ```merge_fastq`` with very small fastq files (1D array)
- ``merge_and_cut`` test workflow item (3D array)

Zebra
-----

- ```merge_bam``` with very small bam files (1D array)
- ``merge_and_cut`` test workflow item (3D array)


Reruns
~~~~~~

Pony
----

- md5 conflict test
  - rerun the same File item with a different md5 content (must fail)
  - rerun a different File item with the same md5 content (must fail)
- overwrite_extra test
  - rerun the same ``bed2beddb`` job with different file content with overwrite_extra = True (must overwrite)
  - rerun the same ``bed2beddb`` job with overwrite_extra = False (must fail)

Zebra
-----

- md5 conflict test
  - rerun the same File item with a different md5 content (must fail)
  - rerun a different File item with the same md5 content (must fail)
  
WDL
~~~

Pony
----

- ``merge`` WDL test workflow item (also 2D array test)

Zebra
-----

- ``merge`` WDL test workflow item (also 2D array test)


Workflow Run QC
~~~~~~~~~~~~~~~

- check html & tsv

EC2 test
~~~~~~~~

- EC2 unintended termination test (force kill externally)
- EC2 idle test (sleep for 1hr)



Other tests that we should include in the future
++++++++++++++++++++++++++++++++++++++++++++++++

The following tests are currently not set up and is done manually. Ideally they should be automated in the future.

- CLI test
- md5/fastqc trigger test
- initiator test
- permission tests

