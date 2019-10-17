========
Overview
========


Tibanna_ff is an extension of Tibanna that integrates with 4DN/CGAP data portals. Tibanna is a software tool that helps you run genomic pipelines on the the Amazon (AWS) cloud. Tibanna_ff does the same but in integration with 4DN/CGAP data portal.

This documentation is written mostly for developers who want to understand the structure of the code arragements and details of the features and behaviors that are intended for Tibanna Unicorn, Pony and Zebra (the latter two specifically designed for 4DNucleome and CGAP (Clinical Genome Analysis Platform) data portals).

Tibanna Pony is an extension of Tibanna Unicorn used specifically for 4DN-DCIC (4D Nucleome Data Coordination and Integration Center). Pony has two additional steps that communicate with the 4DN Data Portal and handle 4DN metadata. Pony is only for 4DN-DCIC and requires access keys to the Data Portal and the 4DN DCIC AWS account.

Tibanna Zebra is an extension of Tibanna Unicorn used specifically for CGAP (Clinical Genome Analysis Platform). Zebra has two additional steps that communicate with the CGAP Data Portal and handle CGAP metadata. Zebra is only for CGAP and requires access keys to the Data Portal and the CGAP AWS account.


=================  ==============  ===============
 Tibanna Unicorn    Tibanna Pony    Tibanna Zebra
=================  ==============  ===============
|tibanna_unicorn|  |tibanna_pony|  |tibanna_zebra|
=================  ==============  ===============

.. |tibanna_unicorn| image:: images/screenshot_tibanna_unicorn.png
.. |tibanna_pony| image:: images/screenshot_tibanna_pony.png
.. |tibanna_zebra| image:: images/screenshot_tibanna_zebra.png


From Tibanna ``0.10.0`` (also ``tibanna_ff`` ``0.10.0``), Tibanna_ff is no longer part of the ``tibanna`` package, but is released as a separate package that requires ``tibanna`` as dependency.


Contents:

.. toctree::
   :hidden:

   self


.. toctree::
   :maxdepth: 4

   overview
   installation
   cli
   lambda
   behavior
   execution_json
