document.addEventListener('DOMContentLoaded', function() {


    const socket = io.connect('http://' + document.domain + ':5002');
    const recentChatsList = document.getElementById('recent-chats-list');
    const chatMessagesContainer = document.getElementById('chat-messages');
    const sendMessageForm = document.getElementById('send-message-form');
    const messageInput = document.getElementById('message-input');
    const userSearchInput = document.getElementById('user-search-input'); // Assuming you have this input
    const userSearchResults = document.getElementById('user-search-results'); // Assuming you have this div
    let currentActiveChatId = initialActiveChatId;

    socket.on('connect', function() {
        console.log('WebSocket connected!');
        if (currentActiveChatId) {
            socket.emit('join', { room: `chat_${currentActiveChatId}` });
        }
    });

    socket.on('message', function(data) {
    console.log('Received WebSocket message:', data);
    if (data.chat_id === parseInt(currentActiveChatId)) {
        const messageContainer = document.createElement('div');
        messageContainer.classList.add('message-container');
        // ... (creating message bubble and timestamp) ...
        messageBubble.appendChild(messageParagraph);
        messageBubble.appendChild(timestampSmall);
        messageContainer.appendChild(messageBubble);
        chatMessagesContainer.appendChild(messageContainer); // Appending a single message
        scrollToBottom();
    }
});

    recentChatsList.addEventListener('click', function(event) {
        const chatItem = event.target.closest('.chat-item');
        if (chatItem) {
            const chatId = chatItem.dataset.chatId;
            const recipientSpan = chatItem.querySelector('.recipient-info span');
            let recipientUsername = 'Chat'
            if (recipientSpan){
                recipientUsername = recipientSpan.textContent;
            }
            switchChat(chatId, chatItem, recipientUsername);
        }
    });

    function switchChat(chatId, chatItem, recipientUsername) {
    currentActiveChatId = chatId;
    socket.emit('join', { room: `chat_${chatId}` });

    fetch(`/chat_messages/${chatId}`)
        .then(response => response.text())
        .then(data => {
            chatMessagesContainer.innerHTML = data; // Replacing the entire content
            document.querySelector('.active-chat-area h1').textContent = recipientUsername;
            scrollToBottom();
        });

    fetch('/update_last_chat', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ chat_id: chatId })
    });
}

    sendMessageForm.addEventListener('submit', function(event) {
        event.preventDefault();
        const message = messageInput.value.trim();
        if (message && currentActiveChatId) {
            socket.emit('message', { message: message, room: `chat_${currentActiveChatId}` });
            messageInput.value = '';
            const messageContainer = document.createElement('div');
            messageContainer.classList.add('message-container', 'sent');
            const messageBubble = document.createElement('div');
            messageBubble.classList.add('message-bubble');
            const messageParagraph = document.createElement('p');
            messageParagraph.textContent = message;
            const timestampSmall = document.createElement('small');
            timestampSmall.classList.add('message-timestamp');
            const now = new Date();
            const formattedTime = `${now.toLocaleDateString()} ${now.toLocaleTimeString()}`;
            timestampSmall.textContent = formattedTime;
            messageBubble.appendChild(messageParagraph);
            messageBubble.appendChild(timestampSmall);
            messageContainer.appendChild(messageBubble);
            chatMessagesContainer.appendChild(messageContainer);
            scrollToBottom();
        } else if (!currentActiveChatId) {
            alert('Please select a chat to send a message to.');
        }
    });

    function scrollToBottom() {
    const chatMessagesContainer = document.getElementById('chat-messages');
    if (chatMessagesContainer) {
        chatMessagesContainer.scrollTop = chatMessagesContainer.scrollHeight;
        }
    }



    if (currentActiveChatId) {
    fetch(`/chat_messages/${currentActiveChatId}`)
        .then(response => response.text())
        .then(data => {
            chatMessagesContainer.innerHTML = data;
            const initialRecipient = document.querySelector('.recent-chats-list .chat-item[data-chat-id="' + currentActiveChatId + '"] .recipient-info span');
            if (initialRecipient) {
                document.querySelector('.active-chat-area h1').textContent = initialRecipient.textContent;
            }
            scrollToBottom();
        });
    socket.emit('join', { room: `chat_${currentActiveChatId}` });
}

    // --- Add New User/Start Chat Functionality ---
    if (users && users.length > 0) {
    users.forEach(user => {
        const userDiv = document.createElement('div');
        userDiv.classList.add('search-result-user');
        userDiv.textContent = user.username;
        userDiv.dataset.userId = user.id;
        userDiv.addEventListener('click', function() {
            const otherUserId = this.dataset.userId;
            // ... (logic to start a new chat) ...
        });
        userSearchResults.appendChild(userDiv);
    });
    userSearchResults.style.display = 'block'; // Show results
} else {
    const noResults = document.createElement('div');
    noResults.textContent = 'No users found.';
    userSearchResults.appendChild(noResults);
    userSearchResults.style.display = 'block'; // Show "No results"
}
});

