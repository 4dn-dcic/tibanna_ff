===========
Permissions
===========

Permissions for Tibanna Pony/Zebra users are set up in a way similar to the way it is set up for Unicorn, but there are differences.


With usergroup
++++++++++++++

One can set up usergroups while deploying a pony/zebra like the way a usergroup is set up while deploying a unicorn (using ``-g`` option). They work the same way.

::

    tibanna_4dn deploy_pony -g <usergroupname>


::    
    
    tibanna_cgap deploy_zebra -g <usergroupname>
    
    
Without usergroup
+++++++++++++++++

If a pony/zebra is deployed without usergroup, it gives the pony/zebra access to all the buckets. You have to be an admin in order to use this kind of pony/zebra. It applies to cases where you deploy a pony/zebra without any other options, or with a suffix.

::

    tibanna_4dn deploy_pony

::

    tibanna_4dn deploy_pony -s dev
    
::

    tibanna_cgap deploy_zebra

::

    tibanna_cgap deploy_zebra -s dev
    
    
