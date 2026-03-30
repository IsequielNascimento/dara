"""
game_state.py — Estado e regras do Jogo Dara
Responsável por: tabuleiro, fases, validações, contagem de peças.
Não possui dependências de UI ou rede.
"""

from constants import ROWS, COLS, TOTAL_PIECES


class GameState:
    """
    Mantém o estado completo de uma partida de Dara:
      - tabuleiro 5×6
      - fase atual (PLACEMENT / MOVEMENT)
      - turno corrente
      - contagem de peças colocadas por cada jogador
      - flag de captura pendente
      - peça selecionada para mover
    """

    def __init__(self):
        self.reset()

    def reset(self):
        # board[r][c]: 0 = vazio, 1 = jogador 1, 2 = jogador 2
        self.board: list[list[int]] = [[0] * COLS for _ in range(ROWS)]

        self.phase: str       = "PLACEMENT"  
        self.current_turn: int = 0          
        self.pieces_placed: list[int] = [0, 0]  
        self.waiting_capture: bool = False   
        self.selected: tuple | None = None   

    # Consultas 

    def cell(self, row: int, col: int) -> int:
        return self.board[row][col]

    def count_pieces(self, player_id: int) -> int:
        """Conta peças do jogador (1 ou 2) no tabuleiro."""
        return sum(
            self.board[r][c] == player_id
            for r in range(ROWS) for c in range(COLS)
        )

    def pieces_remaining(self, player_idx: int) -> int:
        """Peças que ainda faltam colocar na fase de Colocação."""
        return TOTAL_PIECES - self.pieces_placed[player_idx]

    def all_placed(self) -> bool:
        """Retorna True quando ambos os jogadores colocaram todas as peças."""
        return all(p >= TOTAL_PIECES for p in self.pieces_placed)

    # Validações 
    @staticmethod
    def in_bounds(row: int, col: int) -> bool:
        return 0 <= row < ROWS and 0 <= col < COLS

    @staticmethod
    def is_adjacent(r1: int, c1: int, r2: int, c2: int) -> bool:
        """Retorna True se as duas casas são adjacentes (horizontal ou vertical)."""
        return (abs(r1 - r2) == 1 and c1 == c2) or \
               (abs(c1 - c2) == 1 and r1 == r2)

    def makes_line3(self, row: int, col: int, pid: int) -> bool:
        """
        Verifica se a peça em (row, col) com id `pid` forma uma linha de 3
        na horizontal ou vertical.
        """
        return (self._count_line(row, col, pid, 0, 1) >= 3 or   # horizontal
                self._count_line(row, col, pid, 1, 0) >= 3)      # vertical

    def _count_line(self, row: int, col: int, pid: int,
                    dr: int, dc: int) -> int:
        """Conta peças contíguas do mesmo jogador numa direção (e seu oposto)."""
        count = 1
        for d in (-1, 1):
            r, c = row + d * dr, col + d * dc
            while self.in_bounds(r, c) and self.board[r][c] == pid:
                count += 1
                r += d * dr
                c += d * dc
        return count

    # Aplicação de jogadas 
    def place_piece(self, row: int, col: int, pid: int):
        """Coloca uma peça no tabuleiro e incrementa o contador do jogador."""
        self.board[row][col] = pid
        self.pieces_placed[pid - 1] += 1

    def move_piece(self, r1: int, c1: int, r2: int, c2: int):
        """Move a peça de (r1,c1) para (r2,c2)."""
        self.board[r2][c2] = self.board[r1][c1]
        self.board[r1][c1] = 0

    def remove_piece(self, row: int, col: int):
        """Remove uma peça do tabuleiro (captura)."""
        self.board[row][col] = 0

    def advance_turn(self):
        """Alterna o turno corrente."""
        self.current_turn = 1 - self.current_turn

    def enter_movement_phase(self):
        self.phase = "MOVEMENT"
        self.selected = None
        self.waiting_capture = False
