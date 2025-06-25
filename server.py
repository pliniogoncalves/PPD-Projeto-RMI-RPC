# ==============================================================================
# ===== ANTES: Importações para o servidor baseado em Sockets ==================
# ==============================================================================
# import socket
# import pickle
# from main import preencher_tabuleiro_automaticamente

# ==============================================================================
# ===== DEPOIS: Importações para o servidor baseado em XML-RPC =================
# ==============================================================================
from xmlrpc.server import SimpleXMLRPCServer
from xmlrpc.server import SimpleXMLRPCRequestHandler
import threading

# Importações da lógica do jogo (permanecem as mesmas)
from game_logic import (
    criar_tabuleiro, verificar_vitoria, eh_movimento_valido,
    realizar_movimento, verificar_e_realizar_capturas, proximo_jogador,
    eh_casa_central, pode_continuar_jogada_apos_captura,
    existe_captura_com_movimento, jogador_esta_bloqueado, peca_esta_bloqueada
)

# ==============================================================================
# ===== ANTES: Variáveis globais para o servidor de Sockets ====================
# ==============================================================================
# Na abordagem antiga, o estado do jogo era gerenciado por variáveis globais,
# o que pode ser mais difícil de manter.
#
# HOST = '127.0.0.1'
# PORT = 55555
# tabuleiro = criar_tabuleiro()
# jogador_atual = 1
# fase = "colocacao"
# pecas_colocadas = {1: 0, 2: 0}
# pecas_turno_atual = {1: 0, 2: 0}
# conexoes = {}
# ultima_captura = {"jogador": None, "linha": None, "coluna": None}
# lock = threading.Lock()
# ultimo_jogador_colocou = None
# movimento_pendente = {}
#
# # Esta lógica de preenchimento automático interativo foi removida para tornar
# # o servidor um serviço não interativo, que é o padrão para RPC.
# if input("Preencher automaticamente o tabuleiro? (s/n): ").lower() == 's':
#     tabuleiro = preencher_tabuleiro_automaticamente(tabuleiro)
#     fase = "movimentacao"

# ==============================================================================
# ===== DEPOIS: Estrutura de Servidor XML-RPC com Classe de Jogo ===============
# ==============================================================================

# ===== NOVO: Handler Silencioso para Desativar o Log de Acesso =====
# Criamos uma classe que herda da original, mas sobrescrevemos o método
# de log para que ele não faça nada (pass).
class QuietRequestHandler(SimpleXMLRPCRequestHandler):
    def log_message(self, format, *args):
        """Sobrescreve o método original para não imprimir logs de acesso HTTP."""
        pass

# A classe GameServer agora encapsula TODO o estado e a lógica do jogo.
# Em vez de variáveis globais, o estado é mantido como atributos da instância (self).
class GameServer:
    def __init__(self):
        """Inicializa o servidor do jogo, criando um lock para controle de concorrência e resetando o estado."""
        self.lock = threading.Lock()
        self.reset_game()

    def reset_game(self):
        """Reseta todas as variáveis de estado para iniciar uma nova partida."""
        with self.lock:
            self.tabuleiro = criar_tabuleiro()
            self.jogador_atual = 1
            self.fase = "colocacao"
            self.pecas_colocadas = {1: 0, 2: 0}
            self.pecas_turno_atual = {1: 0, 2: 0}
            self.ultimo_jogador_colocou = None
            self.vencedor = None
            self.chat_log = []
            self.conexoes = {1: False, 2: False}
            self.mensagens_erro = {1: None, 2: None}
            self.modo_remocao = {1: False, 2: False}
            # ===== ESTADO ADICIONADO PARA AS REGRAS COMPLEXAS =====
            self.turnos_peca_central = 0
            self.jogador_peca_central = None


    # --- MÉTODOS EXPOSTOS PELA API RPC ---

    def register_player(self):
        """Registra um novo jogador, atribuindo ID 1 ou 2. Retorna 0 se o servidor estiver cheio."""
        with self.lock:
            if not self.conexoes[1]:
                self.conexoes[1] = True; print("[+] Jogador 1 conectado."); return 1
            elif not self.conexoes[2]:
                self.conexoes[2] = True; print("[+] Jogador 2 conectado."); return 2
            else:
                print("[-] Tentativa de conexão recusada: servidor cheio."); return 0

    def get_state(self, player_id):
        """Método que o cliente chama periodicamente para "puxar" o estado atual do jogo."""
        with self.lock:
            error_message = self.mensagens_erro.get(player_id)
            if error_message:
                self.mensagens_erro[player_id] = None # Limpa a mensagem de erro após enviá-la uma vez

            return {
                "tabuleiro": self.tabuleiro,
                "jogador_atual": self.jogador_atual,
                "fase": self.fase,
                "vencedor": self.vencedor,
                "chat_log": self.chat_log,
                "seu_turno": self.jogador_atual == player_id,
                "error": error_message,
                "modo_remocao": self.modo_remocao.get(player_id, False)
            }

    def send_chat_message(self, player_id, message):
        """Adiciona uma mensagem ao log de chat do servidor."""
        with self.lock:
            self.chat_log.append(f"[Jogador {player_id}] {message}")
        return True

    def place_piece(self, player_id, linha, coluna):
        """Lida com a lógica de colocação de peças."""
        with self.lock:
            if self.fase != "colocacao" or player_id != self.jogador_atual:
                self.mensagens_erro[player_id] = "Não é seu turno."
                return False
            if not (0 <= linha < 5 and 0 <= coluna < 5):
                self.mensagens_erro[player_id] = "Posição fora do tabuleiro."
                return False
            if eh_casa_central(linha, coluna) or self.tabuleiro[linha][coluna] != 0:
                self.mensagens_erro[player_id] = "Posição inválida."
                return False

            self.tabuleiro[linha][coluna] = player_id
            self.pecas_colocadas[player_id] = self.pecas_colocadas.get(player_id, 0) + 1
            self.pecas_turno_atual[player_id] = self.pecas_turno_atual.get(player_id, 0) + 1
            self.ultimo_jogador_colocou = player_id

            if self.pecas_turno_atual[player_id] == 2:
                self.pecas_turno_atual[player_id] = 0
                if self.pecas_colocadas.get(1, 0) >= 12 and self.pecas_colocadas.get(2, 0) >= 12:
                    self.fase = "movimentacao"
                    self.jogador_atual = self.ultimo_jogador_colocou
                else:
                    self.jogador_atual = proximo_jogador(self.jogador_atual)
            return True

    def move_piece(self, player_id, linha_origem, coluna_origem, linha_destino, coluna_destino):
        """Lida com a lógica de movimento de peças, agora com todas as regras complexas."""
        with self.lock:
            # Validações iniciais
            if self.fase != "movimentacao" or player_id != self.jogador_atual:
                self.mensagens_erro[player_id] = "Aguarde seu turno."
                return False
            
            # PRIORIDADE 1: Bloqueio Total
            # Se o jogador não tem nenhum movimento possível, esta regra tem precedência sobre todas as outras.
            if jogador_esta_bloqueado(self.tabuleiro, player_id):
                self.mensagens_erro[player_id] = "Você está bloqueado! Remova uma peça adversária."
                self.modo_remocao[player_id] = True
                return False

            # PRIORIDADE 2: Regra dos 3 Turnos da Casa Central
            peca_no_centro = self.tabuleiro[2][2]
            if peca_no_centro == player_id and self.jogador_peca_central == player_id and self.turnos_peca_central >= 3:
            
                # ===== NOVA SUB-CONDIÇÃO: A peça central está, ela mesma, bloqueada? =====
                if peca_esta_bloqueada(self.tabuleiro, 2, 2):
                    self.mensagens_erro[player_id] = "Peça central bloqueada! Remova uma peça adversária adjacente."
                    self.modo_remocao[player_id] = True
                    return False # Ativa o modo de remoção para resolver o bloqueio específico
                
                # Se a peça central não estiver bloqueada, a regra original se aplica
                elif (linha_origem, coluna_origem) != (2, 2):
                    self.mensagens_erro[player_id] = "Regra dos 3 turnos: Você DEVE mover a peça central."
                    return False

            # PRIORIDADE 3: Captura Obrigatória
            elif existe_captura_com_movimento(self.tabuleiro, player_id):
                copia_tabuleiro = [row[:] for row in self.tabuleiro]
                if eh_movimento_valido(copia_tabuleiro, linha_origem, coluna_origem, linha_destino, coluna_destino, player_id):
                    realizar_movimento(copia_tabuleiro, linha_origem, coluna_origem, linha_destino, coluna_destino)
                    if not verificar_e_realizar_capturas(copia_tabuleiro, linha_destino, coluna_destino, player_id):
                        self.mensagens_erro[player_id] = "Movimento inválido. Existe uma captura obrigatória a ser feita."
                        return False
                else:
                    self.mensagens_erro[player_id] = "Movimento inválido. Lembre-se que há uma captura obrigatória."
                    return False
            
            # CASO PADRÃO: Movimento Normal
            # Se nenhuma das regras de prioridade foi acionada, trata-se de um movimento comum.
            if not eh_movimento_valido(self.tabuleiro, linha_origem, coluna_origem, linha_destino, coluna_destino, player_id):
                self.mensagens_erro[player_id] = "Movimento inválido."
                return False

            # Executa o movimento e captura
            realizar_movimento(self.tabuleiro, linha_origem, coluna_origem, linha_destino, coluna_destino)
            capturou = verificar_e_realizar_capturas(self.tabuleiro, linha_destino, coluna_destino, player_id)

            if verificar_vitoria(self.tabuleiro, player_id):
                self.vencedor = player_id; return True

            # Lógica para trocar de turno e atualizar contagem da casa central
            jogador_troca = True
            if capturou and pode_continuar_jogada_apos_captura(self.tabuleiro, linha_destino, coluna_destino, player_id):
                jogador_troca = False # Não troca o jogador, pois ele pode continuar
            
            if jogador_troca:
                self.jogador_atual = proximo_jogador(self.jogador_atual)
                
                # ===== LÓGICA REINSERIDA: Contagem de turnos da casa central =====
                peca_final_centro = self.tabuleiro[2][2]
                if peca_final_centro != 0 and peca_final_centro == self.jogador_peca_central:
                    self.turnos_peca_central += 1
                elif peca_final_centro != 0 and peca_final_centro != self.jogador_peca_central:
                    self.jogador_peca_central = peca_final_centro
                    self.turnos_peca_central = 1
                else: # Casa central ficou vazia
                    self.jogador_peca_central = None
                    self.turnos_peca_central = 0
            return True

    def remove_piece_when_blocked(self, player_id, linha, coluna):
        """Permite que um jogador bloqueado remova uma peça adversária."""
        with self.lock:
            if not self.modo_remocao.get(player_id):
                self.mensagens_erro[player_id] = "Não está em modo de remoção."; return False
            adversario = proximo_jogador(player_id)
            if self.tabuleiro[linha][coluna] == adversario:
                self.tabuleiro[linha][coluna] = 0; self.modo_remocao[player_id] = False; return True
            else:
                self.mensagens_erro[player_id] = "Selecione uma peça do adversário."; return False

    def surrender(self, player_id):
        """Registra a desistência de um jogador."""
        with self.lock:
            self.vencedor = proximo_jogador(player_id)
            self.chat_log.append(f"Jogador {player_id} desistiu.")
            print(f"[*] Fim de jogo. Jogador {self.vencedor} venceu por desistência.")
        return True

# ==============================================================================
# ===== ANTES: Funções de comunicação e loop principal do servidor Sockets =====
# ==============================================================================
# A função 'broadcast' enviava uma mensagem para todas as conexões ativas.
# No modelo RPC, o cliente é quem busca o estado, então o broadcast não é necessário.
#
# def broadcast(message):
#     for conn in list(conexoes.keys()):
#         try:
#             conn.sendall(pickle.dumps(message))
#         except:
#             del conexoes[conn]
#
# A função 'enviar_estado_para_todos' era uma especialização do broadcast.
#
# def enviar_estado_para_todos():
#     broadcast({
#         "tipo": "estado",
#         "tabuleiro": tabuleiro,
#         "jogador": jogador_atual,
#         "fase": fase
#     })
#
# A função 'handle_client' era o coração do servidor antigo. Ela rodava em uma thread
# para cada jogador, ouvindo constantemente por novas mensagens. Todo o seu conteúdo
# foi refatorado e distribuído entre os métodos da classe GameServer.
#
# def handle_client(conn, addr):
#     global jogador_atual, tabuleiro, fase, pecas_colocadas, pecas_turno_atual, ultima_captura
#     jogador_id = len(conexoes) + 1
#     conexoes[conn] = jogador_id
#     print(f"[+] Jogador {jogador_id} conectado: {addr}")
#     conn.sendall(pickle.dumps({"tipo": "id", "jogador": jogador_id}))
#     enviar_estado_para_todos()
#     while True:
#         try:
#             data = pickle.loads(conn.recv(4096))
#             if not data: break
#             tipo = data["tipo"]
#             # O grande bloco if/elif que existia aqui agora é tratado por chamadas diretas de métodos RPC.
#             # if tipo == "colocacao": ...
#             # if tipo == "movimento": ...
#             # etc...
#         except Exception as e:
#             print(f"[!] Erro com jogador {jogador_id}: {e}")
#             break
#     print(f"[-] Jogador {jogador_id} desconectado.")
#     del conexoes[conn]
#     conn.close()
#
# A função 'start_server' era o ponto de entrada do servidor de sockets.
#
# def start_server():
#     sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#     sock.bind((HOST, PORT))
#     sock.listen(2)
#     print("[*] Servidor iniciado. Aguardando jogadores...")
#     while len(conexoes) < 2:
#         conn, addr = sock.accept()
#         threading.Thread(target=handle_client, args=(conn, addr)).start()
#
# # Ponto de entrada do servidor antigo
# start_server()


# ==============================================================================
# ===== DEPOIS: Função principal e ponto de entrada do servidor XML-RPC ========
# ==============================================================================

def run_server():
    """Configura e inicia o servidor XML-RPC."""
    server_addr = ('127.0.0.1', 55555)
    server = SimpleXMLRPCServer(server_addr, requestHandler=QuietRequestHandler, allow_none=True)
    server.register_introspection_functions()
    server.register_instance(GameServer())
    print("🎮 Servidor XML-RPC do jogo Seega iniciado em http://127.0.0.1:55555")
    server.serve_forever()

if __name__ == "__main__":
    run_server()