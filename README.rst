=================================================
 ``devenv-secrets``: A tool to keep local secrets
=================================================

Overview
--------

``devenv-secrets`` is a devenv plugin that lets you keep a number of
"profiles", each of which can have different secrets.  The secrets are
serialized into JSON and then stored in your local computer's keychain or
wallet (using the Python ``keyring`` module).  When ``devenv shell`` is run,
the secrets are placed into environment variables for the duration of the
shell.

It will work on most Linux systems that have a desktop environment and on
MacOS.  It will not work on headless systems, so cannot be used in CI
deployments.

Setting It Up
-------------

To enable ``devenv-secrets`` within a devenv project, you must add its URL to
``devenv.yaml``.  For example, a ``devenv.yaml`` might look like:

.. code-block:: yaml

   inputs:
     nixpkgs:
       url: github:NixOS/nixpkgs/nixpkgs-unstable
     devenv-secrets:
       url: github:mcdonc/devenv-secrets

Then you have to include its plugin and enable it within ``devenv.nix``.  For
example:

.. code-block:: nix

   { pkgs, lib, config, inputs, ... }:

   {
     imports = [ inputs.devenv-secrets.plugin ];

     secrets.enable = true;
     secrets.profile = "dev";

   }

Once it is enabled, each time ``devenv shell`` starts, it will attempt to add
environment variables to the shell environment that are the decrypted secrets.

The first time you start it, it will inject default values into the shell's
environment.  It won't be useful until you configure it.  While in the devenv
shell, you can configure it for your use via the ``secrets`` script:

.. code-block::

   secrets edit

This will pull up your ``EDITOR`` and place the current secrets profile JSON
into its buffer.  Change the values to suit you.  Once you've saved the buffer,
it will write the values into your computer's keychain.

You can then either restart the shell or follow the prompts to activate the
changes.

The default profile is named ``dev``.  You can create a new environment
named ``another`` via:

.. code-block::

   secrets copy dev another

Then exit the devenv shell and change ``secrets.profile = "dev";`` to
``secrets.profile = "another";`` in order to select the new secrets profile.  

Note that secrets profiles are not local to a specific devenv environmnent or
directory or anything, they are shared by all devenv environments that you use
on the system.  Each of your projects that needs unique secrets should have its
own profile name.

``secrets`` also has some other features explained in its help::

  usage: secrets [-h] {edit,list,delete,copy,export} ...

  secrets

  positional arguments:
    {edit,list,delete,copy,export}
                          No arguments means show current profile
      edit                Edit the current secrets profile
      list                Show all available profiles
      delete              Delete a profile
      copy                Copy a profile
      export              Output shell commands to export the required envvars

  options:
    -h, --help            show this help message and exit

