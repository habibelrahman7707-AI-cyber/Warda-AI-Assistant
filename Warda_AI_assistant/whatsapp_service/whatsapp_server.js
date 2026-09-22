const { Client, LocalAuth } = require('whatsapp-web.js');
const qrcode = require('qrcode-terminal');
const express = require('express');
const axios = require('axios');
const fs = require('fs');
const path = require('path');
const multer = require('multer');

const app = express();
app.use(express.json({limit: '50mb'}));

// Port for this Node service
const PORT = 3001;
// Webhook URL of the Python Desktop App
const PYTHON_WEBHOOK_URL = 'http://127.0.0.1:3002/webhook';

// Directory to save media
const MEDIA_DIR = path.join(require('os').homedir(), 'Downloads', 'WhatsApp_Media');
if (!fs.existsSync(MEDIA_DIR)) {
    fs.mkdirSync(MEDIA_DIR, { recursive: true });
}

// Initialize WhatsApp Client
const client = new Client({
    authStrategy: new LocalAuth({ dataPath: './wwebjs_auth' }),
    puppeteer: { 
        executablePath: 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
        headless: true,
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    }
});

client.on('loading_screen', (percent, message) => {
    console.log(`[WhatsApp] Loading: ${percent}% - ${message}`);
});

client.on('qr', (qr) => {
    console.log('[WhatsApp] Need to scan QR! Generating code...');
    qrcode.generate(qr, { small: true });
});

client.on('authenticated', () => {
    console.log('[WhatsApp] Authenticated successfully!');
});

client.on('auth_failure', msg => {
    console.error('[WhatsApp] Authentication failure:', msg);
});

client.on('ready', () => {
    console.log('[WhatsApp] Client is ready!');
});

client.on('message', async msg => {
    // Ignore status updates
    if (msg.from === 'status@broadcast') return;
    
    // Ignore internal @lid messages (usually communities/linked devices)
    if (msg.from.includes('@lid')) return;
    
    try {
        let mediaPath = null;
        let textBody = msg.body;
        
        let senderName = msg.from.split('@')[0];
        try {
            const contact = await msg.getContact();
            senderName = contact.name || contact.pushname || senderName;
        } catch (err) {
            console.error('[WhatsApp] Error getting contact name, falling back to number:', err.message);
        }
        
        console.log(`[WhatsApp] Received message from ${senderName} (type: ${msg.type})`);
        
        // If it's a media message (image, video, document, voice note)
        if (msg.hasMedia) {
            try {
                const media = await msg.downloadMedia();
                if (media) {
                    const extension = media.mimetype.split('/')[1].split(';')[0];
                    const filename = `msg_${Date.now()}.${extension === 'ogg' ? 'ogg' : extension}`;
                    mediaPath = path.join(MEDIA_DIR, filename);
                    fs.writeFileSync(mediaPath, media.data, 'base64');
                    console.log(`[WhatsApp] Media saved to ${mediaPath}`);
                }
            } catch (mediaErr) {
                console.error(`[WhatsApp] Failed to download media: ${mediaErr.message}`);
                textBody = textBody ? textBody + ' [Failed to download media due to WhatsApp Web bug]' : '[Failed to download media due to WhatsApp Web bug]';
            }
        }
        
        // Send webhook to Python App
        const payload = {
            from: senderName, // Send the actual Name!
            author: msg.author || senderName,
            body: textBody,
            type: msg.type,
            hasMedia: msg.hasMedia,
            mediaPath: mediaPath,
            timestamp: msg.timestamp
        };
        
        axios.post(PYTHON_WEBHOOK_URL, payload)
            .then(res => console.log('[WhatsApp] Forwarded to Python UI'))
            .catch(err => console.log('[WhatsApp] Warning: Python UI not running or webhook failed.'));
            
    } catch (e) {
        console.error('[WhatsApp] Error processing message:', e);
    }
});

client.initialize();

// Express APIs for Python to command WhatsApp

// 1. Send Message
app.post('/send', async (req, res) => {
    const { to, message } = req.body;
    if (!to || !message) return res.status(400).json({ error: 'Missing to or message' });
    
    try {
        const chatId = to.includes('@c.us') || to.includes('@g.us') ? to : `${to}@c.us`;
        await client.sendMessage(chatId, message);
        res.json({ success: true, message: 'Sent successfully' });
    } catch (e) {
        res.status(500).json({ error: e.toString() });
    }
});

// 2. Get Recent Contacts (Replaced getChats due to r:r bug)
app.get('/chats', async (req, res) => {
    try {
        const query = (req.query.q || '').toLowerCase();
        const contacts = await client.getContacts();
        let simplifiedContacts = contacts
            .filter(c => c.name || c.pushname) // only valid named contacts
            .map(c => ({
                id: c.id._serialized,
                name: c.name || c.pushname,
                isGroup: c.isGroup
            }));
            
        if (query) {
            simplifiedContacts = simplifiedContacts.filter(c => c.name.toLowerCase().includes(query)).slice(0, 10);
        } else {
            simplifiedContacts = simplifiedContacts.slice(0, 30);
        }
        res.json(simplifiedContacts);
    } catch (e) {
        res.status(500).json({ error: e.toString() });
    }
});

// 3. Get Messages from specific Chat
app.get('/chat/:id', async (req, res) => {
    try {
        const chatId = req.params.id;
        const chat = await client.getChatById(chatId);
        const messages = await chat.fetchMessages({ limit: 15 });
        const history = messages.map(m => ({
            fromMe: m.fromMe,
            body: m.body,
            type: m.type,
            timestamp: m.timestamp
        }));
        res.json(history);
    } catch (e) {
        res.status(500).json({ error: e.toString() });
    }
});

app.listen(PORT, () => {
    console.log(`[WhatsApp Server] Express API running on port ${PORT}`);
});
