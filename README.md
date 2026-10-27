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
