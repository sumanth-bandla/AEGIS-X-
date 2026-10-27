# AEGIS X — Open AI Investigation Agent

Verify the data. Investigate the evidence. Understand the results.

AEGIS X is an AI-assisted data investigation platform. Upload a CSV, get a
data-quality and statistical overview, explore visualizations, identify unusual
records, ask questions in natural language, and generate a report with findings,
supporting calculations, limitations, and evidence references.

Core principle: **Calculate with code. Explain with AI. Verify with evidence.**

## Features

- CSV upload with validation, size limits, encoding handling, duplicate-column detection
- Dataset profiling: types, missingness, duplicates, numeric/categorical summaries, date ranges, quality issues
- Exploratory visualizations: histograms, bars, scatter, box, correlation heatmap, time series (Plotly)
- Interpretable anomaly detection: IQR, Z-score, missingness rules
- Evidence/provenance engine: every finding traceable to calculation or record
- AI investigation assistant (NVIDIA via Nebius, OpenAI-compatible) grounded in calculated evidence
- Report generation (Markdown + CSV findings)
- Works without an AI key (deterministic analysis only)

## Setup

```powershell
cd aegis-x
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
# edit .env with your key
streamlit run app.py
```

## AI configuration

Set `NEBIUS_API_KEY` (preferred) or `OPENAI_API_KEY` in `.env`. Base URL and
model are configurable. The app degrades gracefully when no key is present.

## Tests

```powershell
pytest -q
```

## Deployment

Streamlit Community Cloud: point to `app.py`, add secrets via the dashboard.

## Known limitations

- In-memory only; no persistence.
- Row references tied to current dataset version.
- Anomalies are unusual, not proof of error/fraud.
- AI explanations are grounded but probabilistic.

## License

MIT