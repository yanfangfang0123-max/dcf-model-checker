#!/usr/bin/env python3
"""
dcf_check.py - independently rebuild a DCF and reconcile it, line by line,
against the figures reported in someone else's model (e.g. exported from Excel).

For every line that does not reconcile, the checker tests a short list of
common modelling mistakes and reports which one reproduces the reported
number, so the reviewer gets a likely root cause rather than just "mismatch".

Standard library only. Usage:
    python dcf_check.py data/model_inputs.json data/colleague_model_outputs.json
    python dcf_check.py data/model_inputs.json data/colleague_model_outputs.json --report review.md
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, field

REL_TOL = 0.005   # 0.5% relative tolerance
ABS_TOL = 0.05    # or 0.05 in model units (GBP m)


# ---------------------------------------------------------------- the rebuild
@dataclass
class DCF:
    years: list
    revenue: list
    ebit: list
    nopat: list
    da: list
    capex: list
    delta_nwc: list
    fcff: list
    cost_of_equity: float
    after_tax_cost_of_debt: float
    wacc: float
    discount_factors: list
    pv_fcff: list
    terminal_value: float
    pv_terminal_value: float
    enterprise_value: float
    equity_value: float
    value_per_share: float
    ebitda_final: float = 0.0
    notes: list = field(default_factory=list)


def wacc_from(w: dict, tax: float) -> tuple[float, float, float]:
    ke = w["risk_free_rate"] + w["equity_beta"] * w["equity_risk_premium"]
    kd_after = w["pre_tax_cost_of_debt"] * (1 - tax)
    e, d = w["market_value_equity"], w["market_value_debt"]
    wacc = ke * e / (e + d) + kd_after * d / (e + d)
    return ke, kd_after, wacc


def fcff_lines(m: dict, nwc_sign: int = -1) -> dict:
    """Step 1: free cash flow to the firm. nwc_sign=-1 is correct (increase in NWC uses cash)."""
    t = m["tax_rate"]
    rev = m["revenue"]
    ebit = [r * mg for r, mg in zip(rev, m["ebit_margin"])]
    nopat = [e * (1 - t) for e in ebit]
    da = [r * m["da_pct_revenue"] for r in rev]
    capex = [r * m["capex_pct_revenue"] for r in rev]
    nwc = [m["base_year_revenue"] * m["nwc_pct_revenue"]] + [r * m["nwc_pct_revenue"] for r in rev]
    dnwc = [nwc[i + 1] - nwc[i] for i in range(len(rev))]
    fcff = [n + d - c + nwc_sign * x for n, d, c, x in zip(nopat, da, capex, dnwc)]
    return dict(revenue=rev, ebit=ebit, nopat=nopat, da=da, capex=capex, delta_nwc=dnwc, fcff=fcff)


def discount_factors(rate: float, n: int, mid_year: bool, shift: int = 0) -> list:
    return [1 / (1 + rate) ** (t - (0.5 if mid_year else 0) + shift) for t in range(1, n + 1)]


def rebuild(m: dict) -> DCF:
    f = fcff_lines(m)
    ke, kd_after, wacc = wacc_from(m["wacc_inputs"], m["tax_rate"])
    n = len(f["fcff"])
    dfs = discount_factors(wacc, n, m["mid_year_convention"])
    pv = [c * d for c, d in zip(f["fcff"], dfs)]
    g = m["terminal_growth"]
    tv = f["fcff"][-1] * (1 + g) / (wacc - g)
    # TV sits at the END of the final forecast year, so it takes the year-N end-of-period factor
    pv_tv = tv / (1 + wacc) ** n
    ev = sum(pv) + pv_tv
    eq = ev - m["net_debt"]
    return DCF(
        years=m["forecast_years"], revenue=f["revenue"], ebit=f["ebit"], nopat=f["nopat"],
        da=f["da"], capex=f["capex"], delta_nwc=f["delta_nwc"], fcff=f["fcff"],
        cost_of_equity=ke, after_tax_cost_of_debt=kd_after, wacc=wacc,
        discount_factors=dfs, pv_fcff=pv, terminal_value=tv, pv_terminal_value=pv_tv,
        enterprise_value=ev, equity_value=eq, value_per_share=eq / m["diluted_shares_m"],
        ebitda_final=f["ebit"][-1] + f["da"][-1],
    )


# ------------------------------------------------- common-mistake hypotheses
def explain_fcff(m: dict, reported: list) -> str | None:
    flipped = fcff_lines(m, nwc_sign=+1)["fcff"]
    if all(close(a, b) for a, b in zip(flipped, reported)):
        return "Change in working capital ADDED instead of subtracted (sign error on the NWC line)."
    f = fcff_lines(m)
    no_da = [x - d for x, d in zip(f["fcff"], f["da"])]
    if all(close(a, b) for a, b in zip(no_da, reported)):
        return "D&A not added back to NOPAT."
    pre_tax = [x + e * m["tax_rate"] for x, e in zip(f["fcff"], f["ebit"])]
    if all(close(a, b) for a, b in zip(pre_tax, reported)):
        return "Tax not deducted from EBIT (pre-tax cash flow discounted at an after-tax WACC)."
    return None


def explain_wacc(m: dict, reported: float) -> str | None:
    w, t = dict(m["wacc_inputs"]), m["tax_rate"]
    ke = w["risk_free_rate"] + w["equity_beta"] * w["equity_risk_premium"]
    e, d = w["market_value_equity"], w["market_value_debt"]
    pre_tax = ke * e / (e + d) + w["pre_tax_cost_of_debt"] * d / (e + d)
    if close(pre_tax, reported, rel=1e-4, ab=1e-5):
        return "Cost of debt used PRE-tax; the debt tax shield is missing from WACC."
    if close(ke, reported, rel=1e-4, ab=1e-5):
        return "Cost of equity used as WACC (debt weight ignored)."
    return None


def explain_pv_tv(m: dict, tv: float, wacc: float, reported: float) -> str | None:
    n = len(m["revenue"])
    if close(tv / (1 + wacc) ** (n + 1), reported):
        return f"Terminal value discounted {n + 1} periods instead of {n} (one period too many)."
    if close(tv, reported):
        return "Terminal value not discounted at all."
    if close(tv / (1 + wacc) ** (n - 0.5), reported):
        return "Mid-year factor applied to the terminal value (TV is an end-of-year amount)."
    return None


# ------------------------------------------------------------------ helpers
def close(a: float, b: float, rel: float = REL_TOL, ab: float = ABS_TOL) -> bool:
    return abs(a - b) <= max(ab, rel * max(abs(a), abs(b)))


def fmt(x: float, pct: bool = False) -> str:
    return f"{x:.2%}" if pct else f"{x:,.2f}"


# ------------------------------------------------------------------- review
def review(m: dict, rep: dict) -> list[str]:
    d = rebuild(m)
    out: list[str] = []
    issues: list[str] = []

    out.append(f"# DCF review: {m['company']}")
    out.append(f"Units: {m['currency']}. Tolerance: {REL_TOL:.1%} relative or {ABS_TOL} absolute.\n")

    # Step 1 - FCFF
    out.append("## Step 1 - Free cash flow to firm")
    out.append("| Year | Rebuilt FCFF | Reported | Status |")
    out.append("|---|---:|---:|---|")
    ok = True
    for y, a, b in zip(d.years, d.fcff, rep["fcff"]):
        s = "OK" if close(a, b) else "MISMATCH"
        ok &= s == "OK"
        out.append(f"| {y} | {fmt(a)} | {fmt(b)} | {s} |")
    if not ok:
        why = explain_fcff(m, rep["fcff"]) or "No standard hypothesis reproduces it; trace line by line."
        issues.append(f"FCFF: {why}")
        out.append(f"\n**Likely cause:** {why}")
    out.append("")

    # Step 2 - WACC
    out.append("## Step 2 - Discount rate")
    out.append(f"- Cost of equity (CAPM): {fmt(d.cost_of_equity, True)}")
    out.append(f"- After-tax cost of debt: {fmt(d.after_tax_cost_of_debt, True)}")
    s = "OK" if close(d.wacc, rep["wacc"], rel=1e-4, ab=1e-5) else "MISMATCH"
    out.append(f"- WACC rebuilt {fmt(d.wacc, True)} vs reported {fmt(rep['wacc'], True)}: **{s}**")
    if s != "OK":
        why = explain_wacc(m, rep["wacc"]) or "No standard hypothesis reproduces it."
        issues.append(f"WACC: {why}")
        out.append(f"\n**Likely cause:** {why}")
    out.append("")

    # Step 3 - terminal value. Test the reported TV/PV against the reported WACC first,
    # so an upstream WACC error is not double-counted as a TV error.
    out.append("## Step 3 - Terminal value")
    g = m["terminal_growth"]
    tv_on_their_inputs = rep["fcff"][-1] * (1 + g) / (rep["wacc"] - g)
    s_tv = "OK" if close(tv_on_their_inputs, rep["terminal_value"]) else "MISMATCH"
    out.append(f"- Gordon growth TV using THEIR final FCFF and WACC: {fmt(tv_on_their_inputs)} vs reported "
               f"{fmt(rep['terminal_value'])}: **{s_tv}** (formula applied correctly, inherits upstream errors)")
    s_pv = "OK" if close(rep["terminal_value"] / (1 + rep["wacc"]) ** len(d.years), rep["pv_terminal_value"]) else "MISMATCH"
    out.append(f"- PV of TV, discounting check: **{s_pv}**")
    if s_pv != "OK":
        why = explain_pv_tv(m, rep["terminal_value"], rep["wacc"], rep["pv_terminal_value"]) or "Unexplained."
        issues.append(f"PV of terminal value: {why}")
        out.append(f"\n**Likely cause:** {why}")
    out.append(f"- Rebuilt TV {fmt(d.terminal_value)}, PV {fmt(d.pv_terminal_value)}\n")

    # Step 4 - bridge to equity
    out.append("## Step 4 - Enterprise value to value per share")
    out.append("| Line | Rebuilt | Reported | Difference |")
    out.append("|---|---:|---:|---:|")
    for label, a, b in [
        ("Sum of PV(FCFF)", sum(d.pv_fcff), rep["sum_pv_fcff"]),
        ("PV(terminal value)", d.pv_terminal_value, rep["pv_terminal_value"]),
        ("Enterprise value", d.enterprise_value, rep["enterprise_value"]),
        ("Equity value", d.equity_value, rep["equity_value"]),
        ("Value per share (GBP)", d.value_per_share, rep["value_per_share"]),
    ]:
        out.append(f"| {label} | {fmt(a)} | {fmt(b)} | {fmt(b - a)} ({(b - a) / a:+.1%}) |")
    out.append("")

    # Step 5 - sanity checks on the corrected model
    out.append("## Step 5 - Sanity checks on the rebuilt model")
    tv_share = d.pv_terminal_value / d.enterprise_value
    implied_multiple = d.terminal_value / d.ebitda_final
    checks = [
        (g < d.wacc, f"Terminal growth {fmt(g, True)} below WACC {fmt(d.wacc, True)}"),
        (g <= 0.03, "Terminal growth at or below a long-run nominal GDP proxy (3%)"),
        (tv_share <= 0.75, f"Terminal value is {tv_share:.0%} of EV (flag if above 75%)"),
        (6 <= implied_multiple <= 14, f"Implied terminal EV/EBITDA {implied_multiple:.1f}x (flag outside 6-14x)"),
    ]
    for passed, text in checks:
        out.append(f"- [{'x' if passed else ' '}] {text}")
    out.append("")

    # Summary
    out.append("## Summary")
    if issues:
        out.append(f"{len(issues)} issue(s) found:")
        out += [f"{i}. {x}" for i, x in enumerate(issues, 1)]
        out.append(f"\nReported value per share GBP {fmt(rep['value_per_share'])}; corrected GBP "
                   f"{fmt(d.value_per_share)} ({(d.value_per_share - rep['value_per_share']) / rep['value_per_share']:+.1%}).")
    else:
        out.append("All lines reconcile within tolerance.")
    return out


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("inputs", help="model assumptions (JSON)")
    p.add_argument("reported", help="figures reported by the model under review (JSON)")
    p.add_argument("--report", help="also write the review to this Markdown file")
    a = p.parse_args()
    with open(a.inputs) as f:
        m = json.load(f)
    with open(a.reported) as f:
        rep = json.load(f)
    lines = review(m, rep)
    text = "\n".join(lines)
    print(text)
    if a.report:
        with open(a.report, "w") as f:
            f.write(text + "\n")


if __name__ == "__main__":
    main()
