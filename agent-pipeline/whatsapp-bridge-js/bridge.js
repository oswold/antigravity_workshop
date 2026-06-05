/**
 * WhatsApp HTTP Bridge — Baileys-based
 * ─────────────────────────────────────────────────────────────────────────────
 * Starts a local HTTP server on port 3002.
 * On first run: renders a QR code in the terminal — scan with WhatsApp mobile.
 * Session is saved in ./auth_info_baileys/ — no re-scan needed after that.
 *
 * Endpoints:
 *   GET /health           → { status: 'ok', connected: true/false }
 *   GET /messages?days=7  → [ { text, timestamp, sender, links: [] }, ... ]
 *
 * Start: node bridge.js
 */

const { default: makeWASocket, useMultiFileAuthState, DisconnectReason, fetchLatestBaileysVersion } = require('@whiskeysockets/baileys');
const qrcode  = require('qrcode-terminal');
const http    = require('http');
const url     = require('url');
const fs      = require('fs');
const path    = require('path');

const PORT        = 3002;
const AUTH_FOLDER = path.join(__dirname, 'auth_info_baileys');
const URL_REGEX   = /https?:\/\/[^\s>\"']+/g;

let sock       = null;
let isReady    = false;
let msgStore   = [];   // in-memory store of recent messages

const CACHE_FILE = path.join(AUTH_FOLDER, 'messages_cache.json');

// Load cache
try {
  if (fs.existsSync(CACHE_FILE)) {
    msgStore = JSON.parse(fs.readFileSync(CACHE_FILE, 'utf8'));
    console.log(`✅ Loaded ${msgStore.length} cached messages from persistent storage.`);
  }
} catch (e) {
  console.error('⚠️ Error loading message cache:', e);
}

// ── Connect to WhatsApp ───────────────────────────────────────────────────────
async function connectToWhatsApp() {
  const { state, saveCreds } = await useMultiFileAuthState(AUTH_FOLDER);
  const { version } = await fetchLatestBaileysVersion();

  sock = makeWASocket({
    version,
    auth: state,
    printQRInTerminal: false,   // We handle QR ourselves
    syncFullHistory: false,
    getMessage: async () => undefined,
  });

  // ── QR Code ───────────────────────────────────────────────────────────────
  sock.ev.on('connection.update', async (update) => {
    const { connection, lastDisconnect, qr } = update;

    if (qr) {
      console.log('\n\n📱  SCAN THIS QR CODE WITH YOUR WHATSAPP MOBILE APP\n');
      qrcode.generate(qr, { small: true });
      console.log('\n  WhatsApp → Linked Devices → Link a Device → Scan\n');
    }

    if (connection === 'open') {
      console.log('✅  WhatsApp connected! Bridge is ready on port', PORT);
      isReady = true;
    }

    if (connection === 'close') {
      isReady = false;
      const shouldReconnect =
        lastDisconnect?.error?.output?.statusCode !== DisconnectReason.loggedOut;
      console.log('⚠️  Connection closed — reconnecting:', shouldReconnect);
      if (shouldReconnect) {
        setTimeout(connectToWhatsApp, 3000);
      }
    }
  });

  sock.ev.on('creds.update', saveCreds);

  // ── Cache incoming messages ───────────────────────────────────────────────
  sock.ev.on('messages.upsert', ({ messages }) => {
    let changed = false;
    for (const msg of messages) {
      if (!msg.message) continue;
      const text =
        msg.message?.conversation ||
        msg.message?.extendedTextMessage?.text ||
        msg.message?.imageMessage?.caption ||
        '';
      if (!text) continue;

      // Avoid duplicates
      if (msgStore.some(m => m.id === msg.key.id)) continue;

      msgStore.push({
        id:        msg.key.id,
        text,
        timestamp: msg.messageTimestamp,
        sender:    msg.key.remoteJid,
        fromMe:    msg.key.fromMe,
        links:     text.match(URL_REGEX) || [],
      });
      changed = true;
    }

    if (changed) {
      // Keep last 500 messages only
      if (msgStore.length > 500) msgStore = msgStore.slice(-500);

      try {
        fs.writeFileSync(CACHE_FILE, JSON.stringify(msgStore, null, 2));
      } catch (e) {
        console.error('⚠️ Error saving message cache:', e);
      }
    }
  });
}

// ── HTTP Server ───────────────────────────────────────────────────────────────
const server = http.createServer((req, res) => {
  const parsed = url.parse(req.url, true);
  res.setHeader('Content-Type', 'application/json');
  res.setHeader('Access-Control-Allow-Origin', '*');

  // GET /health
  if (parsed.pathname === '/health') {
    res.end(JSON.stringify({ status: 'ok', connected: isReady }));
    return;
  }

  // GET /user
  if (parsed.pathname === '/user') {
    res.end(JSON.stringify(sock ? sock.user : null));
    return;
  }

  // GET /messages?days=7&self_only=true
  if (parsed.pathname === '/messages') {
    if (!isReady) {
      res.statusCode = 503;
      res.end(JSON.stringify({ error: 'WhatsApp not connected yet. Check terminal for QR code.' }));
      return;
    }

    const days     = parseInt(parsed.query.days || '7', 10);
    const selfOnly = parsed.query.self_only !== 'false';  // default: true
    const since    = Math.floor(Date.now() / 1000) - days * 86400;

    const getBaseJid = (jid) => {
      if (!jid) return null;
      const parts = jid.split('@');
      const cleanUser = parts[0].split(':')[0];
      return parts[1] ? `${cleanUser}@${parts[1]}` : cleanUser;
    };
    const ownJid = getBaseJid(sock?.user?.id);
    const ownLid = getBaseJid(sock?.user?.lid);

    let messages = msgStore.filter(m => {
      const ts = typeof m.timestamp === 'object'
        ? Number(m.timestamp.low || m.timestamp)
        : Number(m.timestamp);
      if (ts < since) return false;
      
      if (selfOnly) {
        const chatJid = getBaseJid(m.sender);
        if (chatJid !== ownJid && chatJid !== ownLid) {
          return false;
        }
      }
      return true;
    });

    // Sort newest first, limit to 30
    messages = messages
      .sort((a, b) => Number(b.timestamp) - Number(a.timestamp))
      .slice(0, 30);

    res.end(JSON.stringify(messages));
    return;
  }

  res.statusCode = 404;
  res.end(JSON.stringify({ error: 'Not found' }));
});

server.listen(PORT, () => {
  console.log(`\n🌉  WhatsApp Bridge HTTP server running on http://localhost:${PORT}`);
  console.log('   Waiting for WhatsApp connection...\n');
});

connectToWhatsApp().catch(console.error);
