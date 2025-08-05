const express = require('express');
const fs = require('fs');
const path = require('path');

const app = express();
const port = process.env.PORT || 3000;
const logLevel = process.env.LOG_LEVEL || 'info';

app.use(express.json());

// Store messages in memory (for demo purposes)
let messages = [];

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({ status: 'healthy', service: 'chat-service' });
});

// Get all messages
app.get('/messages', (req, res) => {
  res.json({ messages });
});

// Send a message
app.post('/messages', (req, res) => {
  const { sender, recipient, message, channel } = req.body;
  
  const newMessage = {
    id: messages.length + 1,
    sender,
    recipient,
    message,
    channel: channel || 'general',
    timestamp: new Date().toISOString()
  };
  
  messages.push(newMessage);
  
  // Log the message
  const logEntry = `${newMessage.timestamp} - ${sender} -> ${recipient || 'ALL'} [${newMessage.channel}]: ${message}\n`;
  fs.appendFileSync(path.join('/app/logs', 'chat.log'), logEntry);
  
  res.json({ success: true, message: newMessage });
});

// Clear all messages (for testing)
app.delete('/messages', (req, res) => {
  messages = [];
  res.json({ success: true, message: 'All messages cleared' });
});

app.listen(port, '0.0.0.0', () => {
  console.log(`Chat service running on port ${port}`);
});
