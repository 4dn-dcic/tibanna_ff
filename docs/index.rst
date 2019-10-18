========
Overview
========

Tibanna_ff_ is an extension of Tibanna_ that integrates with 4DN/CGAP data portals. Tibanna is a software tool that helps you run genomic pipelines on the the Amazon (AWS) cloud. Tibanna_ff does the same but in integration with 4DN/CGAP data portal.

The generic Tibanna is called Unicorn, whereas the Tibanna_ff components that are specifically designed for 4DN (4DNucleome) and CGAP (Clinical Genome Analysis Platform) are called Pony and Zebra, respectively.


.. _Tibanna: https://github.com/4dn-dcic/tibanna
.. _Tibanna_ff: https://github.com/4dn-dcic/tibanna_ff

This documentation is written mostly for developers who want to understand the structure of the code arragements and details of the features and behaviors that are intended for Tibanna Unicorn, Pony and Zebra.


=================  ==============  ===============
 Tibanna Unicorn    Tibanna Pony    Tibanna Zebra
=================  ==============  ===============
|tibanna_unicorn|  |tibanna_pony|  |tibanna_zebra|
=================  ==============  ===============

.. |tibanna_unicorn| image:: images/screenshot_tibanna_unicorn.png
.. |tibanna_pony| image:: images/screenshot_tibanna_pony.png
.. |tibanna_zebra| image:: images/screenshot_tibanna_zebra.png


Tibanna Pony is an extension of Tibanna Unicorn used specifically for 4DN. Pony has two additional steps that communicate with the 4DN Data Portal and handle 4DN metadata. Pony requires access keys to the 4DN Data Portal and the 4DN DCIC AWS account.

Tibanna Zebra is an extension of Tibanna Unicorn used specifically for CGAP. Zebra has two additional steps that communicate with the CGAP Data Portal and handle CGAP metadata. Zebra requires access keys to the CGAP Data Portal and the CGAP AWS account.


Contents:

.. toctree::
   :hidden:

   self


.. toctree::
   :maxdepth: 4

   news
   code
   installation
   cli
   behavior
   execution_json
   tests
