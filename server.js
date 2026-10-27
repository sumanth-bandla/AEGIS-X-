require('dotenv').config();
const express = require('express');
const fs = require('fs');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 3000;
const DATA_DIR = path.join(__dirname, 'data');
app.use(express.json({ limit: '2mb' }));
app.use(express.static(path.join(__dirname, 'public')));

/* ---------- LLM provider selection (keys stay on the server) ---------- */
function provider() {
  if (process.env.NVIDIA_API_KEY)
    return { name: 'NVIDIA', url: 'https://integrate.api.nvidia.com/v1/chat/completions',
             key: process.env.NVIDIA_API_KEY, model: process.env.NVIDIA_MODEL || 'meta/llama-3.1-70b-instruct' };
  if (process.env.NEBIUS_API_KEY)
    return { name: 'Nebius', url: 'https://api.studio.nebius.com/v1/chat/completions',
             key: process.env.NEBIUS_API_KEY, model: process.env.NEBIUS_MODEL || 'meta-llama/Llama-3.3-70B-Instruct' };
  return null;
}

app.get('/api/status', (_req, res) => {
  const p = provider();
  res.json({ connected: !!p, provider: p ? p.name : 'Local engine', model: p ? p.model : 'rule-based' });
});

/* ---------- streaming chat (OpenAI-compatible SSE passthrough) ---------- */
app.post('/api/chat', async (req, res) => {
  const p = provider();
  if (!p) return res.status(503).json({ error: 'no_key' });
  const { question = '', context = '' } = req.body || {};
  const system = 'You are AEGIS X, an AI data-investigation agent. Answer ONLY from the dataset context provided. ' +
    'Cite finding IDs (e.g. F003) and row numbers as evidence. Be concise, plain, and say when the data cannot answer.\n\nDATASET CONTEXT:\n' +
    String(context).slice(0, 12000);
  try {
    const up = await fetch(p.url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${p.key}` },
      body: JSON.stringify({ model: p.model, stream: true, temperature: 0.2, max_tokens: 700,
        messages: [{ role: 'system', content: system }, { role: 'user', content: String(question).slice(0, 2000) }] })
    });
    if (!up.ok) return res.status(502).json({ error: 'upstream', status: up.status, detail: (await up.text()).slice(0, 300) });
    res.set({ 'Content-Type': 'text/event-stream', 'Cache-Control': 'no-cache', Connection: 'keep-alive' });
    const dec = new TextDecoder(); let buf = '';
    for await (const chunk of up.body) {
      buf += dec.decode(chunk, { stream: true });
      const lines = buf.split('\n'); buf = lines.pop();
      for (const l of lines) {
        if (!l.startsWith('data:')) continue;
        const d = l.slice(5).trim();
        if (d === '[DONE]') continue;
        try { const t = JSON.parse(d).choices?.[0]?.delta?.content; if (t) res.write(`data: ${JSON.stringify({ t })}\n\n`); } catch {}
      }
    }
    res.write('data: {"done":true}\n\n'); res.end();
  } catch (e) {
    if (!res.headersSent) res.status(502).json({ error: 'network', detail: String(e.message) });
    else res.end();
  }
});

/* ---------- live dataset feed: drop a .csv into ./data and every open browser analyses it instantly ---------- */
const clients = new Set();
app.get('/api/events', (req, res) => {
  res.set({ 'Content-Type': 'text/event-stream', 'Cache-Control': 'no-cache', Connection: 'keep-alive' });
  res.write('retry: 2000\n\n');
  clients.add(res);
  const ka = setInterval(() => res.write(': ping\n\n'), 25000);
  req.on('close', () => { clearInterval(ka); clients.delete(res); });
});
const timers = {};
function pushFile(f) {
  try {
    const text = fs.readFileSync(path.join(DATA_DIR, f), 'utf8');
    const msg = `event: dataset\ndata: ${JSON.stringify({ name: f, text })}\n\n`;
    clients.forEach(c => c.write(msg));
    console.log(`[live] pushed ${f} to ${clients.size} client(s)`);
  } catch {}
}
fs.mkdirSync(DATA_DIR, { recursive: true });
fs.watch(DATA_DIR, (_e, f) => {
  if (!f || !f.toLowerCase().endsWith('.csv')) return;
  clearTimeout(timers[f]); timers[f] = setTimeout(() => pushFile(f), 250);
});

app.listen(PORT, () => {
  const p = provider();
  console.log(`AEGIS X 2.0 running → http://localhost:${PORT}`);
  console.log(p ? `LLM: ${p.name} (${p.model})` : 'LLM: none configured – using local engine (add a key to .env)');
});
