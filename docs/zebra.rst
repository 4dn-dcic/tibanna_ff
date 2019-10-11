======================
Tibanna Zebra for CGAP
======================

Tibanna Zebra is an extension of Tibanna Unicorn used specifically for CGAP (Clinical Genome Analysis Platform). Zebra has two additional steps that communicate with the CGAP Data Portal and handle CGAP metadata. Zebra is only for CGAP and requires access keys to the Data Portal and the CGAP AWS account.


=================  ==================
 Tibanna Unicorn    Tibanna Zebra
=================  ==================
|tibanna_unicorn|  |tibanna_zebra|
=================  ==================

.. |tibanna_unicorn| image:: images/screenshot_tibanna_unicorn.png
.. |tibanna_zebra| image:: images/screenshot_tibanna_zebra.png


Example Tibanna setup for CGAP
------------------------------

To deploy zebra, you could do the following.

::

    tibanna_cgap deploy_zebra
