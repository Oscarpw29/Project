import socket
from threading import Thread

# server's IP address

SERVER_HOST = '0.0.0.0'
SERVER_PORT = 5002  # port
seperator_token = ("<SEP>")

# initialize list/set of sockets of all connected client's sockets

client_sockets = set()
# create a tcp socket
s = socket.socket()
# make the port as resuable port
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
# bind the socket to the address specified previously
s.bind((SERVER_HOST, SERVER_PORT))
# listen for upcomming connections
s.listen(5)
print(f"[*] Listening on {SERVER_HOST}:{SERVER_PORT}")


def listen_for_client(cs):
    """
    Function keeps listening for a message from the client
    Whenever a message is received it will broadcast to all other clients
    """
    while True:
        try:
            # keep listening for a message from the socket
            msg = cs.recv(1024).decode()
        except Exception as e:
            # client no longer connected
            # remove it from the set
            print(f"[!] Error {e}")
            client_sockets.remove(cs)
        else:
            # if a message was received, replace the seperator token with : for nice printing
            msg = msg.replace(seperator_token, ":")
        # iterate over all connected sockets
        for client_socket in client_sockets:
            client_socket.send(msg.encode())
while True:
    # keep listening for new connections
    client_socket, client_address = s.accept()
    print(f"[*] Accepted connection from {client_address}")
    # add the new connected client to connected sockets
    client_sockets.add(client_socket)
    # start a new thread that listens for each client's message
    t = Thread(target=listen_for_client, args=(client_socket,))
    # make the thread daemon, so it ends whenever the main thread ends
    t.daemon = True
    # Start the thread
    t.start()

# close client sockets

for cs in client_sockets:
    cs.close()
# close server socket
s.close()
