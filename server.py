import socket
import threading
import sys

# -- Server Settings --
HOST = '127.0.0.1'  # localhost
PORT = 5555

# Let's set up the server socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.bind((HOST, PORT))
sock.listen(2)  # we only need two clients for this simple game

print(f"[INFO] Server is live on {HOST}:{PORT}")
print("[INFO] Waiting for players to show up...")

# Global game state
game_board = [' ' for _ in range(9)]  # init empty board
active_symbol = 'X'
is_game_over = False
connected_clients = []
client_roles = {}  # Map socket to 'X' or 'O' (typical user notations in tic-tac-toe)

def draw_board():
    # Just prints the current board as a string grid
    display = "\n"
    for idx in range(0, 9, 3):
        display += f" {game_board[idx]} | {game_board[idx+1]} | {game_board[idx+2]} \n"
        if idx < 6:
            display += "---+---+---\n"
    return display

def check_game_status():
    # Check horizontal wins
    for row in range(0, 9, 3):
        if game_board[row] == game_board[row+1] == game_board[row+2] != ' ':
            return game_board[row]

    # Check verticals
    for col in range(3):
        if game_board[col] == game_board[col+3] == game_board[col+6] != ' ':
            return game_board[col]

    # Diagonals
    if game_board[0] == game_board[4] == game_board[8] != ' ':
        return game_board[0]
    if game_board[2] == game_board[4] == game_board[6] != ' ':
        return game_board[2]

    # If no empty spots, then it's a draw
    if ' ' not in game_board:
        return 'Tie'

    return None  # No winner yet

def send_to_all(msg, except_socket=None):
    # Quick broadcast to all clients, except the one specified
    for client in connected_clients:
        if client != except_socket:
            try:
                client.send(msg.encode())
            except:
                # Probably disconnected
                if client in connected_clients:
                    connected_clients.remove(client)

def client_thread(conn, addr):
    global active_symbol, is_game_over

    # Assign a symbol: first come first serve
    role = 'X' if len(client_roles) == 0 else 'O'
    client_roles[conn] = role

    conn.send(f"Hey there! You're playing as '{role}'".encode())

    if len(connected_clients) < 2:
        conn.send("Waiting for the other player... Sit tight.".encode())
        while len(connected_clients) < 2:
            pass  # kind of janky, but works

    # Game start message
    if role == 'X':
        conn.send(f"You're up first! Here's the board:{draw_board()}".encode())
    else:
        conn.send(f"Hang on, X is making the first move.{draw_board()}".encode())

    while not is_game_over:
        if client_roles.get(conn) == active_symbol:
            try:
                conn.send(f"Your move! (1-9):{draw_board()}".encode())
                move = conn.recv(1024).decode().strip()

                try:
                    pos = int(move) - 1
                except ValueError:
                    conn.send("Hmm, please enter a number between 1-9.".encode())
                    continue

                if pos < 0 or pos > 8 or game_board[pos] != ' ':
                    conn.send("That spot's already taken or invalid. Try again.".encode())
                    continue

                game_board[pos] = active_symbol

                result = check_game_status()
                if result:
                    is_game_over = True
                    final_msg = f"Game over! It's a draw!{draw_board()}" if result == 'Tie' else f"Boom! Player {result} wins!{draw_board()}"
                    send_to_all(final_msg)
                    break

                # Alternate turn
                active_symbol = 'O' if active_symbol == 'X' else 'X'
                send_to_all(f"{role} moved to position {pos + 1}.{draw_board()}")
                send_to_all(f"Player {active_symbol}'s turn.")
            except:
                print(f"[WARN] Lost connection with {role}")
                if conn in connected_clients:
                    connected_clients.remove(conn)
                is_game_over = True
                send_to_all("Looks like the other player disconnected. Ending game.")
                break
        else:
            # Not your turn, do nothing
            continue

# Main server loop
try:
    while len(connected_clients) < 2:
        conn, addr = sock.accept()
        connected_clients.append(conn)
        print(f"[JOIN] Player from {addr} has connected.")
        threading.Thread(target=client_thread, args=(conn, addr)).start()

    while not is_game_over:
        pass  # hold the main thread until game is finished

    print("[INFO] Game wrapped up. Shutting down.")
except KeyboardInterrupt:
    print("\n[EXIT] Manual shutdown triggered.")
finally:
    for client in connected_clients:
        client.close()
    sock.close()
