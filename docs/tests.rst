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

Currently ``fourfront-webdev`` is used as a main Tibanna test portal for 4DN, and ``fourfront-cgap`` for CGAP.


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
    

Tests on deployed dev tibanna
+++++++++++++++++++++++++++++

Testing on a dev tibanna requires spinning up EC2 instances and it costs $$. So this test should be done only when we're confident about our modifications and after all the local tests already passed.

To run a deployment-based test, do the following.

Pony
~~~~

::

   tibanna_4dn deploy_pony -s dev
   tibanna_4dn run_workflow -s tibanna_pony_dev -s <testjson>
   

Zebra
~~~~~

::
   
   tibanna_cgap deploy_zebra -s dev
   tibanna_cgap run_workflow -s tibanna_zebra_dev -i test_json/zebra/md5.json
   tibanna_cgap run_workflow -s tibanna_zebra_dev -i test_json/zebra/fastqc.json
   tibanna_cgap run_workflow -s tibanna_zebra_dev -i test_json/zebra/bwa-check.json
   

Production Deployment
+++++++++++++++++++++

After all the tests pass, we should deploy production tibanna.

::

    tibanna_4dn deploy_pony
    tibanna_4dn deploy_pony -s tmp_md5  # md5/fastqc triggers
    tibanna_4dn deploy_pony -g default_luisa  # luisa's tibanna, with different permission
    
    tibanna_cgap deploy_zebra
    tibanna_cgap deploy_zebra -s tmp_md5  # md5/fastqc triggers


