# Standalone pages

Two self-contained HTML files. Double-click either one to open it in a browser -
no server, no build step, no internet beyond the Google Fonts link. Everything
else, including the customer data and the 3D renderer, is inside the file.

| File | What it is |
|---|---|
| [landing.html](landing.html) | The product landing page. 3D customer field behind the headline, with messages flying to the persuadable ones, then how it works, the numbers and what is still broken. |
| [customer-explorer.html](customer-explorer.html) | The explainer. Same field, bigger and interactive: click a customer for their scores, run a campaign on the top 30% and see the predicted lift. |

Both draw the same 48 customers from `data/examples/sales_sample.csv`, scored by
the transferable uplift model. The numbers are the model's real output, not
mock-ups. Regenerate them with:

```
python scripts/score_shop.py --sales data/examples/sales_sample.csv
```

The figures quoted on both pages come from `docs/TAGGING_ACCURACY.md` and
`docs/JACK_WORK.md`. If those change, change these too - nothing updates
automatically.

## The field

Three axes: days since last visit, uplift, months as a customer. Drag to turn it,
arrow keys work too. The flat grid is zero uplift; a few customers sit below it,
where the model expects a message to make things slightly worse.

Looking along the recency axis shows the gap worth knowing about before the
pitch: the customers who have not visited in months all sit low, because the
model has no recency feature and cannot tell a lapsed customer from a quiet one.

## Not the app

These are for showing the project. The working app is the Streamlit one in
`app/`, which has the same field on its Results page, built from the shop's own
customers rather than the sample.
