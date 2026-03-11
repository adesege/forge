# forge — Sphinx configuration

project = "forge"
author = "Brian Payne"
release = "0.1.0"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx_click",
    "sphinx_rtd_theme",
]

templates_path = ["_templates"]
exclude_patterns = ["_build"]

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]

# Auto-doc settings
autodoc_member_order = "bysource"
autodoc_typehints = "description"
