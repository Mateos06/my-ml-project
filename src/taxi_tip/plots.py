"""Publication-style, static evidence figures; no network calls or model fitting."""
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from sklearn.metrics import precision_recall_curve

INK, GOLD, TEAL = "#152c3a", "#df9f20", "#087e8b"


def setup():
    plt.rcParams.update({"figure.facecolor": "#faf8f2", "axes.facecolor": "#faf8f2", "text.color": INK,
                         "axes.labelcolor": INK, "axes.spines.top": False, "axes.spines.right": False,
                         "font.family": "DejaVu Sans", "font.size": 10, "savefig.dpi": 160})


def save(fig, output: Path, name: str):
    output.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(output / name, bbox_inches="tight")
    plt.close(fig)


def exploratory(frame, payment, rates, output: Path):
    setup()
    fig, ax = plt.subplots(figsize=(9, 4))
    ax.hist(frame.tip_pct.clip(upper=100), bins=np.arange(0, 102, 1), color=TEAL, edgecolor="none")
    ax.axvline(25, color=GOLD, linewidth=2, label="Generous tip threshold · 25%")
    ax.set(xlabel="Recorded tip / fare (%) · values over 100% pooled at 100", ylabel="Card trips", title="May · the shape of recorded tipping")
    ax.legend(frameon=False)
    save(fig, output, "tip-distribution.png")
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.bar(payment.payment_type, payment.recorded_25pct_rate * 100, color=TEAL)
    ax.set(xlabel="Payment type (1 = card; 2 = cash; 0 = flex)", ylabel="Recorded ≥25% tips (%)", title="May · missing cash tips are not zero generosity")
    save(fig, output, "payment-observability.png")
    table = rates["pickup_hour"]
    fig, ax = plt.subplots(figsize=(9, 4))
    ax.plot(table.pickup_hour, 100 * table.rate, color=TEAL, marker="o", markersize=4)
    ax.fill_between(table.pickup_hour, 100 * table.lower_95, 100 * table.upper_95, color=TEAL, alpha=.13)
    ax.set(xlabel="Pickup hour · local recorded clock", ylabel="Generous card tips (%)", title="May · hour differences with 95% Wilson intervals")
    save(fig, output, "hour-rates.png")


def evaluation_figures(y, scores, calibration, threshold_table, output: Path, prefix: str):
    setup()
    precision, recall, _ = precision_recall_curve(y, scores)
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    axes[0].plot(recall, precision, color=TEAL)
    axes[0].axhline(np.mean(y), color=GOLD, linestyle="--", label="Prevalence reference")
    axes[0].set(xlabel="Recall", ylabel="Precision", title=f"{prefix} · precision–recall", xlim=(0, 1), ylim=(0, 1))
    axes[0].legend(frameon=False)
    axes[1].plot([0, 1], [0, 1], color=GOLD, linestyle="--")
    axes[1].plot(calibration.predicted, calibration.observed, marker="o", color=TEAL)
    axes[1].set(xlabel="Mean predicted probability", ylabel="Observed positive rate", title=f"{prefix} · reliability", xlim=(0, 1), ylim=(0, 1))
    save(fig, output, f"{prefix.lower()}-performance.png")
    if threshold_table is not None:
        fig, ax = plt.subplots(figsize=(8, 3.5))
        ax.plot(threshold_table.threshold, threshold_table.cost_per_trip, color=TEAL)
        best = threshold_table.sort_values(["cost_per_trip", "threshold"], ascending=[True, False]).iloc[0]
        ax.scatter([best.threshold], [best.cost_per_trip], color=GOLD, s=70, zorder=3)
        ax.set(xlabel="Decision threshold", ylabel="Cost per trip · FP=1, FN=2", title="June · choosing a decision from stated costs", xlim=(0, 1))
        save(fig, output, "threshold-cost.png")


def zone_map(frame, raw: Path, output: Path):
    """Plot native projected feet; never mislabel them as latitude/longitude."""
    import shapefile
    from matplotlib.collections import PatchCollection
    from matplotlib.patches import Polygon
    candidates = list(raw.rglob("*.shp"))
    if not candidates:
        return
    reader = shapefile.Reader(str(candidates[0]))
    counts = frame.groupby("PULocationID").generous_tip.agg(["size", "mean"])
    patches, values = [], []
    for record in reader.iterShapeRecords():
        zone = int(record.record.as_dict()["LocationID"])
        if zone not in counts.index or counts.loc[zone, "size"] < 200:
            value = np.nan
        else:
            value = 100 * counts.loc[zone, "mean"]
        points = np.array(record.shape.points)
        parts = list(record.shape.parts) + [len(points)]
        for left, right in zip(parts[:-1], parts[1:]):
            patches.append(Polygon(points[left:right], closed=True))
            values.append(value)
    fig, ax = plt.subplots(figsize=(8, 7))
    collection = PatchCollection(patches, cmap="YlGnBu", edgecolor="#ffffff", linewidth=.2)
    collection.set_array(np.array(values))
    ax.add_collection(collection)
    ax.autoscale_view()
    ax.set_aspect("equal")
    ax.set_axis_off()
    ax.set_title("May · generous card tips by pickup zone\nZones with fewer than 200 trips are uncolored")
    fig.colorbar(collection, ax=ax, shrink=.65, label="Generous card tips (%)")
    fig.text(.13, .02, "Native shapefile projection in feet; descriptive association, not a causal map.", fontsize=8)
    save(fig, output, "zone-rates.png")
