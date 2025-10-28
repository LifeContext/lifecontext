// server.js
import express from 'express';
import bodyParser from 'body-parser';
import { Dataset } from 'crawlee';

const app = express();
const PORT = 3000;

app.use(bodyParser.json({ limit: '10mb' }));

// 简单 CORS（只允许本机）
// server.js 中
app.use((req, res, next) => {
  res.setHeader('Access-Control-Allow-Origin', '*'); // 或 chrome-extension://<your-extension-id>
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  if (req.method === 'OPTIONS') return res.sendStatus(200);
  next();
});


app.post('/save', async (req, res) => {
  try {
    const payload = req.body; // 期望为 { url, text, images, videos, meta? }
    if (!payload || !payload.url) {
      return res.status(400).json({ ok: false, error: 'missing payload or url' });
    }

    // 将数据写入 Crawlee Dataset（会存到 ./storage/datasets/default）
    await Dataset.pushData(payload);

    return res.json({ ok: true });
  } catch (err) {
    console.error('Error saving dataset:', err);
    return res.status(500).json({ ok: false, error: String(err) });
  }
});

app.listen(PORT, () => {
  console.log(`Local dataset server listening on http://localhost:${PORT}`);
});
