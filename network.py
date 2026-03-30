"""
network.py — Camada de rede do cliente Dara
Responsável por: dois sockets TCP independentes (jogo e chat),
threads de leitura e envio de mensagens.

  Socket de jogo  → PORT_GAME (9090)  — movimentos, turnos, captura, desistência
  Socket de chat  → PORT_CHAT (9091)  — mensagens de texto entre jogadores
"""

import socket
import threading
from typing import Callable

from constants import PORT_GAME, PORT_CHAT


class NetworkManager:
    """
    Gerencia duas conexões TCP simultâneas com o servidor:
      - game_sock  (porta 9090): protocolo de jogo
      - chat_sock  (porta 9091): protocolo de chat

    Cada socket possui uma Thread daemon dedicada para leitura assíncrona.
    As mensagens recebidas são despachadas via callbacks registrados pelo cliente.
    """

    def __init__(self):
        self.game_sock: socket.socket | None = None
        self.chat_sock: socket.socket | None = None

        # Callbacks injetados pela UI
        self._on_game_msg: Callable[[str], None] | None = None
        self._on_chat_msg: Callable[[str, str], None] | None = None
        self._on_disconnect: Callable[[str], None] | None = None

    # Registro de callbacks 

    def on_game_message(self, callback: Callable[[str], None]):
        """Registra função chamada ao receber mensagem do socket de jogo."""
        self._on_game_msg = callback

    def on_chat_message(self, callback: Callable[[str, str], None]):
        """Registra função chamada ao receber mensagem de chat: (remetente, texto)."""
        self._on_chat_msg = callback

    def on_disconnect(self, callback: Callable[[str], None]):
        """Registra função chamada em caso de desconexão."""
        self._on_disconnect = callback

    # Conexão 

    def connect(self, host: str, player_name: str) -> str | None:
        """
        Abre os dois sockets e envia o nome do jogador em cada um.
        Retorna None em caso de sucesso ou a mensagem de erro.
        """
        try:
            # Socket de jogo
            self.game_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.game_sock.connect((host, PORT_GAME))
            self._send_raw(self.game_sock, player_name)

            # Socket de chat (conecta logo em seguida)
            self.chat_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.chat_sock.connect((host, PORT_CHAT))
            self._send_raw(self.chat_sock, player_name)

            # Threads de leitura (daemon → encerram com o processo)
            threading.Thread(
                target=self._read_loop,
                args=(self.game_sock, self._dispatch_game),
                daemon=True, name="GameReader"
            ).start()

            threading.Thread(
                target=self._read_loop,
                args=(self.chat_sock, self._dispatch_chat),
                daemon=True, name="ChatReader"
            ).start()

            return None   # sucesso

        except Exception as e:
            return str(e)

    def disconnect(self):
        """Fecha ambos os sockets."""
        for s in (self.game_sock, self.chat_sock):
            try:
                if s:
                    s.close()
            except Exception:
                pass

    # Envio 

    def send_game(self, msg: str):
        """Envia mensagem pelo socket de jogo."""
        self._send_raw(self.game_sock, msg)

    def send_chat(self, msg: str):
        """Envia mensagem pelo socket de chat."""
        self._send_raw(self.chat_sock, msg)

    @staticmethod
    def _send_raw(sock: socket.socket, msg: str):
        """Serializa a mensagem como linha UTF-8 e envia pelo socket."""
        try:
            sock.sendall((msg + "\n").encode("utf-8"))
        except Exception as e:
            print(f"[Network] Erro ao enviar '{msg}': {e}")

    # Leitura assíncrona 
    def _read_loop(self, sock: socket.socket, dispatch: Callable[[str], None]):
        """
        Loop de leitura de um socket.
        Acumula bytes num buffer e despacha uma mensagem por vez (delimitada por \\n).
        Executado em Thread daemon separada.
        """
        buf = ""
        try:
            while True:
                chunk = sock.recv(4096).decode("utf-8")
                if not chunk:
                    break
                buf += chunk
                while "\n" in buf:
                    line, buf = buf.split("\n", 1)
                    line = line.strip()
                    if line:
                        dispatch(line)
        except Exception as e:
            if self._on_disconnect:
                self._on_disconnect(str(e))

    # Despacho de mensagens 

    def _dispatch_game(self, msg: str):
        """Encaminha mensagem do socket de jogo para o callback registrado."""
        print(f"[JOGO ←] {msg}")
        if self._on_game_msg:
            self._on_game_msg(msg)

    def _dispatch_chat(self, msg: str):
        """
        Mensagens de chat chegam no formato  'NOME: texto'.
        Separa remetente e conteúdo e aciona o callback de chat.
        """
        print(f"[CHAT ←] {msg}")
        if self._on_chat_msg:
            idx = msg.find(":")
            if idx >= 0:
                sender = msg[:idx].strip()
                text   = msg[idx + 1:].strip()
            else:
                sender, text = "?", msg
            self._on_chat_msg(sender, text)
