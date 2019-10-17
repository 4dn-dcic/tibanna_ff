======================================
Overview of the Tibanna code structure
======================================

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


