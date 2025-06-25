TABULEIRO_TAMANHO = 5

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
                            
                            temp = [r[:] for r in copia]
                            verificar_e_realizar_capturas(copia, l_dest, c_dest, jogador_atual)
                            if copia != temp:  
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
    
    
    for dl, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        novo_l = centro + dl
        novo_c = centro + dc
        if (0 <= novo_l < TABULEIRO_TAMANHO and 
            0 <= novo_c < TABULEIRO_TAMANHO and 
            tabuleiro[novo_l][novo_c] == 0):
            return False  
    return True  

def peca_esta_bloqueada(tabuleiro, linha, coluna):
    """Verifica se uma peça específica em uma dada posição não tem movimentos legais."""
    
    for dl, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        nl, nc = linha + dl, coluna + dc
        
        if 0 <= nl < 5 and 0 <= nc < 5 and tabuleiro[nl][nc] == 0:
            return False

    return True
