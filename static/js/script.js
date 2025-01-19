const socket = io();

const messageForm = document.getElementById('message-form');
const messageInput = document.getElementById('message-input');
const chatMessages = document.getElementById('chat-messages');
const recipient = '{{ recipient }}'; // Get recipient from template

messageForm.addEventListener('submit', (e) => {
    e.preventDefault();
    const message = messageInput.value;
    if (message) {
        socket.emit('message', { message: message, sender: 'YourUsername', recipient: recipient });
        messageInput.value = '';
    }
});

socket.on('message', (data) => {
    const messageItem = document.createElement('li');
    messageItem.textContent = `${data.sender}: ${data.data}`;
    chatMessages.appendChild(messageItem);
});