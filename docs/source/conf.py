#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Trio documentation build configuration file, created by
# sphinx-quickstart on Sat Jan 21 19:11:14 2017.
#
# This file is execfile()d with the current directory set to its
# containing dir.
#
# Note that not all possible configuration values are present in this
# autogenerated file.
#
# All configuration values have a default; values that are commented out
# serve to show the default.

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys
sys.path.insert(0, os.path.abspath('.'))

# XX hack the RTD theme until
#   https://github.com/rtfd/sphinx_rtd_theme/pull/382
# is shipped (should be in the release after 0.2.4)
def setup(app):
    app.add_stylesheet("hackrtd.css")

# XX monkeypatch until
#   https://github.com/sphinx-doc/sphinx/pull/3449
# is resolved (hopefully before the next release...)
import sphinx
# Currently sphinx issue #3449 has the 1.6 milestone set, so maybe that's
# the plan?
if sphinx.version_info < (1, 6, 0):
    print("Monkeypatching sphinx!")
    print("I hope they release a fixed version soon...")
    import inspect
    import sphinx.util.inspect
    # Copied from the definition of inspect.getfullargspec from Python master,
    # and modified to remove the use of special flags that break decorated
    # callables and bound methods in the name of backwards compatibility. Used
    # under the terms of PSF license v2, which requires the above statement
    # and the following:
    #
    #   Copyright (c) 2001, 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009,
    #   2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017 Python Software
    #   Foundation; All Rights Reserved
    def getargspec(func):
        """Like inspect.getfullargspec but supports bound methods, and wrapped
        methods."""
        sig = inspect.signature(func)

        args = []
        varargs = None
        varkw = None
        kwonlyargs = []
        defaults = ()
        annotations = {}
        defaults = ()
        kwdefaults = {}

        if sig.return_annotation is not sig.empty:
            annotations['return'] = sig.return_annotation

        for param in sig.parameters.values():
            kind = param.kind
            name = param.name

            if kind is inspect.Parameter.POSITIONAL_ONLY:
                args.append(name)
            elif kind is inspect.Parameter.POSITIONAL_OR_KEYWORD:
                args.append(name)
                if param.default is not param.empty:
                    defaults += (param.default,)
            elif kind is inspect.Parameter.VAR_POSITIONAL:
                varargs = name
            elif kind is inspect.Parameter.KEYWORD_ONLY:
                kwonlyargs.append(name)
                if param.default is not param.empty:
                    kwdefaults[name] = param.default
            elif kind is inspect.Parameter.VAR_KEYWORD:
                varkw = name

            if param.annotation is not param.empty:
                annotations[name] = param.annotation

        if not kwdefaults:
            # compatibility with 'func.__kwdefaults__'
            kwdefaults = None

        if not defaults:
            # compatibility with 'func.__defaults__'
            defaults = None

        return inspect.FullArgSpec(args, varargs, varkw, defaults,
                                   kwonlyargs, kwdefaults, annotations)
    sphinx.util.inspect.getargspec = getargspec

# -- General configuration ------------------------------------------------

# If your documentation needs a minimal Sphinx version, state it here.
#
# needs_sphinx = '1.0'

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.intersphinx',
    'sphinx.ext.coverage',
    'sphinx.ext.napoleon',
    'sphinxcontrib_trio',
]

intersphinx_mapping = {
    "python": ('https://docs.python.org/3', None),
}

autodoc_member_order = "bysource"

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# The suffix(es) of source filenames.
# You can specify multiple suffix as a list of string:
#
# source_suffix = ['.rst', '.md']
source_suffix = '.rst'

# The master toctree document.
master_doc = 'index'

# General information about the project.
project = 'Trio'
copyright = '2017, Nathaniel J. Smith'
author = 'Nathaniel J. Smith'

# The version info for the project you're documenting, acts as replacement for
# |version| and |release|, also used in various other places throughout the
# built documents.
#
# The short X.Y version.
import trio
version = trio.__version__
# The full version, including alpha/beta/rc tags.
release = version

# It would be nicer to make this a .png; literally every browser that
# supports favicons at all now supports png:
#     https://caniuse.com/#feat=link-icon-png
# But sphinx won't let me:
#     https://github.com/sphinx-doc/sphinx/pull/3715
# Oh well. 'convert favicon-32.png favicon-32.ico' it is. And it's only 2x
# bigger...
html_favicon = "_static/favicon-32.ico"
html_logo = "../../logo/wordmark-transparent.svg"
# & down below in html_theme_options we set logo_only=True

# The language for content autogenerated by Sphinx. Refer to documentation
# for a list of supported languages.
#
# This is also used if you do content translation via gettext catalogs.
# Usually you set "language" from the command line for these cases.
language = None

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This patterns also effect to html_static_path and html_extra_path
exclude_patterns = []

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = 'sphinx'

highlight_language = 'python3'

# If true, `todo` and `todoList` produce output, else they produce nothing.
todo_include_todos = False


# -- Options for HTML output ----------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
#html_theme = 'alabaster'

# We have to set this ourselves, not only because it's useful for local
# testing, but also because if we don't then RTD will throw away our
# html_theme_options.
import sphinx_rtd_theme
html_theme = 'sphinx_rtd_theme'
html_theme_path = [sphinx_rtd_theme.get_html_theme_path()]

# Theme options are theme-specific and customize the look and feel of a theme
# further.  For a list of options available for each theme, see the
# documentation.
#
html_theme_options = {
    # default is 2
    # show deeper nesting in the RTD theme's sidebar TOC
    # https://stackoverflow.com/questions/27669376/
    # I'm not 100% sure this actually does anything with our current
    # versions/settings...
    "navigation_depth": 4,
    "logo_only": True,
}

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']


# -- Options for HTMLHelp output ------------------------------------------

# Output file base name for HTML help builder.
htmlhelp_basename = 'Triodoc'


# -- Options for LaTeX output ---------------------------------------------

latex_elements = {
    # The paper size ('letterpaper' or 'a4paper').
    #
    # 'papersize': 'letterpaper',

    # The font size ('10pt', '11pt' or '12pt').
    #
    # 'pointsize': '10pt',

    # Additional stuff for the LaTeX preamble.
    #
    # 'preamble': '',

    # Latex figure (float) alignment
    #
    # 'figure_align': 'htbp',
}

# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title,
#  author, documentclass [howto, manual, or own class]).
latex_documents = [
    (master_doc, 'Trio.tex', 'Trio Documentation',
     'Nathaniel J. Smith', 'manual'),
]


# -- Options for manual page output ---------------------------------------

# One entry per manual page. List of tuples
# (source start file, name, description, authors, manual section).
man_pages = [
    (master_doc, 'trio', 'Trio Documentation',
     [author], 1)
]


# -- Options for Texinfo output -------------------------------------------

# Grouping the document tree into Texinfo files. List of tuples
# (source start file, target name, title, author,
#  dir menu entry, description, category)
texinfo_documents = [
    (master_doc, 'Trio', 'Trio Documentation',
     author, 'Trio', 'One line description of project.',
     'Miscellaneous'),
]
