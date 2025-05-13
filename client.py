import socket
import threading
import sys

# -- Config --
HOST = '127.0.0.1'
PORT = 5555

# Set up our client socket
my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Flag to let both threads know when to stop
game_done = False

def listen_to_server():
    global game_done
    while True:
        try:
            msg = my_socket.recv(1024).decode()
            if not msg:
                break
            print(msg)

            if "Your turn" in msg:
                print("Enter a number between 1 and 9: ", end="")

            if "Game over" in msg or "disconnected" in msg.lower():
                game_done = True
                print("Press Enter to quit...")
                break
        except:
            print("Oops, lost connection to the server.")
            game_done = True
            break

try:
    my_socket.connect((HOST, PORT))
    print(f"[CONNECTED] to server at {HOST}:{PORT}")

    # Start listening in a separate thread
    threading.Thread(target=listen_to_server, daemon=True).start()

    # Input loop
    while not game_done:
        move = input()
        if game_done:
            break  # Just in case the game ends while waiting for input
        if move.strip() == "":
            continue  # ignore blank inputs
        try:
            my_socket.send(move.encode())
        except:
            print("Couldn't send your move. Maybe server's down?")
            break
except ConnectionRefusedError:
    print("⚠️ Couldn't reach server. Is it running?")
except KeyboardInterrupt:
    print("\n[EXIT] Client shutting down.")
finally:
    my_socket.close()
