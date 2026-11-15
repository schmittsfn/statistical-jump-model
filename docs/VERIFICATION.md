# Verification scope

The model and its reference fixtures are extracted from the checked combined
package at `b8afcda`, with only package/helper import relocation. Standalone
installation, reference tests and the synthetic example are checked before
publication using CPython 3.12.4 on macOS ARM64 and uv 0.12.10.

These checks do not resolve omitted author conventions or reproduce the paper's
empirical results. Other operating systems and Python 3.13 have not been tested.
Hosted CI is not configured. No live market data or multi-hour historical study
is included in this standalone verification.

Recorded 15 November 2026: isolated install succeeded; 7 tests passed
with zero skips or failures (42.873 seconds), and the synthetic example
exited 0. Model AST parity after import relocation and internal documentation
links were checked.
