"""Generate the four thin, narrated notebooks from reproducible source imports."""
from pathlib import Path
import nbformat as nbf

ROOT = Path(__file__).resolve().parents[1]
SETUP = '''from pathlib import Path
import json
import pandas as pd
from IPython.display import display, Markdown, Image
from taxi_tip.config import ROOT, REPORTS, ARTIFACTS
from taxi_tip.data import read_split, clean_trips
print("Project:", ROOT)
'''


def create(name, cells):
    notebook = nbf.v4.new_notebook()
    notebook.metadata.kernelspec = {"display_name": "Python 3", "language": "python", "name": "python3"}
    notebook.metadata.language_info = {"name": "python", "version": "3.11"}
    notebook.cells = [nbf.v4.new_markdown_cell(text) if kind == "md" else nbf.v4.new_code_cell(text) for kind, text in cells]
    target = ROOT / "notebooks" / name
    target.parent.mkdir(exist_ok=True)
    nbf.write(notebook, target)


create("01-frame.ipynb", [
    ("md", "# 01 · Frame\n\nOne question: at payment time, which eligible card trips end in a recorded tip of at least 25% of the fare? Read the problem card before examining outcomes."),
    ("code", SETUP),
    ("code", 'display(Markdown((ROOT / "PROBLEM.md").read_text(encoding="utf-8")))'),
    ("md", "## Check the boundary\n\nExactly 25% is positive. Cash is outside the observable population. A tip is not compared with total amount."),
    ("code", '''examples = pd.DataFrame({"fare_amount": [20., 20., 20., 0.], "tip_amount": [5., 4.99, 0., 0.], "payment_type": [1, 1, 2, 1]})
examples["eligible_target"] = (examples.payment_type == 1) & (examples.fare_amount > 0)
examples["positive_if_eligible"] = (examples.tip_amount >= .25 * examples.fare_amount).where(examples.eligible_target)
display(examples)'''),
    ("md", "## Defense checkpoint\n\nExplain why distance and rate code are usable at payment but not automatically at booking. Explain why `total_amount` is forbidden and why an all-negative baseline can still have nonzero AP. Costs are assumptions: FP=1, FN=2, not measured dollars."),
])
create("02-clean-and-split.ipynb", [
    ("md", "# 02 · Clean and split\n\nLoad May and June only. Cleaning is stateless; fixed bounds never learn from a held-out distribution."),
    ("code", SETUP),
    ("code", '''from taxi_tip.data import payment_audit
may_raw = read_split("train")
june_raw = read_split("validation")
may, may_audit = clean_trips(may_raw)
june, june_audit = clean_trips(june_raw)
display(pd.DataFrame({"month": ["May", "June"], "raw_n": [len(may_raw), len(june_raw)], "eligible_n": [len(may), len(june)], "positive_rate": [may.generous_tip.mean(), june.generous_tip.mean()]}))
display(may_audit)
display(june_audit)'''),
    ("md", "## Prove the observability problem\n\nThe table below reports recorded tips. Non-card rates do not measure actual generosity. Card-only eligibility prevents cash zeros from entering the negative class."),
    ("code", "display(payment_audit(may_raw))"),
    ("code", '''from taxi_tip.evaluation import rate_table, SLICE_COLUMNS
for column in SLICE_COLUMNS:
    display(Markdown(f"### {column}"))
    display(rate_table(may, column))'''),
    ("code", '''import matplotlib.pyplot as plt
fig, ax = plt.subplots(figsize=(9, 3))
ax.hist(may.tip_pct.clip(upper=100), bins=100)
ax.axvline(25, color="orange")
ax.set(xlabel="Tip / fare (%) · >100 pooled", ylabel="Card trips", title="May tip distribution")
plt.show()'''),
    ("md", "## Defend the policy\n\nUnknown zones and nonstandard fares remain flagged. Missing passengers become unknown categories. Cash, flex fares, invalid monetary components and impossible journeys are excluded by explicit rules. Five-percentage-point rate differences are descriptive practical-effect flags; confidence intervals and sample sizes matter. July outcomes have not been examined here."),
])
create("03-features.ipynb", [
    ("md", "# 03 · Features and models\n\nAll learned transformations fit May. June decides which additions survive and which model wins. Running this notebook in a fresh clone builds the frozen artifacts; rerunning an existing completed study reads its reports."),
    ("code", SETUP),
    ("code", '''from taxi_tip.workflow import develop
if not (ARTIFACTS / "selection.json").exists():
    selection = develop()
else:
    selection = json.loads((ARTIFACTS / "selection.json").read_text())
    print("Using this run's frozen selection; no model fitting.")
display(selection)'''),
    ("code", '''from taxi_tip.config import FEATURE_GROUPS, FORBIDDEN
from taxi_tip.models import feature_columns, make_pipeline
numeric, categorical = feature_columns(selection["feature_groups"])
assert not FORBIDDEN.intersection(numeric + categorical)
display(pd.DataFrame({"feature": numeric + categorical, "kind": ["numeric"]*len(numeric) + ["categorical"]*len(categorical)}))
display(make_pipeline(selection["feature_groups"]))'''),
    ("code", '''display(pd.read_csv(REPORTS / "tables" / "feature_comparison.csv"))
display(pd.read_csv(REPORTS / "validation_metrics.csv"))
display(Image(filename=str(REPORTS / "figures" / "june-performance.png")))
display(Image(filename=str(REPORTS / "figures" / "threshold-cost.png")))'''),
    ("md", "## Explain the losses\n\nA group below the 0.001 AP gain requirement is rejected and remains in the ledger. The greedy procedure is order dependent and uses logistic regression to select the representation for both model families. June is reused for multiple choices, so its best score is optimistic. No July score informed this decision."),
])
create("04-evaluate.ipynb", [
    ("md", "# 04 · Evaluate and defend\n\nThis stage opens July once, using the frozen model. Repeated execution reuses saved results. Do not delete the holdout lock to tune against July."),
    ("code", SETUP),
    ("code", '''from taxi_tip.workflow import final_evaluate
result = final_evaluate(repetitions=500)
display(result)
display(pd.read_csv(REPORTS / "test_metrics.csv"))
display(pd.read_csv(REPORTS / "tables" / "bootstrap_intervals.csv"))'''),
    ("code", '''display(Image(filename=str(REPORTS / "figures" / "july-performance.png")))
slices = pd.read_csv(REPORTS / "tables" / "test_slices.csv")
display(slices.loc[slices.n >= 200].sort_values("cost_per_trip", ascending=False).head(12))
display(pd.read_csv(REPORTS / "tables" / "test_reliability.csv"))'''),
    ("code", '''from taxi_tip.reporting import build_docs
build_docs()
display(Markdown((ROOT / "MODEL_CARD.md").read_text(encoding="utf-8")))'''),
    ("md", "## Final defense\n\nRead the model card's limitations, including cash exclusion, hypothetical costs, temporal drift, missing rider context, and trip-level bootstrap assumptions. Review `presentation/DEFEND.md`. Team D reviews Team A: `PEER_REVIEW.md` remains pending until a real repository is reviewed and the review is delivered. AI assistance is disclosed in the README; every team member must understand the implementation."),
])
print("Created four stage notebooks.")
