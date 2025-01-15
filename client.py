import socket
import random
from threading import Thread
from datetime import datetime
from colorama import Fore, init, Back

# init colours

init()

# set the available colours

colours = [Fore.BLUE, Fore.CYAN, Fore.GREEN, Fore.LIGHTBLACK_EX, Fore.LIGHTBLUE_EX,
           Fore.LIGHTCYAN_EX, Fore.LIGHTGREEN_EX, Fore.LIGHTMAGENTA_EX,
           Fore.LIGHTRED_EX, Fore.LIGHTWHITE_EX, Fore.LIGHTYELLOW_EX, Fore.MAGENTA,
           Fore.RED, Fore.WHITE, Fore.YELLOW]

# choose a random colour for the client

client_color = random.choice(colours)

# Server's IP address

SERVER_HOST = "127.0.0.1"
SERVER_PORT = 5002

separator_token = "<SEP>"

# Initialize TCP socket
s = socket.socket()
print(f"[*] Connecting to {SERVER_HOST}:{SERVER_PORT}...")
# connect to server
s.connect((SERVER_HOST, SERVER_PORT))
print("[*] Connected.")

# prompt client name
name = input("Enter your name: ")
recipient = input("Enter your recipient: ")

def listen_for_message():
    while True:
        message = s.recv(1024).decode()
        print("\n" + message)


# Make a thread that listens for messages to this client & print them
t = Thread(target=listen_for_message)
# Make the thread a daemon thread, so it ends whenever the main thread ends
t.daemon = True
# Start thread
t.start()

while True:
    # input messages to send to the server
    to_send = input()
    # a way to exit the program
    if to_send.lower() == "q":
        break
    # Add the datetime, name & colour of the sender
    date_now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    to_send = f"{client_color}[{date_now}] {name}{separator_token}{to_send}{Fore.RESET}"
    # send the message
    s.send(to_send.encode())

s.close()
