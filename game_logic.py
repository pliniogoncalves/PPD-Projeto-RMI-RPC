TABULEIRO_TAMANHO = 5
# ===== REMOVIDO DAQUI =====
# As variáveis globais abaixo foram removidas pois o estado da contagem
# de turnos da casa central agora é gerenciado pela classe GameServer.
# contador_turnos_peca_central = 0
# posicao_peca_central = None

def criar_tabuleiro():
    return [[0 for _ in range(TABULEIRO_TAMANHO)] for _ in range(TABULEIRO_TAMANHO)]

def eh_casa_central(linha, coluna):
    meio = TABULEIRO_TAMANHO // 2
    return linha == meio and coluna == meio

def proximo_jogador(jogador_atual):
    return 2 if jogador_atual == 1 else 1

def eh_movimento_valido(tabuleiro, linha_origem, coluna_origem, linha_destino, coluna_destino, jogador_atual):
    if tabuleiro[linha_origem][coluna_origem] != jogador_atual:
        return False
    if tabuleiro[linha_destino][coluna_destino] != 0:
        return False
    if not ((linha_origem == linha_destino and abs(coluna_origem - coluna_destino) == 1) or
            (coluna_origem == coluna_destino and abs(linha_origem - linha_destino) == 1)):
        return False
    return True

def realizar_movimento(tabuleiro, linha_origem, coluna_origem, linha_destino, coluna_destino):
    jogador = tabuleiro[linha_origem][coluna_origem]
    tabuleiro[linha_destino][coluna_destino] = jogador
    tabuleiro[linha_origem][coluna_origem] = 0

def verificar_e_realizar_capturas(tabuleiro, linha, coluna, jogador_atual):
    capturou = False
    for dl, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        l_adj = linha + dl
        c_adj = coluna + dc
        l_oposto = linha + 2 * dl
        c_oposto = coluna + 2 * dc
        if 0 <= l_adj < TABULEIRO_TAMANHO and 0 <= c_adj < TABULEIRO_TAMANHO and \
           0 <= l_oposto < TABULEIRO_TAMANHO and 0 <= c_oposto < TABULEIRO_TAMANHO:
            if tabuleiro[l_adj][c_adj] != 0 and tabuleiro[l_adj][c_adj] != jogador_atual and \
               tabuleiro[l_oposto][c_oposto] == jogador_atual:
                
                if eh_casa_central(l_adj, c_adj):
                    continue

                tabuleiro[l_adj][c_adj] = 0
                capturou = True
    return capturou


def verificar_vitoria(tabuleiro, jogador_atual):
    adversario = 1 if jogador_atual == 2 else 2
    for linha in tabuleiro:
        if adversario in linha:
            return False
    return True

def existe_captura_possivel(tabuleiro, jogador_atual):
    for linha in range(TABULEIRO_TAMANHO):
        for coluna in range(TABULEIRO_TAMANHO):
            if tabuleiro[linha][coluna] == jogador_atual:
                for dl, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    l_dest = linha + dl
                    c_dest = coluna + dc
                    if 0 <= l_dest < TABULEIRO_TAMANHO and 0 <= c_dest < TABULEIRO_TAMANHO:
                        if eh_movimento_valido(tabuleiro, linha, coluna, l_dest, c_dest, jogador_atual):
                            copia = [r[:] for r in tabuleiro]
                            realizar_movimento(copia, linha, coluna, l_dest, c_dest)
                            # Verifica se houve captura após o movimento
                            temp = [r[:] for r in copia]
                            verificar_e_realizar_capturas(copia, l_dest, c_dest, jogador_atual)
                            if copia != temp:  # Compara com estado pós-movimento
                                return True
    return False

def pode_continuar_jogada_apos_captura(tabuleiro, linha, coluna, jogador_atual):
    for dl, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        l_dest = linha + dl
        c_dest = coluna + dc
        if 0 <= l_dest < TABULEIRO_TAMANHO and 0 <= c_dest < TABULEIRO_TAMANHO:
            if eh_movimento_valido(tabuleiro, linha, coluna, l_dest, c_dest, jogador_atual):
                copia = [r[:] for r in tabuleiro]
                realizar_movimento(copia, linha, coluna, l_dest, c_dest)
                temp = [r[:] for r in copia]
                verificar_e_realizar_capturas(copia, l_dest, c_dest, jogador_atual)
                if copia != temp:
                    return True
    return False

# ===== REMOVIDO DAQUI =====
# A função verificar_regras_casa_central foi removida pois sua lógica,
# que depende de estado, foi movida para a classe GameServer.
#def verificar_regras_casa_central(tabuleiro):
#    global contador_turnos_peca_central, posicao_peca_central
#
#    centro = TABULEIRO_TAMANHO // 2
#    peca = tabuleiro[centro][centro]
#
#    if peca != 0:
#        if posicao_peca_central == (centro, centro):
#            contador_turnos_peca_central += 1
#        else:
#            posicao_peca_central = (centro, centro)
#            contador_turnos_peca_central = 1
#    else:
#        posicao_peca_central = None
#        contador_turnos_peca_central = 0
#
#    if peca != 0 and contador_turnos_peca_central >= 3:
#        return False
#    return True

def existe_captura_com_movimento(tabuleiro, jogador_id):
    for i in range(TABULEIRO_TAMANHO):
        for j in range(TABULEIRO_TAMANHO):
            if tabuleiro[i][j] == jogador_id:
                for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    ni, nj = i + dx, j + dy
                    if 0 <= ni < TABULEIRO_TAMANHO and 0 <= nj < TABULEIRO_TAMANHO:
                        if eh_movimento_valido(tabuleiro, i, j, ni, nj, jogador_id):
                            copia = [linha[:] for linha in tabuleiro]
                            realizar_movimento(copia, i, j, ni, nj)
                            temp = [linha[:] for linha in copia]
                            if verificar_e_realizar_capturas(copia, ni, nj, jogador_id):
                                return True
    return False

def jogador_esta_bloqueado(tabuleiro, jogador_id):
    for i in range(len(tabuleiro)):
        for j in range(len(tabuleiro[i])):
            if tabuleiro[i][j] == jogador_id:
                for dl, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                    ni, nj = i + dl, j + dc
                    if 0 <= ni < 5 and 0 <= nj < 5:
                        if tabuleiro[ni][nj] == 0:
                            return False
    return True

def peca_central_bloqueada(tabuleiro, jogador_id):
    centro = TABULEIRO_TAMANHO // 2
    if tabuleiro[centro][centro] != jogador_id:
        return False
    
    # Verifica todos os movimentos possíveis da peça central
    for dl, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        novo_l = centro + dl
        novo_c = centro + dc
        if (0 <= novo_l < TABULEIRO_TAMANHO and 
            0 <= novo_c < TABULEIRO_TAMANHO and 
            tabuleiro[novo_l][novo_c] == 0):
            return False  # A peça tem para onde mover
    return True  # Está completamente bloqueada
