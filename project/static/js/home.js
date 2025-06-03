import sodium from 'libsodium-wrappers';
function arrayBufferToBase64(buffer){
    let binary = '';
    const bytes = new Uint8Array(buffer);
    const len = bytes.byteLength;
    for (let i = 0; i < len; i++){
        binary += String.fromCharCode(bytes[i]);
    }
    return window.btoa(binary);
}
function base64ToArrayBuffer(base64) {
    // ... (your existing console.logs and null/empty checks) ...

    try {
        const binary_string = window.atob(base64);
        const len = binary_string.length;
        const bytes = new Uint8Array(len); // This is your Uint8Array instance

        for (let i = 0; i < len; i++) {
            bytes[i] = binary_string.charCodeAt(i);
        }

        // --- THIS IS THE CRITICAL CHANGE ---
        return bytes; // <--- Return the Uint8Array instance directly
        // --- NOT ---
        // return bytes.buffer; // This returns the underlying ArrayBuffer
        // --- END CRITICAL CHANGE ---

    } catch (e) {
        console.error("[base64ToArrayBuffer] ERROR: Exception during decoding or buffer creation:", e);
        return null; // Or return new Uint8Array(0); as before
    }
}


async function generateAndUploadE2EKeys(userId, username){
    await sodium.ready;

    const storedKeys = localStorage.getItem(`libsodium_e2e_keys_${userId}`);
    let keyPair;
    // Checks whether there are any keys stored locally, if so it will create the keypair.
    if (storedKeys){
        console.log("E2E Keys already exist locally for user:", username);

        keyPair = JSON.parse(storedKeys);
        keyPair.publicKey = base64ToArrayBuffer(keyPair.publicKey);
        keyPair.privateKey = base64ToArrayBuffer(keyPair.privateKey);
    } else {
        console.log("Generating a new sodium E2E key pair for user:", username);
        keyPair = sodium.crypto_box_keypair();
        console.log("Key pair generated.")

        localStorage.setItem(`libsodium_e2e_keys_${userId}`, JSON.stringify({
            publicKey: arrayBufferToBase64(keyPair.publicKey),
            privateKey: arrayBufferToBase64(keyPair.privateKey)
        }));
        console.log('Private E2E key stored locally for prototype')

        const response = await fetch ('/api/e2e_keys/upload',{
            method:'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                public_e2e_key: arrayBufferToBase64(keyPair.publicKey)
            })
        });

        if (response.ok) {
            console.log("Public E2E key uploaded successfully.");
        } else {
            const error = await response.json();
            console.error("Failed to upload public E2E key:", error)
            alert("Failed to upload public E2E key: "+ error.error)
        }
    }
}



document.addEventListener('DOMContentLoaded', async function() {
    const searchInput = document.getElementById('search-user');
    const searchButton = document.getElementById('search-button');
    const searchResultsList = document.getElementById('search-results');
    const userList = document.getElementById('user-list');

    await generateAndUploadE2EKeys( currentUserId , currentUsername);



    searchButton.addEventListener('click', function() {
        const query = searchInput.value.trim();
        if (query) {
            fetch(`/search_users?q=${query}`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                },
            })
                .then(response => response.json())
                .then(data => {
                    searchResultsList.innerHTML = '';
                    if (data && data.results && Array.isArray(data.results) && data.results.length > 0) {
                        data.results.forEach(user => {
                            const listItem = document.createElement('li');
                            listItem.classList.add('search-result-item');
                            listItem.innerHTML = `
                    <span>${user.username}</span>
                    <button class="start-chat-button" data-username="${user.username}">Start Chat</button>
                `;
                            searchResultsList.appendChild(listItem);

                            // Get the newly created button
                            const startChatButton = listItem.querySelector('.start-chat-button');
                            // Attach the event listener to this specific button
                            startChatButton.addEventListener('click', function() {
                                const recipientUsername = this.dataset.username;
                                startNewChat(recipientUsername);
                            });
                        });
                    } else {
                        const listItem = document.createElement('li');
                        listItem.classList.add('no-results');
                        listItem.textContent = 'No users found.';
                        searchResultsList.appendChild(listItem);
                    }
                })
                .catch(error => {
                    console.error('Error searching users:', error);
                    alert('Failed to search for users.');
                });
        } else {
            searchResultsList.innerHTML = '';
        }
    });

    const startChatButtonsInitial = document.querySelectorAll('.start-chat-button[data-username]'); // Select initial buttons

    startChatButtonsInitial.forEach(button => {
        button.addEventListener('click', function() {
            const recipientUsername = this.dataset.username;
            startNewChat(recipientUsername);
        });
    });

    async function getE2EPublicKey(userID){
        const response = await fetch(`/api/e2e_keys/${userID}`);
        if (response.ok) {
            const data = await response.json()
            return data.public_e2e_key;
        } else {
            const error = await response.json();
            console.error("Failed to fetch public E2E key for", userID, ":",error);
            alert(`Failed to get public key for ${userID}: ${error.error || response.statusText}`);
            return null;
        }
    }

    function startNewChat(recipientUsername) {
        fetch('/new_chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ recipient_username: recipientUsername }),
        })
            .then(response => response.json())
            .then(data => {
                if (data.redirect_url) {
                    window.location.href = data.redirect_url;
                } else if (data.error) {
                    alert(`Error starting chat: ${data.error}`);
                } else {
                    console.warn('Unexpected response:', data);
                    alert('Failed to start chat.');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Failed to connect to the server.');
            });
    }
});