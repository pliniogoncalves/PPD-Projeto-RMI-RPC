from xmlrpc.server import SimpleXMLRPCServer
from xmlrpc.server import SimpleXMLRPCRequestHandler
import threading

from game_logic import (
    criar_tabuleiro, verificar_vitoria, eh_movimento_valido,
    realizar_movimento, verificar_e_realizar_capturas, proximo_jogador,
    eh_casa_central, pode_continuar_jogada_apos_captura,
    existe_captura_com_movimento, jogador_esta_bloqueado, peca_esta_bloqueada
)

class QuietRequestHandler(SimpleXMLRPCRequestHandler):
    def log_message(self, format, *args):
        """Sobrescreve o método original para não imprimir logs de acesso HTTP."""
        pass

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
            self.turnos_peca_central = 0
            self.jogador_peca_central = None


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
                self.mensagens_erro[player_id] = None

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
            if self.fase != "movimentacao" or player_id != self.jogador_atual:
                self.mensagens_erro[player_id] = "Aguarde seu turno."
                return False
            
            if jogador_esta_bloqueado(self.tabuleiro, player_id):
                self.mensagens_erro[player_id] = "Você está bloqueado! Remova uma peça adversária."
                self.modo_remocao[player_id] = True
                return False

            peca_no_centro = self.tabuleiro[2][2]
            if peca_no_centro == player_id and self.jogador_peca_central == player_id and self.turnos_peca_central >= 3:
            
                if peca_esta_bloqueada(self.tabuleiro, 2, 2):
                    self.mensagens_erro[player_id] = "Peça central bloqueada! Remova uma peça adversária adjacente."
                    self.modo_remocao[player_id] = True
                    return False 
                
                elif (linha_origem, coluna_origem) != (2, 2):
                    self.mensagens_erro[player_id] = "Regra dos 3 turnos: Você DEVE mover a peça central."
                    return False

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
            
            if not eh_movimento_valido(self.tabuleiro, linha_origem, coluna_origem, linha_destino, coluna_destino, player_id):
                self.mensagens_erro[player_id] = "Movimento inválido."
                return False

            realizar_movimento(self.tabuleiro, linha_origem, coluna_origem, linha_destino, coluna_destino)
            capturou = verificar_e_realizar_capturas(self.tabuleiro, linha_destino, coluna_destino, player_id)

            if verificar_vitoria(self.tabuleiro, player_id):
                self.vencedor = player_id; return True

            jogador_troca = True
            if capturou and pode_continuar_jogada_apos_captura(self.tabuleiro, linha_destino, coluna_destino, player_id):
                jogador_troca = False
            
            if jogador_troca:
                self.jogador_atual = proximo_jogador(self.jogador_atual)
                
                peca_final_centro = self.tabuleiro[2][2]
                if peca_final_centro != 0 and peca_final_centro == self.jogador_peca_central:
                    self.turnos_peca_central += 1
                elif peca_final_centro != 0 and peca_final_centro != self.jogador_peca_central:
                    self.jogador_peca_central = peca_final_centro
                    self.turnos_peca_central = 1
                else:
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