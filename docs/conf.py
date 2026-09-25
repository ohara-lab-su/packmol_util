"""
packmol_util documentation
"""

import os
import sys

sys.path.insert(0, os.path.abspath("../src"))

project = "packmol_util"
language = "ja"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "myst_parser",
]

source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}

myst_enable_extensions = [
    "deflist",
    "attrs_block",
    "substitution",
    "colon_fence",
    "linkify",
]
myst_linkify_fuzzy_links = True
myst_heading_anchors = 3

autosummary_generate = True

autodoc_default_options = {
    "members": True,
    "undoc-members": True,
    "show-inheritance": True,
    "private-members": True,
}

add_module_names = False
autodoc_typehints = "description"
autodoc_preserve_defaults = True
set_type_checking_flag = True

autodoc_mock_imports = [
    "x_logger",
]

html_theme = "sphinx_rtd_theme"
html_theme_options = {
    "collapse_navigation": False,
    "navigation_depth": 4,
    "titles_only": False,
}

exclude_patterns = [
    "_build",
    "api",
]

html_static_path = []
