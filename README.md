<<<<<<< HEAD
# AEGIS X 2.0 – AI Investigation Agent

Upload a CSV, get evidence-backed findings (missing values, duplicates, rule violations, outliers), and ask an LLM Copilot questions about your data – with live streaming answers.

## Features
- **Real analysis engine** – null detection, exact duplicates, Quantity × Price = Total check, negative values, IQR outliers
- **Evidence Explorer** – every finding links to method, threshold and affected rows
- **AI Copilot** – streams answers from **NVIDIA NIM** or **Nebius AI Studio** (keys stay on the server); falls back to a local rule engine with no key
- **Real-time feed** – drop a `.csv` into `./data` and every open browser analyses it instantly (Server-Sent Events)
- **Exports** – findings CSV and Markdown report

## Run
```bash
git clone https://github.com/sumanth-bandla/AEGIS-X.git && cd AEGIS-X
npm install
cp .env.example .env      # add NVIDIA_API_KEY and/or NEBIUS_API_KEY
npm start                 # http://localhost:3000
```
Try live mode: `cp sample/Sales_Analysis_Dataset.csv data/` while the app is open.

## Structure
```
server.js        Express API: /api/status, /api/chat (SSE stream), /api/events (live feed)
public/index.html  Dashboard UI + analysis engine
data/            watched folder for live datasets
sample/          example CSV
```
Never commit `.env`. Rotate any key you have pasted anywhere public.

## Stack
Node 18+, Express, vanilla JS, NVIDIA NIM / Nebius (OpenAI-compatible chat API).
=======
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
>>>>>>> 8527a8843f52cd1d29f07e0fbc8c67a98bb34595
