# Case study: peer-reviewing a property acquisition DCF

*An illustrative example of the errors I look for when reviewing a colleague's valuation model. The asset and all figures are fictional; every number below is reproduced by `case_study/property_case.py`.*

## The situation

A colleague had built the DCF for a proposed acquisition of a multi-let regional office building, asking price **£13.4m**, to go to the client's investment committee the next morning. The client's hurdle was an **8% unlevered IRR** over a five-year hold, and the purchase would be funded at **55% LTV**, with a lender covenant of **2.0x interest cover**.

The draft showed an IRR of **8.69%**, a positive NPV of **£0.38m** at 8%, and interest cover of **2.76x**, so the recommendation was to proceed at the asking price.

## How I reviewed it

I did not start from the headline IRR. A result that clears the hurdle by about 0.7 points can still hide errors that move it by more than that. I worked through the model in four steps:

1. **Rebuild the cash flows from the assumptions:** rent, non-recoverable costs, NOI growth, exit and sale costs. I did this independently in Python, then compared my rebuild with the Excel model line by line.
2. **Check what each formula refers to:** which NOI year the exit cap rate is applied to, what the Year 0 outlay contains, and what the cover ratio is measured on.
3. **Find the first line that diverges** and trace it back to an input or formula.
4. **Size each error separately**, so the committee could see which errors mattered and by how much.

## What I found

| # | Issue | Draft | Corrected | Effect on IRR |
|---|---|---|---|---|
| 1 | Purchase costs (stamp duty, legal and agency fees, 6.8% of price) left out of the Year 0 outlay | £13.40m outlay | £14.31m | **−1.6 pts** |
| 2 | Exit cap rate applied to Year 5 (trailing) NOI instead of Year 6 (forward) NOI, which is what a buyer would pay for | £14.66m net exit value | £15.02m | +0.4 pts |
| 3 | Interest cover calculated on **gross rent** instead of NOI | 2.76x | **2.24x** | n/a (financing risk) |

**Combined effect:**

| | Draft | Corrected |
|---|---|---|
| Unlevered IRR | 8.69% | **7.52%** |
| NPV at 8% | +£0.38m | **−£0.28m** |
| NOI fall before covenant breach | 28% | **11%** |

Two things stood out:

- **The errors partly offset.** Error 2 understated value, so fixing it alone would have made the deal look *better*, at a 9.13% IRR. Only fixing both errors showed that the deal **did not clear the 8% hurdle at the asking price**.
- **Error 3 changed the risk picture, not the return.** On the draft, the deal could survive a 28% fall in income before breaching the covenant. In reality the headroom was 11%, roughly the loss of one mid-sized tenant.

## Outcome

I sent the colleague a short note before the committee: each issue, the cell reference, the corrected figure and its effect. We agreed the fixes together, and the paper went to committee with the corrected numbers. The recommendation changed from "proceed at asking price" to **bid no higher than about £13.1m**, which is the price that delivers 8% on the corrected cash flows. It also flagged the thin covenant headroom, so lower leverage or a longer lease profile would be needed before proceeding.

## What I check on every DCF now

- Year 0 includes **all-in** acquisition costs, not just the price.
- The exit value capitalises **forward** income, and sale costs are deducted.
- Cover and yield ratios state what they are measured on (gross rent, NOI or cash flow) and use the same basis as the lender's definition.
- The terminal or exit value is discounted the correct number of periods.
- Each error is sized **on its own**, because errors that offset can make a wrong model look right.

---

### Interview version (about 60 seconds)

> **Situation:** A colleague's acquisition model for a £13.4m office building was going to the investment committee the next day, showing an 8.7% IRR against an 8% hurdle.
> **Task:** I was asked to peer-review it before it went out.
> **Action:** Instead of sense-checking the headline IRR, I rebuilt the cash flows independently in Python and reconciled them line by line with the Excel model. I found three issues: purchase costs were missing from the Year 0 outlay, the exit was capitalised on trailing rather than forward NOI, and interest cover was measured on gross rent instead of NOI. I sized each one separately, because two of them pulled in opposite directions.
> **Result:** The corrected IRR was 7.5%, below the hurdle, and covenant headroom was 11% rather than 28%. The committee paper went out with corrected numbers and a recommended maximum bid of about £13.1m instead of the asking price. The lesson I took away was that offsetting errors can make a wrong model look right, which is exactly what you need to catch when reviewing AI-generated analysis too.
