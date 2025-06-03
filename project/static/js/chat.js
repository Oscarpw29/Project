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
// project/static/js/chat.js (and home.js if separate)
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

async function getRecipientE2EPublicKey(recipientId){
    const response = await fetch(`/api/e2e_keys/${recipientId}`)
    if (response.ok) {
        const data = await response.json();
        if (data.public_key) {
            return base64ToArrayBuffer(data.public_key)
        }
    }
    return null;
}


async function encryptMessageE2E(plaintext, sharedSecretBuffer){
    await sodium.ready;
    // Nonce is a random value for each message,

    // Checks whether the Nonce exists, and if it does not it will generate one
    let nonceLength = sodium.crypto_secretbox_NONCEBYTES;
    if (typeof nonceLength === 'undefined' || nonceLength === null) {
        console.warn("WARNING: sodium.crypto_secretbox_NONCEBYTES is undefined or null. Using hardcoded 24 bytes.");
        nonceLength = 24; // Fallback to the standard constant (24 bytes)
    }

    const nonce = sodium.randombytes_buf(nonceLength);

    // The message will be encrypted on the client-side before it is even sent to the server.
    const encrypted = sodium.crypto_secretbox_easy(
        sodium.from_string(plaintext),
        nonce,
        sharedSecretBuffer
    );

    return{
        ciphertext: arrayBufferToBase64(encrypted),
        nonce: arrayBufferToBase64(nonce)
    };
}

async function getClientE2EPrivateKey(userId){
    const storedKeys = localStorage.getItem(`libsodium_e2e_keys_${userId}`)
    if (storedKeys){
        const keys = JSON.parse(storedKeys)
        return base64ToArrayBuffer(keys.privateKey)
    }
    return null;
}

// project/static/js/chat.js (within decryptMessageE2E function)

async function decryptMessageE2E(ciphertextBuffer, nonceBuffer, sharedSecretBuffer) {
    await sodium.ready;
    console.log("--- ATTEMPTING DECRYPTMESSAGEE2E ---"); // NEW LOG
    console.log("Ciphertext Buffer:", ciphertextBuffer, "Length:", ciphertextBuffer ? ciphertextBuffer.byteLength : null); // NEW LOG
    console.log("Nonce Buffer:", nonceBuffer, "Length:", nonceBuffer ? nonceBuffer.byteLength : null); // NEW LOG
    console.log("Shared Secret Buffer (last 5 bytes):", sharedSecretBuffer ? sharedSecretBuffer.slice(-5) : null, "Length:", sharedSecretBuffer ? sharedSecretBuffer.byteLength : null); // NEW LOG
    console.log("Expected Nonce Length:", sodium.crypto_secretbox_NONCEBYTES); // NEW LOG
    console.log("Expected Ciphertext Min Length (MACBYTES):", sodium.crypto_secretbox_MACBYTES); // NEW LOG

    // --- NEW/CHANGED: Explicit Type and Length Checks BEFORE calling libsodium ---
    if (!(ciphertextBuffer instanceof Uint8Array) || ciphertextBuffer.byteLength < sodium.crypto_secretbox_MACBYTES) {
        console.error("DECRYPT_E2E_ERROR: Invalid ciphertextBuffer type or length.", ciphertextBuffer);
        return "[Decryption Failed: Invalid Ciphertext]"; // Return error message
    }
    if (!(nonceBuffer instanceof Uint8Array) || nonceBuffer.byteLength !== sodium.crypto_secretbox_NONCEBYTES) {
        console.error("DECRYPT_E2E_ERROR: Invalid nonceBuffer type or length.", nonceBuffer);
        return "[Decryption Failed: Invalid Nonce]"; // Return error message
    }
    if (!(sharedSecretBuffer instanceof Uint8Array) || sharedSecretBuffer.byteLength !== sodium.crypto_box_BEFORENMBYTES) {
        console.error("DECRYPT_E2E_ERROR: Invalid sharedSecretBuffer type or length.", sharedSecretBuffer);
        return "[Decryption Failed: Invalid Shared Secret]"; // Return error message
    }
    // --- END NEW/CHANGED ---


    try {
        const decrypted = sodium.crypto_secretbox_open_easy(
            ciphertextBuffer,
            nonceBuffer,
            sharedSecretBuffer
        );
        console.log("Decryption successful (inside decryptMessageE2E)!");
        return sodium.to_string(decrypted);
    } catch (e) {
        // --- CRITICAL: Log the exact error thrown by crypto_secretbox_open_easy ---
        console.error("DECRYPT_E2E_ERROR: crypto_secretbox_open_easy threw an exception:", e);
        return "[Decryption Failed: " + e.message + "]"; // Return error message with details
    }
}

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


const e2eSessions = {};


// End to End Session management

const chatSharedSecrets = new Map();

// project/static/js/chat.js (within establishE2ESession function)

async function establishE2ESession(chatId, recipientUserId) {
    await sodium.ready;
    console.log(`[establishE2ESession] START - chat ID: ${chatId}, recipient ID: ${recipientUserId}`); // NEW CRITICAL LOG
    console.log(`[establishE2ESession] Type of chatId: ${typeof chatId}, Type of recipientUserId: ${typeof recipientUserId}`); // NEW LOG


    // 1. Check if session already established for this chat
    console.log(`[establishE2ESession] Checking if session already in map for chat ${chatId}. Map size: ${chatSharedSecrets.size}`); // NEW LOG

    if (chatSharedSecrets.has(chatId)) {
        const existingSecret = chatSharedSecrets.get(chatId);
        console.log(`[establishE2ESession] Session already established for chat ${chatId} (retrieved from map). Length: ${existingSecret.byteLength}`);
        return existingSecret; // Return existing shared secret
    }
    console.log(`[establishE2ESession] Session NOT in map. Proceeding with key derivation.`); // NEW LOG

    console.log("[establishE2ESession] Attempting to get sender's private key from localStorage."); // NEW LOG

    // 2. Get sender's private key (from localStorage)
    const senderKeysString = localStorage.getItem(`libsodium_e2e_keys_${currentUserId}`);
    if (!senderKeysString) {
        console.error("ERROR: [establishE2ESession] Sender's private E2E key not found locally. Cannot establish session.");
        alert("Your private E2E key is missing. Please log in again or re-generate keys.");
        return null;
    }
    const senderKeys = JSON.parse(senderKeysString);
    console.log("[establishE2ESession] Sender's private key loaded from localStorage (parsed)."); // NEW LOG

    const senderPrivateKey = base64ToArrayBuffer(senderKeys.privateKey);
    console.log("[establishE2ESession] Sender Private Key Loaded (Base64):", arrayBufferToBase64(senderPrivateKey)); // NEW LOG
    console.log("Sender Private Key Length:", senderPrivateKey.byteLength);

    if (senderPrivateKey.byteLength !== sodium.crypto_box_SECRETKEYBYTES) {
        console.error(`ERROR: [establishE2ESession] Invalid sender private key length: ${senderPrivateKey.byteLength}. Expected ${sodium.crypto_box_SECRETKEYBYTES}.`);
        alert("Invalid sender private key. Session cannot be established.");
        return null;
    }

    // 3. Get recipient's public key (from server)
    console.log(`[establishE2ESession] Fetching public key for recipient: ${recipientUserId}`);
    const recipientPublicKeyBase64 = await getE2EPublicKey(recipientUserId);
    if (!recipientPublicKeyBase64) {
        console.error("ERROR: [establishE2ESession] Recipient's public E2E key not found or fetch failed. Cannot establish session.");
        alert("Recipient's public E2E key is missing. Please ensure they have logged in and generated keys.");
        return null;
    }
    const recipientPublicKeyBuffer = base64ToArrayBuffer(recipientPublicKeyBase64);
    console.log("Recipient Public Key Loaded (Base64):", arrayBufferToBase64(recipientPublicKeyBuffer)); // NEW LOG
    console.log("Recipient Public Key Length:", recipientPublicKeyBuffer.byteLength);

    if (recipientPublicKeyBuffer.byteLength !== sodium.crypto_box_PUBLICKEYBYTES) {
        console.error(`ERROR: [establishE2ESession] Invalid recipient public key length: ${recipientPublicKeyBuffer.byteLength}. Expected ${sodium.crypto_box_PUBLICKEYBYTES}.`);
        alert("Invalid recipient public key received. Session cannot be established.");
        return null;
    }

    // 4. Derive shared secret key
    const sharedSecret = sodium.crypto_box_beforenm(recipientPublicKeyBuffer, senderPrivateKey);

    console.log(`[establishE2ESession] DERIVED Shared Secret for chat ${chatId} (Base64): ${arrayBufferToBase64(sharedSecret)}`); // NEW LOG
    console.log(`[establishE2ESession] Derived Shared Secret Length: ${sharedSecret.byteLength}`); // NEW LOG

    chatSharedSecrets.set(chatId, sharedSecret);
    console.log(`[establishE2ESession] Shared secret STORED in map for chat ${chatId}.`); // NEW LOG
    console.log(`[establishE2ESession] Map size after store: ${chatSharedSecrets.size}`); // NEW LOG

    return sharedSecret; // This should be the successful return
}


// End of E2E session management

function scrollToBottom(){
    const messagesContainer = document.getElementById('messages');
    if (messagesContainer) {
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
}


document.addEventListener('DOMContentLoaded', async function(){
    await sodium.ready;
    console.log('--- DOMContentLoaded! ---')
    let sharedSecretBufferForPage = null;

    const messagesContainer = document.getElementById('messages');
    const sendMessageForm = document.getElementById('send-message-form');
    const messageInput = document.getElementById('message-input');

    const socket = io.connect('http://127.0.0.1:5002');


    if (currentChatType === 'secret'){
        console.log('DEBUG: currentChatType is "secret". Attempting establishE2ESession')
        const sessionEstablishedResult = await establishE2ESession(chatId, recipientId)

        sharedSecretBufferForPage = sessionEstablishedResult

        if (!sharedSecretBufferForPage) {
            console.error('Critical Error: E2E Session not established on page load')
        } else {
            console.log('DEBUG: EE2ES complete')
        }
    } else {
        console.log('DEBUG: Chat is not secret')
    }


    socket.on('connect', function () {
        console.log('Websocket connected! (client side)');
        socket.emit('join', {room: `chat_${chatId}`});
        console.log(`Client emitted 'join' for room: chat_${chatId}`);
    });

    socket.on('message', async function (data) { // Ensure this is async!
        console.log('--- REAL-TIME: Client received WebSocket message ---');
        console.log('REAL-TIME: Raw data received by client:', data); // CRITICAL: See the full payload
        let sharedSecretBuffer = chatSharedSecrets.get(data.chat_id);

        // Check if the message is for the currently active chat
        console.log('REAL-TIME: Chat ID from data:', data.chat_id, 'Current Chat ID:', chatId, 'Match:', data.chat_id === parseInt(chatId));
        console.log('REAL-TIME: Chat Type from data:', data.chat_type, 'Expected Type:', currentChatType);

        if (data.chat_id === parseInt(chatId)) {
            let displayContent = data.message; // Holds the raw message from server (plaintext or object)
            if (data.chat_type === 'secret') {
                console.log('DEBUG: currentChatType is "secret". Attempting establishE2ESession.');
                console.log('REAL-TIME: **Current chatSharedSecrets map contents (before get):**', chatSharedSecrets);
                console.log('REAL-TIME: **Key being looked up in map:**', data.chat_id);
                sharedSecretBuffer = sharedSecretBufferForPage

                if (!sharedSecretBuffer) {
                console.error("CRITICAL ERROR: E2E Session NOT established on page load. Decryption/Encryption will fail.");
                alert("Secret Chat initialization failed. Messages may not decrypt. Please refresh.");
            }

                console.log('Debug: Shared Secret Buffer found:', !!sharedSecretBuffer);


                // Check if data.message is the object {ciphertext: ..., nonce: ...}
                // It should be if server emits Python dict directly.

                let incomingMessageObject = data.message

                if (typeof data.message ==='string'){
                    try{
                        incomingMessageObject = JSON.parse(data.message)
                        console.log("REAL-TIME: Succesffuly parsed message")
                    } catch (e){
                        console.error("REAL-TIME: Malformed message");
                        displayContent = "[Malformed Encrypted Message]";
                        return;
                    }
                } else {
                    incomingMessageObject = data.message
                }

                console.log('REAL-TIME: Inspecting incomingMessageObject. Keys:', Object.keys(incomingMessageObject)); // NEW LOG
                console.log('REAL-TIME: incomingMessageObject.ciphertext value:', incomingMessageObject.ciphertext); // NEW LOG
                console.log('REAL-TIME: incomingMessageObject.nonce value:', incomingMessageObject.nonce); // NEW LOG


                const incomingCiphertext = incomingMessageObject.ciphertext;
                const incomingNonce = incomingMessageObject.nonce;


                if (sharedSecretBuffer && incomingCiphertext && incomingNonce) {
                    try {
                        const ciphertextBuffer = base64ToArrayBuffer(incomingCiphertext);
                        const nonceBuffer = base64ToArrayBuffer(incomingNonce);
                        console.log('REAL-TIME: Ciphertext Buffer:', ciphertextBuffer, 'Length:', ciphertextBuffer ? ciphertextBuffer.byteLength : null);
                        console.log('REAL-TIME: Nonce Buffer:', nonceBuffer, 'Length:', nonceBuffer ? nonceBuffer.byteLength : null);
                        console.log('REAL-TIME: Shared Secret Buffer:', sharedSecretBuffer, 'Length:', sharedSecretBuffer ? sharedSecretBuffer.byteLength : null);


                        console.log('REAL-TIME: Calling decryptMessageE2E with:', incomingCiphertext, incomingNonce, sharedSecretBuffer);
                        const decrypted = await decryptMessageE2E(
                            base64ToArrayBuffer(incomingCiphertext),
                            base64ToArrayBuffer(incomingNonce),
                            sharedSecretBufferForPage
                        );
                        displayContent = decrypted;
                        console.log('REAL-TIME: Decryption SUCCESS! Decrypted content:', displayContent);
                    } catch (e) {
                        displayContent = "[Real-time Decryption Failed]";
                        console.error("ERROR: decryptMessageE2E threw an exception during real-time receive:", e); // CRITICAL: This is the exact error
                    }
                } else {
                    displayContent = "[Real-time Decryption Failed / Keys Missing]";
                    console.error("REAL-TIME ERROR: Missing Shared secret, ciphertext, or nonce. Data:", data);
                }
            } else {
                console.log('REAL-TIME: Standard chat message. Displaying as plaintext.');
            }

            // --- DOM Manipulation for message display ---
            const messageContainer = document.createElement('div');
            messageContainer.classList.add('message-container');
            if (data.sender === currentUsername) {
                messageContainer.classList.add('sent');
            } else {
                messageContainer.classList.add('received');
            }
            const messageBubble = document.createElement('div');
            messageBubble.classList.add('message-bubble');
            const messageParagraph = document.createElement('p');
            messageParagraph.textContent = displayContent; // <<< CRITICAL FIX: Use displayContent here
            const timestampSmall = document.createElement('small');
            timestampSmall.classList.add('message-timestamp');
            const now = new Date();
            const formattedTime = `${now.toLocaleDateString()} ${now.toLocaleTimeString()}`;
            timestampSmall.textContent = formattedTime;

            messageBubble.appendChild(messageParagraph);
            messageBubble.appendChild(timestampSmall);
            messageContainer.appendChild(messageBubble);
            messagesContainer.appendChild(messageContainer);
            scrollToBottom();
            console.log('REAL-TIME: Message element appended and scrolled.');
        } else {
            console.log('REAL-TIME: Message received for a different chat ID. Ignoring. Expected:', chatId, 'Received:', data.chat_id);
        }
    });


// Initial Decryption of Messages Rendered by Jinja (for page load history)
    if (currentChatType === 'secret') { // This condition ensures it only runs for secret chats
        console.log("INITIAL HISTORY: Starting decryption loop for secret chat history...");

        const sharedSecretBuffer = await establishE2ESession(chatId, recipientId); // Ensure this is awaited

        if (!sharedSecretBuffer) { // Check if session establishment failed
            console.error("INITIAL HISTORY: Shared secret not established. Messages will remain encrypted.");
        } else {
            const messageElements = messagesContainer.querySelectorAll('.message-container p');
            for (let i = 0; i < messageElements.length; i++) {
                const pElement = messageElements[i];
                const rawContent = pElement.textContent.trim();

                console.log(`INITIAL HISTORY: Processing message: Raw content "${rawContent}"`);

                try {
                    const parsedContent = JSON.parse(rawContent);
                    console.log(`INITIAL HISTORY: Parsed content:`, parsedContent);

                    if (parsedContent && typeof parsedContent === 'object' && parsedContent.ciphertext && parsedContent.nonce) {
                        console.log("INITIAL HISTORY: Ciphertext and Nonce found. Attempting decryption.");
                        let decrypted = await decryptMessageE2E(
                            base64ToArrayBuffer(parsedContent.ciphertext),
                            base64ToArrayBuffer(parsedContent.nonce),
                            sharedSecretBuffer
                        );
                        pElement.textContent = decrypted;
                        console.log(`INITIAL HISTORY: Decryption SUCCESS! Decrypted content: ${decrypted}`);
                    } else {
                        console.warn("INITIAL HISTORY: Parsed content is not an object or missing ciphertext/nonce:", parsedContent);
                        pElement.textContent = "[Malformed Encrypted Message]";
                    }
                } catch (e) {
                    console.error("INITIAL HISTORY ERROR: JSON.parse failed or decryption exception:", e, "Raw content:", rawContent);
                    pElement.textContent = "[Decryption Failed (Invalid Format)]";
                }
            }
        }
    }
    sendMessageForm.addEventListener('submit', async function(event){
        event.preventDefault();
        const message = messageInput.value.trim();

        if (message && chatId){
            let messageToSend = message;

            if (currentChatType === 'secret') {
                console.log('--- SEND MESSAGE E2E ENCRYPTION ATTEMPT ---'); // NEW LOG
                console.log('SEND: Current chat ID:', chatId); // NEW LOG
                console.log('SEND: Value of chatSharedSecrets map:', chatSharedSecrets); // NEW LOG: Check the map itself

                const sharedSecretBuffer = chatSharedSecrets.get(chatId);
                if (!sharedSecretBuffer) {
                    console.log('E2E Session not established for secret chats')
                    alert("E2E Session not ready")
                    return;
                }

                const encrypted = await encryptMessageE2E(message, sharedSecretBuffer);

                messageToSend = {
                    ciphertext: encrypted.ciphertext,
                    nonce: encrypted.nonce
                };
                console.log("Encrypted Message Sent:", messageToSend);
            } else {
                console.log("Plaintext message sent", messageToSend);
            }

            socket.emit('message', {
                message: messageToSend,
                room: `chat_${chatId}`,
                chat_type: currentChatType,
                sender_id: currentUserId
            });

            messageInput.value = '';

            const messageContainer = document.createElement('div');
            messageContainer.classList.add('message-container', 'sent');
            const messageBubble = document.createElement('div')
            messageBubble.classList.add('message-bubble');
            const messageParagraph = document.createElement('p');
            messageParagraph.textContent = displayContent;

            const timestampSmall = document.createElement('small');
            timestampSmall.classList.add('message-timestamp');
            const now = new Date()
            const formattedTime = `${now.toLocaleDateString()} ${now.toLocaleTimeString()}`;
            timestampSmall.textContent = formattedTime
            scrollToBottom()
        } else if (!message) {
            console.warn('Attempted to send empty message')
        }
    })
scrollToBottom()

})