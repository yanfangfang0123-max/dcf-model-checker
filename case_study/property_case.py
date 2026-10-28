"""Reproduces every number in CASE_STUDY.md. Fictional asset and figures."""

PRICE = 13_400_000          # GBP
PURCHASE_COSTS = 0.068      # SDLT + legal + agency, % of price
GROSS_RENT_Y1 = 1_120_000
NOI_Y1 = 910_000            # after non-recoverable costs, voids and management
GROWTH = 0.025              # rent and NOI growth p.a.
HOLD = 5
EXIT_CAP = 0.0675
SALE_COSTS = 0.015
DISCOUNT = 0.08             # target unlevered return
LTV = 0.55
INTEREST = 0.055            # interest-only
COVENANT_DSCR = 2.00        # lender's minimum interest cover


def noi(year):
    return NOI_Y1 * (1 + GROWTH) ** (year - 1)


def gross_rent(year):
    return GROSS_RENT_Y1 * (1 + GROWTH) ** (year - 1)


def irr(flows, lo=-0.99, hi=1.0):
    f = lambda r: sum(c / (1 + r) ** t for t, c in enumerate(flows))
    for _ in range(200):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if f(mid) > 0 else (lo, mid)
    return mid


def npv(rate, flows):
    return sum(c / (1 + rate) ** t for t, c in enumerate(flows))


def model(include_costs=True, forward_noi=True):
    outlay = PRICE * (1 + (PURCHASE_COSTS if include_costs else 0))
    exit_noi = noi(HOLD + 1) if forward_noi else noi(HOLD)
    exit_value = exit_noi / EXIT_CAP * (1 - SALE_COSTS)
    flows = [-outlay] + [noi(y) for y in range(1, HOLD + 1)]
    flows[-1] += exit_value
    return dict(outlay=outlay, exit_noi=exit_noi, exit_value=exit_value,
                irr=irr(flows), npv=npv(DISCOUNT, flows))


if __name__ == "__main__":
    debt = PRICE * LTV
    interest = debt * INTEREST
    rows = {
        "Colleague's draft (both errors)": model(include_costs=False, forward_noi=False),
        "Fix 1 only: add purchase costs": model(include_costs=True, forward_noi=False),
        "Fix 2 only: forward NOI at exit": model(include_costs=False, forward_noi=True),
        "Corrected (both fixes)": model(include_costs=True, forward_noi=True),
    }
    for k, v in rows.items():
        print(f"{k:34s} outlay £{v['outlay']/1e6:6.2f}m  exit £{v['exit_value']/1e6:6.2f}m  "
              f"IRR {v['irr']:.2%}  NPV@8% £{v['npv']/1e6:+.2f}m")
    print(f"Purchase costs £{PRICE*PURCHASE_COSTS/1e6:.3f}m; Y5 NOI £{noi(5):,.0f}; Y6 NOI £{noi(6):,.0f}")
    print(f"Debt £{debt/1e6:.2f}m, interest £{interest:,.0f}")
    print(f"Interest cover on gross rent: {gross_rent(1)/interest:.2f}x  on NOI: {NOI_Y1/interest:.2f}x  "
          f"covenant {COVENANT_DSCR:.2f}x")
    print(f"NOI fall that breaches covenant: gross-rent basis {1-COVENANT_DSCR*interest/GROSS_RENT_Y1:.0%}, "
          f"NOI basis {1-COVENANT_DSCR*interest/NOI_Y1:.0%}")
    c = model(include_costs=True, forward_noi=True)
    pv_inflows = c["npv"] + c["outlay"]
    print(f"Max price for an 8% unlevered IRR (corrected model): £{pv_inflows/(1+PURCHASE_COSTS)/1e6:.2f}m")
