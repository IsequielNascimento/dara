"""
constants.py — Constantes globais do Jogo Dara
Importado por todos os módulos do cliente e pelo servidor.
"""

# Rede 
HOST_DEFAULT  = "localhost"
PORT_GAME     = 9090   # Socket de jogo 
PORT_CHAT     = 9091   # Socket de chat  

# Tabuleiro 
ROWS          = 5
COLS          = 6
TOTAL_PIECES  = 12 #cada jogador     

# Paleta de cores
CLR_BG         = "#1E1E2E"   # fundo geral da janela
CLR_PANEL      = "#2A2A3E"   # painel de status
CLR_ACCENT     = "#301F4D"   # destaque
CLR_TEXT       = "#E0E0F0"   # texto padrão

CLR_BOARD_BG   = "#C8A96E"   # fundo do tabuleiro
CLR_BOARD_LINE = "#5C3A00"   # linhas e rótulos do tabuleiro

CLR_P1         = "#1A1A2E"   # peça jogador 1 (preto-azulado)
CLR_P1_LT      = "#3A3A5E"   # brilho da peça 1
CLR_P1_SHADOW  = "#3A3A3A"   # sombra da peça 1
CLR_P2         = "#F9F9F9"   # peça jogador 2 (branco)
CLR_P2_DK      = "#AAAAAA"   # borda da peça 2
CLR_P2_SHADOW  = "#999999"   # sombra da peça 2

CLR_SELECT     = "#00CC88"   # célula selecionada
CLR_VALID      = "#FFD700"   # casas de movimento válido
CLR_CAPTURE    = "#FF3333"   # peça capturável

CLR_TURN_MY    = "#00FF88"   # label de turno — minha vez
CLR_TURN_OPP   = "#FF8888"   # label de turno — vez do oponente
CLR_GOLD       = "#FFD700"   # label inicial de turno
