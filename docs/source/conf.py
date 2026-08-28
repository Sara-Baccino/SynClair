import os
import sys
from pathlib import Path

# Registra tutte le cartelle "src" dei sotto-pacchetti nel PYTHONPATH di Sphinx
root_path = Path(__file__).resolve().parents[2]
for src_path in root_path.glob("packages/*/src"):
    sys.path.insert(0, str(src_path))

project = 'SynClair'
copyright = '2026, Sara Baccino'
author = 'Sara Baccino'

extensions = [
    'sphinx.ext.autodoc',       # Legge automaticamente le docstring
    'sphinx.ext.napoleon',      # Supporta lo stile Google/NumPy
    'sphinx.ext.viewcode',      # Aggiunge i collegamenti al codice sorgente
    'sphinxcontrib.mermaid',   # Rendering dei diagrammi senza installare .exe
]

html_theme = 'sphinx_rtd_theme'

# Inserisci in fondo al file conf.py
autodoc_default_options = {
    'members': True,
    'undoc-members': True,        # Mostra anche funzioni senza docstring
    'show-inheritance': True,    # Mostra l'ereditarietà delle classi
    'imported-members': False,
}