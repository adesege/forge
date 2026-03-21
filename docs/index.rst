forge
=====

A Forgejo CLI and MCP tool built with click-clop.

Installation
============

.. code-block:: bash

   uv sync
   make install

Usage
=====

CLI
---

.. code-block:: bash

   forge --help

MCP Server
----------

The MCP server exposes all service functions as tools for AI assistants.

API Reference
=============

.. automodule:: forge.services
   :members:
   :undoc-members:

.. click:: forge.cli:main
   :prog: forge
   :nested: full
