# DCF review: Northwind Components Ltd (fictional)
Units: GBP m. Tolerance: 0.5% relative or 0.05 absolute.

## Step 1 - Free cash flow to firm
| Year | Rebuilt FCFF | Reported | Status |
|---|---:|---:|---|
| 2027 | 10.32 | 12.48 | MISMATCH |
| 2028 | 11.65 | 13.95 | MISMATCH |
| 2029 | 13.12 | 15.31 | MISMATCH |
| 2030 | 14.07 | 16.06 | MISMATCH |
| 2031 | 14.94 | 16.71 | MISMATCH |

**Likely cause:** Change in working capital ADDED instead of subtracted (sign error on the NWC line).

## Step 2 - Discount rate
- Cost of equity (CAPM): 10.25%
- After-tax cost of debt: 4.88%
- WACC rebuilt 9.06% vs reported 9.42%: **MISMATCH**

**Likely cause:** Cost of debt used PRE-tax; the debt tax shield is missing from WACC.

## Step 3 - Terminal value
- Gordon growth TV using THEIR final FCFF and WACC: 229.80 vs reported 229.86: **OK** (formula applied correctly, inherits upstream errors)
- PV of TV, discounting check: **MISMATCH**

**Likely cause:** Terminal value discounted 6 periods instead of 5 (one period too many).
- Rebuilt TV 215.95, PV 140.00

## Step 4 - Enterprise value to value per share
| Line | Rebuilt | Reported | Difference |
|---|---:|---:|---:|
| Sum of PV(FCFF) | 49.01 | 56.61 | 7.60 (+15.5%) |
| PV(terminal value) | 140.00 | 133.96 | -6.04 (-4.3%) |
| Enterprise value | 189.00 | 190.57 | 1.57 (+0.8%) |
| Equity value | 141.00 | 142.57 | 1.57 (+1.1%) |
| Value per share (GBP) | 5.64 | 5.70 | 0.06 (+1.1%) |

## Step 5 - Sanity checks on the rebuilt model
- [x] Terminal growth 2.00% below WACC 9.06%
- [x] Terminal growth at or below a long-run nominal GDP proxy (3%)
- [x] Terminal value is 74% of EV (flag if above 75%)
- [x] Implied terminal EV/EBITDA 7.4x (flag outside 6-14x)

## Summary
3 issue(s) found:
1. FCFF: Change in working capital ADDED instead of subtracted (sign error on the NWC line).
2. WACC: Cost of debt used PRE-tax; the debt tax shield is missing from WACC.
3. PV of terminal value: Terminal value discounted 6 periods instead of 5 (one period too many).

Reported value per share GBP 5.70; corrected GBP 5.64 (-1.0%).
