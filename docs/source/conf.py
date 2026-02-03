# MUIO documentation build configuration file

import sys
from pathlib import Path

# Optional: insert MUIO source path to sys.path if autodoc is used
# sys.path.insert(0, str(Path("../..")))

# -- Project information -----------------------------------------------------
project = 'MUIO: Modelling User Interface for OSeMOSYS'
author = 'MUIO Contributors'
copyright = '2024-2025, MUIO Project'

# -- General configuration ---------------------------------------------------
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.mathjax',
    'sphinx.ext.todo',
    'sphinx.ext.viewcode',
    'sphinx_book_theme',
]

autosummary_generate = True
todo_include_todos = True
source_suffix = '.rst'
master_doc = 'index'
language = 'en'
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# -- HTML output -------------------------------------------------------------

html_theme = "sphinx_book_theme"

html_theme_options = {
    "repository_url": "https://github.com/OSeMOSYS/MUIO",
    "use_repository_button": True,
    "use_edit_page_button": True,
    "path_to_docs": "docs/source",
    "home_page_in_toc": True,
    "show_navbar_depth": 2,
}

html_title = 'MUIO Documentation'
html_short_title = 'MUIO'
html_logo = '_static/muio-logo.png'  # Ensure this file exists
html_favicon = '_static/favicon.ico'  # Optional
html_static_path = ['_static']

# -- Options for LaTeX output ------------------------------------------------
latex_documents = [
    (master_doc, 'MUIO.tex', 'MUIO Documentation', 'MUIO Contributors', 'manual'),
]

# -- Options for manual page output ------------------------------------------
man_pages = [
    (master_doc, 'muio', 'MUIO Documentation', [author], 1)
]

# -- Options for Texinfo output ----------------------------------------------
texinfo_documents = [
    (master_doc, 'MUIO', 'MUIO Documentation', author, 'MUIO',
     'An interface to build OSeMOSYS energy models.', 'Miscellaneous'),
]

