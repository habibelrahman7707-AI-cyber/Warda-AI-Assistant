const { Client, LocalAuth } = require('whatsapp-web.js');

const client = new Client({
    authStrategy: new LocalAuth({ dataPath: './wwebjs_auth' }),
    puppeteer: { 
        executablePath: 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
        headless: true,
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    }
});

client.on('ready', async () => {
    console.log('[WhatsApp] Client is ready!');
    try {
        const contacts = await client.getContacts();
        console.log("Contacts count:", contacts.length);
        const chats = await client.getChats();
        console.log("Chats count:", chats.length);
    } catch(e) {
        console.error("Error:", e.toString());
    }
    process.exit(0);
});

client.initialize();
