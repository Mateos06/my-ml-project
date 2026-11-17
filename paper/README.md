# Research paper

- [PDF](the-tipping-point.pdf) — formatted reading and printing copy.
- [Word document](the-tipping-point.docx) — editable manuscript with tables and figures.
- [Markdown source](the-tipping-point.md) — the source used to render both documents.

The manuscript covers the problem, background, original dataset, target observability, cleaning, feature selection, temporal evaluation, model comparisons, uncertainty, error slices, discussion, ethics, reproducibility, references, and requirement traceability. Author information uses the repository's Team D designation. Individual names and university-specific submission details were not supplied.

Results are based on the saved study at revision `6f7cc9f503d8746cdffb43aebedbdd495ba94316`, recorded on 3 November 2026. The manuscript was prepared on 17 November 2026 without refitting models or rescoring July. Figures 1–2 are rendered from saved aggregate CSVs; Figures 3–4 use existing report figures. Vector versions of the two new figures are included alongside PNGs in `figures/`.

## Rebuild the documents

Use a separate environment for document rendering. The pinned renderer was used with Python 3.14; it is independent of the study's recorded Python 3.11 environment.

```bash
python -m venv .venv-paper
```

Activate that environment using the appropriate command for your operating system, then run from the repository root:

```bash
python -m pip install -r paper/requirements.txt
python scripts/build_paper.py
```

The builder uses fonts bundled with Matplotlib and needs no LaTeX or Microsoft Word installation. Its outputs are the PDF, DOCX, and two new figure pairs. It does not regenerate the analysis or automatically revise numerical claims in the Markdown prose. Edit the Markdown to change the manuscript, then rebuild. Direct edits in Word will be overwritten by rebuilding.
