=====================
Production Deployment
=====================


After all the tests pass, we should deploy production tibanna as below.

Pony
++++

::

    tibanna_4dn deploy_pony
    tibanna_4dn deploy_pony -s tmp_md5  # md5/fastqc triggers
    tibanna_4dn deploy_pony -g default_luisa  # luisa's tibanna, with different permission


Zebra
+++++

::
    
    tibanna_cgap deploy_zebra
    tibanna_cgap deploy_zebra -s tmp_md5  # md5/fastqc triggers

