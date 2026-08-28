.. SynClair documentation master file, created by
   sphinx-quickstart on Fri Aug 28 15:13:14 2026.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

SynClair documentation
======================

Add your content using ``reStructuredText`` syntax. See the
`reStructuredText <https://www.sphinx-doc.org/en/master/usage/restructuredtext/index.html>`_
documentation for details.

Documentazione SynClair
=======================

.. toctree::
   :maxdepth: 3
   :caption: Architettura e Flussi:

Diagramma di Flusso
-------------------
.. mermaid::

   graph TD
      GUI[synclair-gui] --> Core[synclair-core]
      Structure[synclair-structure] --> Core
      Reporting[synclair-reporting] --> Core

.. toctree::
   :maxdepth: 3
   :caption: API Reference Completo:

   api/core/modules
   api/structure/modules
   api/gui/modules
   api/reporting/modules