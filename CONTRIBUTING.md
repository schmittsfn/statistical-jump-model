# Contributing

Please open a focused issue or pull request with:

- The model, paper version and equation/page being discussed.
- A minimal synthetic or redistributable input and expected result.
- The current behavior and the proposed correction or interpretation.

Run `uv sync --locked` and `uv run --no-sync python -m unittest discover -s tests -v`.
Keep model changes accompanied by independently justified tests. Preserve
unresolved settings as explicit conventions until source evidence resolves them.
Do not submit credentials, proprietary datasets, private portfolios or paper PDFs.
Please distinguish correctness of a calculation from predictive usefulness.
