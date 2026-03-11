forge
=====

forge — a click-clop project

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   installation
   usage
   api

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
   forge hello greet --name World

Shell Completion
~~~~~~~~~~~~~~~~

Generate and install shell completions:

.. code-block:: bash

   # Bash (add to ~/.bashrc)
   eval "$(forge completion bash)"

   # Zsh (add to ~/.zshrc)
   eval "$(forge completion zsh)"

   # Fish
   forge completion fish | source

Server (REST + MCP)
-------------------

.. code-block:: bash

   make serve
   # Swagger UI at http://localhost:8000/docs

API Reference
=============

.. automodule:: forge.services.hello
   :members:
   :undoc-members:

.. click:: forge.cli:main
   :prog: forge
   :nested: full
