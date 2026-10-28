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
  if (process.env.GEMINI_API_KEY)
    return { name: 'Google Gemini', url: 'https://generativelanguage.googleapis.com/v1beta/openai/chat/completions',
             key: process.env.GEMINI_API_KEY, model: process.env.GEMINI_MODEL || 'gemini-2.5-flash' };
  if (process.env.OPENAI_API_KEY)
    return { name: 'OpenAI', url: 'https://api.openai.com/v1/chat/completions',
             key: process.env.OPENAI_API_KEY, model: process.env.OPENAI_MODEL || 'gpt-4o-mini' };
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

app.get('/api/firebase-config', (_req, res) => {
  res.json({
    projectId: process.env.FIREBASE_PROJECT_ID || 'aegis-x-59031',
    authDomain: process.env.FIREBASE_AUTH_DOMAIN || 'aegis-x-59031.firebaseapp.com',
    storageBucket: process.env.FIREBASE_STORAGE_BUCKET || 'aegis-x-59031.firebasestorage.app',
    apiKey: process.env.FIREBASE_API_KEY || '',
    appId: process.env.FIREBASE_APP_ID || '',
    messagingSenderId: process.env.FIREBASE_MESSAGING_SENDER_ID || ''
  });
});

app.post('/api/save-firebase-config', (req, res) => {
  const { apiKey, appId, messagingSenderId } = req.body || {};
  try {
    let envContent = fs.readFileSync(path.join(__dirname, '.env'), 'utf8');
    if (apiKey) envContent = envContent.replace(/FIREBASE_API_KEY=.*/, `FIREBASE_API_KEY=${apiKey}`);
    if (appId) envContent = envContent.replace(/FIREBASE_APP_ID=.*/, `FIREBASE_APP_ID=${appId}`);
    if (messagingSenderId) envContent = envContent.replace(/FIREBASE_MESSAGING_SENDER_ID=.*/, `FIREBASE_MESSAGING_SENDER_ID=${messagingSenderId}`);
    fs.writeFileSync(path.join(__dirname, '.env'), envContent, 'utf8');
    process.env.FIREBASE_API_KEY = apiKey || process.env.FIREBASE_API_KEY;
    process.env.FIREBASE_APP_ID = appId || process.env.FIREBASE_APP_ID;
    res.json({ success: true, message: 'Firebase configuration saved' });
  } catch(e) {
    res.status(500).json({ error: e.message });
  }
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
  console.log(`AEGIS X 3.0 running → http://localhost:${PORT}`);
  console.log(p ? `LLM: ${p.name} (${p.model})` : 'LLM: none configured – using local engine (add a key to .env)');
});
