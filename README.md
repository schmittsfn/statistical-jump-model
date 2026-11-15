# Statistical jump model

Standalone Python research implementation with independent numerical fixtures
and explicit replication questions for the paper authors.

**Replication work in progress.** Not author-endorsed, not a reproduction of
the original empirical results, and not a validated trading or forecasting system.
Unspecified settings remain declared conventions.

## Run locally

Python 3.12 and [uv](https://docs.astral.sh/uv/) are used for the checked setup.

```sh
git clone https://github.com/schmittsfn/statistical-jump-model.git
cd statistical-jump-model
uv sync --locked
uv run --no-sync python -m unittest discover -s tests -v
uv run --no-sync python examples/synthetic.py
```

The example fits one 3,000-observation calibration. The full monthly-selected policy is available as `jump_policy`; it requires much longer history.
Inputs are generated locally; no download or credential is needed.

## Source and implementation

Implementation: [`src/statistical_jump_model/__init__.py`](src/statistical_jump_model/__init__.py). Tests:
[`test_jump.py`](tests/test_jump.py).

Source: Shu, Yu and Mulvey, *Downside Risk Reduction Using Regime-Switching
Signals*, [arXiv:2402.05272v3](https://arxiv.org/abs/2402.05272v3), sections
3.4.1–3.4.3. The [`jumpmodels`](https://github.com/Yizhan-Oliver-Shu/jump-models)
author library performs fitting and supplies the reference dynamic program.

`jump_policy(asset_returns, cash_returns)` uses aligned daily simple returns,
not prices or annual yields. The caller must supply complete, correctly dated
sessions and cash returns. Missing cash is not replaced with zero.

The implementation uses excess-return DD10/Sortino20/Sortino60 features,
3,000-observation training and rolling inference, semiannual calibration,
monthly penalty selection over eight calendar years of online strategy returns,
and 10bp per exposure change. Signal t affects return t+2. It requires a long
history before producing its first selected strategy state.

Declared choices: normalized EWM weights; square-root downside deviation
following author code rather than the printed expression; population feature
standardization; January/July calibration anchors; penalty grid
[0, 1, 3, 10, 30, 100, 300, 1000]; seed 137. Calendar month-end detection uses
XNYS. Other exchanges are not supported by that calendar convention.

State labels follow author cumulative-return sorting, including unreachable
empty states. Original Bloomberg/GFD datasets and experiment configuration are
not included. The author library is a dependency, not vendored or relicensed.

## Replication and contributions

See [open questions](docs/REPLICATION_QUESTIONS.md),
[verification scope](docs/VERIFICATION.md) and [provenance](NOTICE.md).
For a correction, provide the paper version, equation/page, and a minimal
reference input/output or failing test. See [CONTRIBUTING.md](CONTRIBUTING.md).

This repository contains only this model. It does not require the other risk
model repositories or the earlier combined package. No private data, portfolio
records, market captures or paper PDFs are distributed. Callers supply their
own appropriately licensed data. Original-paper empirical results have not
been reproduced here.

Code, tests and documentation were prepared with OpenAI Codex assistance.
MIT license covers this project's files; dependencies and papers retain their
respective licenses and rights. No independent academic audit is claimed.
