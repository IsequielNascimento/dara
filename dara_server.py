"""
dara_server.py — Servidor do Jogo Dara (dois sockets TCP por jogador)

Porta 9090 — socket de JOGO   responsável por: movimentos, turno, captura, desistência
Porta 9091 — socket de CHAT   responsável pro: mensagens de texto

Cada porta abre um ServerSocket independente.
Cada cliente conecta nos dois sockets; o servidor cruza as conexões pelo
nome do jogador recebido no handshake inicial.

Threads:
  - listen_game(idx)  — escuta e processa mensagens de jogo do jogador idx
  - listen_chat(idx)  — repassa mensagens de chat ao oponente
"""

import socket
import threading

from constants import PORT_GAME, PORT_CHAT, TOTAL_PIECES

#  Estado compartilhado 
player_names: list[str | None]          = [None, None]
game_socks:   list[socket.socket | None] = [None, None]
chat_socks:   list[socket.socket | None] = [None, None]

current_turn: int   = 0
game_phase:   str   = "PLACEMENT"
pieces_total: list[int] = [TOTAL_PIECES, TOTAL_PIECES]   # peças no tabuleiro

game_lock = threading.Lock()   # protege envios simultâneos no socket de jogo
chat_lock = threading.Lock()   # protege envios simultâneos no socket de chat


#  Envio thread-safe 

def send_game(idx: int, msg: str):
    with game_lock:
        _send_raw(game_socks[idx], msg)

def send_chat_to(idx: int, msg: str):
    with chat_lock:
        _send_raw(chat_socks[idx], msg)

def broadcast_game(msg: str):
    with game_lock:
        for i in range(2):
            _send_raw(game_socks[i], msg)

def _send_raw(sock: socket.socket, msg: str):
    try:
        sock.sendall((msg + "\n").encode("utf-8"))
    except Exception as e:
        print(f"[Srv] Erro ao enviar: {e}")


#  Handshake inicial 

def recv_line(conn: socket.socket) -> str:
    buf = b""
    while True:
        c = conn.recv(1)
        if not c or c == b"\n":
            break
        buf += c
    return buf.decode("utf-8").strip()


#  Thread de jogo 

def listen_game(idx: int):
    global current_turn, game_phase, pieces_total

    opp = 1 - idx
    buf = ""
    try:
        while True:
            chunk = game_socks[idx].recv(4096).decode("utf-8")
            if not chunk:
                break
            buf += chunk
            while "\n" in buf:
                line, buf = buf.split("\n", 1)
                msg = line.strip()
                if not msg:
                    continue

                print(f"[JOGO P{idx}->Srv] {msg}")

                if msg.startswith("MOVE:"):
                    send_game(opp, msg)

                elif msg.startswith("LINE3:"):
                    send_game(opp, msg)

                elif msg.startswith("CAPTURED:"):
                    send_game(opp, msg)
                    pieces_total[opp] -= 1
                    print(f"[Srv] Peças de {player_names[opp]}: {pieces_total[opp]}")
                    if pieces_total[opp] <= 2:
                        broadcast_game(f"WINNER:{idx}:{player_names[idx]}")
                        print(f"[Srv] Vencedor: {player_names[idx]}")
                    else:
                        _next_turn()

                elif msg == "TURN_DONE":
                    _next_turn()

                elif msg == "PHASE_MOVEMENT":
                    game_phase = "MOVEMENT"
                    broadcast_game("PHASE:MOVEMENT")
                    print("[Srv] Fase de Movimentação iniciada!")

                elif msg == "RESIGN":
                    broadcast_game(f"RESIGN:{player_names[idx]}")
                    broadcast_game(f"WINNER:{opp}:{player_names[opp]}")
                    print(f"[Srv] {player_names[idx]} desistiu.")
                    return

    except Exception as e:
        print(f"[Srv] Jogador {idx} ({player_names[idx]}) desconectou: {e}")
    finally:
        try:
            send_game(opp, f"DISCONNECT:{player_names[idx]}")
        except Exception:
            pass


def _next_turn():
    global current_turn
    current_turn = 1 - current_turn
    broadcast_game(f"TURN:{current_turn}")
    print(f"[Srv] Turno: {player_names[current_turn]}")


#  Thread de chat 

def listen_chat(idx: int):
    """Repassa qualquer mensagem do socket de chat ao oponente."""
    opp = 1 - idx
    buf = ""
    try:
        while True:
            chunk = chat_socks[idx].recv(4096).decode("utf-8")
            if not chunk:
                break
            buf += chunk
            while "\n" in buf:
                line, buf = buf.split("\n", 1)
                text = line.strip()
                if text:
                    print(f"[CHAT P{idx}->Srv] {text}")
                    # Encaminha ao oponente com prefixo de remetente
                    send_chat_to(opp, f"{player_names[idx]}: {text}")
    except Exception as e:
        print(f"[Srv] Chat {idx} encerrado: {e}")


#  Inicialização dos servidores 

def accept_players(game_server: socket.socket, chat_server: socket.socket):
    """
    Aceita os dois jogadores em ambas as portas.
    Estratégia: aceita as 4 conexões (2 jogo + 2 chat) e cruza pelo nome.
    """
    print("Aguardando 2 jogadores...\n")

    # Aceita 2 conexões de jogo (em ordem)
    for i in range(2):
        conn, addr = game_server.accept()
        game_socks[i] = conn
        player_names[i] = recv_line(conn)
        print(f"[Jogo ] Jogador {i+1}: {player_names[i]}  [{addr[0]}:{addr[1]}]")
        send_game(i, f"ASSIGN:{i}")

    # Aceita 2 conexões de chat — cruza pelo nome recebido no handshake
    pending_chat: dict[str, socket.socket] = {}
    for _ in range(2):
        conn, addr = chat_server.accept()
        name = recv_line(conn)
        pending_chat[name] = conn
        print(f"[Chat ] Conectado: {name}  [{addr[0]}:{addr[1]}]")

    for i in range(2):
        chat_socks[i] = pending_chat[player_names[i]]


#  Main 

def main():
    print("=" * 50)
    print(f"  Servidor DARA")
    print(f"  Jogo -> porta {PORT_GAME}   Chat -> porta {PORT_CHAT}")
    print("=" * 50)

    # Dois ServerSockets independentes
    game_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    chat_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    for srv, port in [(game_server, PORT_GAME), (chat_server, PORT_CHAT)]:
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind(("0.0.0.0", port))
        srv.listen(2)

    accept_players(game_server, chat_server)

    # Notifica início
    broadcast_game(f"NAMES:{player_names[0]}:{player_names[1]}")
    broadcast_game("START:0")
    print(f"\n[Srv] Jogo iniciado! {player_names[0]} começa.\n")

    # Inicia 4 threads (2 jogo + 2 chat)
    threads = []
    for i in range(2):
        threads.append(threading.Thread(
            target=listen_game, args=(i,), daemon=True, name=f"Game-{i}"))
        threads.append(threading.Thread(
            target=listen_chat, args=(i,), daemon=True, name=f"Chat-{i}"))

    for t in threads:
        t.start()

    for t in threads:
        t.join()

    print("\n[Srv] Partida encerrada.")
    game_server.close()
    chat_server.close()


if __name__ == "__main__":
    main()
