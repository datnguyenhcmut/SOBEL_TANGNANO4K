# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'Tang Nano 4K Sobel Edge Detection'
copyright = '2025, Nguyễn Văn Đạt'
author = 'Nguyễn Văn Đạt'

version = '1.0'
release = '1.0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
    'sphinx.ext.todo',
    'sphinx.ext.mathjax',
    'sphinxcontrib_hdl_diagrams',    # Verilog diagrams support
    # 'sphinxcontrib.wavedrom',      # Waveform diagrams (requires libxcb)
]

templates_path = ['_templates']
exclude_patterns = []

language = 'en'

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'alabaster'
html_static_path = ['_static']

# -- Verilog Diagrams Configuration ------------------------------------------
# Path to Verilog source files
verilog_source_path = os.path.abspath('../../verilog')
sys.path.insert(0, verilog_source_path)

# Use yowasp-yosys (WebAssembly version)
hdl_diagrams_yosys = 'yowasp-yosys'
