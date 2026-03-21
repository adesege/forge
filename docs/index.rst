forge
=====

A click-clop CLI application

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

Configuration
=============

forge loads configuration from TOML files with environment variable overrides.
Files are loaded in order, with later values winning via deep-merge:

1. ``.env`` — loaded into the environment (does not overwrite existing env vars)
2. ``config.toml`` — base/default configuration (committed)
3. ``config.dev.toml`` — development overrides (committed)
4. ``config.local.toml`` — local/personal overrides (gitignored)
5. ``~/.config/forge/config.toml`` — user-wide defaults (XDG config)
6. ``~/.config/forge/config.local.toml`` — user-wide local overrides (XDG config)
7. Explicit ``--config`` path — if passed via the CLI
8. Environment variables — ``FORGE_<SECTION>__<KEY>=value`` (highest priority)

Config Sections
---------------

.. code-block:: toml

   [server]
   host = "0.0.0.0"
   port = 8000

   [logging]
   level = "INFO"          # DEBUG, INFO, WARNING, ERROR, CRITICAL
   json_output = true

   [telemetry]
   enabled = true
   otlp_endpoint = "http://localhost:4317"

   [onepassword]
   vault = ""

   [forgejo]
   url = "https://git.example.com"
   token = "your-token-here"
   # OR use a command for dynamic retrieval:
   # token_cmd = 'op read "op://Dev/Forgejo/token"'
   default_owner = "my-org"

Environment Variable Overrides
------------------------------

Environment variables use the prefix ``FORGE_`` with double underscores (``__``)
as section separators. For example:

- ``FORGE_SERVER__PORT=9000`` sets ``[server] port``
- ``FORGE_LOGGING__LEVEL=DEBUG`` sets ``[logging] level``
- ``FORGE_FORGEJO__URL=https://git.example.com`` sets ``[forgejo] url``
- ``FORGE_FORGEJO__TOKEN=secret`` sets ``[forgejo] token``

Recommended Setup
-----------------

- Put shared defaults in ``config.toml`` (committed)
- Put development overrides in ``config.dev.toml`` (committed)
- Put secrets and personal settings in ``config.local.toml`` (gitignored)
- For settings shared across multiple projects, use ``~/.config/forge/config.toml``

API Reference
=============

.. automodule:: forge.services
   :members:
   :undoc-members:

.. click:: forge.cli:main
   :prog: forge
   :nested: full
