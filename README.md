# DCF Model Checker

A small Python tool for **peer-reviewing a discounted cash flow (DCF) model**. It rebuilds the valuation independently from the model's assumptions, reconciles every line against the figures the model reports, and, where a line does not reconcile, tests a short list of common modelling mistakes to name the most likely cause.

It mirrors how I review a DCF built by someone else: rebuild it step by step, find the first line that diverges, and work out *why* before looking at the headline value.

> All companies and numbers in this repository are fictional and were created for illustration.

## Why line-by-line, not just the answer

The sample model in `data/` contains three planted errors. Its headline value per share is **within about 1%** of the correct figure, because the errors partly offset each other:

| Error | Effect on value |
|---|---|
| Increase in working capital *added* to cash flow instead of subtracted | Overstates every year's FCFF by 12–21% |
| WACC built with the **pre-tax** cost of debt | Discount rate 9.42% instead of 9.06% |
| Terminal value discounted **6 periods instead of 5** | Understates PV of terminal value |

A reviewer who only compared the final answer with a "sense check" range would sign this model off. The line-by-line reconciliation catches all three.

## What it checks

1. **Free cash flow to firm:** NOPAT + D&A − capex − increase in net working capital, year by year
2. **Discount rate:** CAPM cost of equity, after-tax cost of debt, market-value weights
3. **Terminal value:** Gordon growth formula applied to the model's own inputs (so an upstream error is not double-counted), then the discounting period
4. **Bridge:** sum of PV(FCFF) + PV(TV) = EV, minus net debt = equity, ÷ diluted shares
5. **Sanity checks on the corrected model:** g < WACC, g ≤ long-run nominal GDP proxy, terminal value share of EV, implied exit EV/EBITDA

Mistakes it can diagnose automatically: NWC sign error, D&A not added back, untaxed EBIT, pre-tax cost of debt, cost of equity used as WACC, terminal value discounted one period too many, terminal value not discounted, and a mid-year factor wrongly applied to the terminal value.

## Run it

Python 3.9+, standard library only.

```bash
python dcf_check.py data/model_inputs.json data/colleague_model_outputs.json
python dcf_check.py data/model_inputs.json data/colleague_model_outputs.json --report review.md
python -m unittest discover -s tests -v
```

`sample_review.md` is the report produced for the sample model.

## Using it on a real model

1. Export the model's assumptions into the format of `data/model_inputs.json`.
2. Export the figures the model reports (FCFF by year, WACC, TV, PV of TV, EV, equity value, value per share) into the format of `data/colleague_model_outputs.json`.
3. Run the checker and start with the **first** line marked `MISMATCH`; later mismatches often inherit from it.

## Files

```
dcf_check.py                        rebuild, reconcile and diagnose
data/model_inputs.json              assumptions (fictional company)
data/colleague_model_outputs.json   figures reported by the model under review
sample_review.md                    output for the sample model
tests/test_dcf_check.py             unit tests, including a hand-checked WACC
CASE_STUDY.md                       write-up of a property DCF peer review
```

## Author

Fangfang Yan, finance and risk specialist (DCF valuation, credit risk, real estate finance). CFA Level I, FRM Part I. [linkedin.com/in/yanfangfang](https://www.linkedin.com/in/yanfangfang)
