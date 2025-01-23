const socket = io();

const messageForm = document.getElementById('message-form');
const messageInput = document.getElementById('message-input');
const recipientInput = document.getElementById('recipient_input');
const chatMessages = document.getElementById('chat-messages');

messageForm.addEventListener('submit', (e) => {
    e.preventDefault();
    const recipient = recipientInput.value;
    const message = messageInput.value;

    if (message && recipient) {
        socket.emit('message', { message: message, sender: username, recipient: recipient });
        messageInput.value = '';
    }
});

socket.on('message', (data) => {
    const messageItem = document.createElement('li');
    messageItem.textContent = `${data.sender}: ${data.message}`;
    chatMessages.appendChild(messageItem);
});