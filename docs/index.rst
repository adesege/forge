forge
=====

forge — a click-clop project

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

Server (REST + MCP)
-------------------

.. code-block:: bash

   make serve
   # Swagger UI at http://localhost:8000/docs

API Reference
=============

.. automodule:: forge.services
   :members:
   :undoc-members:

.. click:: forge.cli:main
   :prog: forge
   :nested: full
