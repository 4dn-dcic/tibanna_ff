=========================
Tibanna Pony for 4DN-DCIC
=========================

Tibanna Pony is an extension of Tibanna Unicorn used specifically for 4DN-DCIC (4D Nucleome Data Coordination and Integration Center). Pony has two additional steps that communicate with the 4DN Data Portal and handle 4DN metadata. Pony is only for 4DN-DCIC and requires access keys to the Data Portal and the 4DN DCIC AWS account.


=================  ==================
 Tibanna Unicorn    Tibanna Pony
=================  ==================
|tibanna_unicorn|  |tibanna_pony|
=================  ==================

.. |tibanna_unicorn| image:: images/screenshot_tibanna_unicorn.png
.. |tibanna_pony| image:: images/screenshot_tibanna_pony.png


Example Tibanna setup for 4DN-DCIC
----------------------------------

To deploy pony, you could do the following.

::

    tibanna_4dn deploy_pony
