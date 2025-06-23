# reconhecimento.py
import os
import cv2
import face_recognition
import numpy as np
from datetime import datetime
import threading
import time
from queue import Queue
import base64
from cadastro import listar_alunos

class ReconhecimentoFacial:
    def __init__(self):
        self.codificacoes_referencia = []
        self.nomes_referencia = []
        self.ausencias_consecutivas = {}
        self.monitoramento_ativo = False
        self.frame_queue = Queue(maxsize=5) # Fila para comunicação entre threads
        self.lock = threading.Lock()
        self.callback_mensagens = None
        self.callback_frame = None
        
        self.carregar_codificacoes_referencia()
        
    def definir_callback_mensagens(self, callback):
        self.callback_mensagens = callback
    
    def definir_callback_frame(self, callback):
        self.callback_frame = callback

    def iniciar_monitoramento(self, camera_id=0):
        if self.monitoramento_ativo:
            return
        self.monitoramento_ativo = True
        
        threading.Thread(target=self._capturar_frames, args=(camera_id,), daemon=True).start()
        threading.Thread(target=self._processar_frames, daemon=True).start()
    
    def parar_monitoramento(self):
        self.monitoramento_ativo = False

    def _capturar_frames(self, camera_id):
        """Thread que captura frames da câmera e os envia para o feed de vídeo E para a fila de processamento."""
        print(f"[MONITORAMENTO] Tentando abrir a câmera {camera_id}...")
        
        cap = cv2.VideoCapture(camera_id, cv2.CAP_DSHOW if os.name == 'nt' else cv2.CAP_ANY)
        if not cap.isOpened():
            print(f"[AVISO] Backend preferencial falhou. Tentando backend padrão para câmera {camera_id}.")
            cap.open(camera_id)
        
        if not cap.isOpened():
            error_msg = f"[ERRO CRÍTICO] Não foi possível abrir a câmera {camera_id} para monitoramento."
            print(error_msg)
            if self.callback_mensagens:
                self.callback_mensagens([error_msg.replace('[ERRO CRÍTICO] ', '')])
            return

        print(f"[MONITORAMENTO] Câmera {camera_id} aberta com sucesso.")
        
        while self.monitoramento_ativo:
            ret, frame = cap.read()
            if not ret or frame is None:
                print("[AVISO] Frame nulo ou inválido recebido da câmera.")
                time.sleep(1)
                continue

            # --- CORREÇÃO ADICIONADA AQUI ---
            # Coloca o frame original na fila para ser analisado pela outra thread.
            if not self.frame_queue.full():
                self.frame_queue.put(frame)
            # --------------------------------

            # Codifica o frame para enviar para a interface (feed de vídeo).
            ret_encode, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            if ret_encode:
                frame_base64 = base64.b64encode(buffer).decode('utf-8')
                if self.callback_frame:
                    self.callback_frame(f'data:image/jpeg;base64,{frame_base64}')
            
            time.sleep(1 / 15)  # Limita a ~15 FPS para performance

        cap.release()
        print(f"[MONITORAMENTO] Câmera {camera_id} liberada.")

    def _processar_frames(self):
        """Thread que pega frames da fila, processa o reconhecimento e envia os logs."""
        ultima_verificacao = 0
        print("[PROCESSAMENTO] Thread de processamento iniciada. Aguardando para iniciar verificações.")

        while self.monitoramento_ativo:
            time.sleep(1) 

            if self.frame_queue.empty():
                continue
            
            if time.time() - ultima_verificacao >= 30:
                print(f"[PROCESSAMENTO] Timer de 30s atingido. Processando um frame...")
                frame = self.frame_queue.get()
                
                # Limpa a fila para não processar frames antigos e pegar sempre o mais recente
                while not self.frame_queue.empty():
                    try:
                        self.frame_queue.get_nowait()
                    except Exception:
                        break

                alunos_presentes, mensagens = self.verificar_presenca(frame)
                print(f"[PROCESSAMENTO] Verificação concluída. Mensagens geradas: {mensagens}")

                with self.lock:
                    for id_aluno in self.nomes_referencia:
                        nome_aluno_str = str(id_aluno)
                        if nome_aluno_str in alunos_presentes:
                            self.ausencias_consecutivas[nome_aluno_str] = 0
                        else:
                            self.ausencias_consecutivas[nome_aluno_str] = self.ausencias_consecutivas.get(nome_aluno_str, 0) + 1
                            if self.ausencias_consecutivas[nome_aluno_str] >= 2:
                                mensagens.append(f"ALERTA: Aluno {nome_aluno_str} ausente há {self.ausencias_consecutivas[nome_aluno_str]} verificações.")
                
                if self.callback_mensagens and mensagens:
                    print("[PROCESSAMENTO] Enviando mensagens para a interface.")
                    self.callback_mensagens(mensagens)
                
                ultima_verificacao = time.time()

    def carregar_codificacoes_referencia(self):
        try:
            alunos = listar_alunos()
            with self.lock:
                self.codificacoes_referencia = [np.array(aluno['codificacao_facial']) for aluno in alunos]
                self.nomes_referencia = [str(aluno['Id']) for aluno in alunos]
                self.ausencias_consecutivas = {str(aluno['Id']): 0 for aluno in alunos}
            print("[INFO] Codificações de referência recarregadas.")
        except Exception as e:
            msg = f"Erro ao carregar codificações: {e}"
            print(f"[ERRO] {msg}")
            if self.callback_mensagens:
                self.callback_mensagens([msg])

    def verificar_presenca(self, frame):
        alunos_presentes = set()
        mensagens = []
        
        frame_pequeno = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
        rgb_frame_pequeno = cv2.cvtColor(frame_pequeno, cv2.COLOR_BGR2RGB)

        with self.lock:
            codificacoes_ref = self.codificacoes_referencia
            nomes_ref = self.nomes_referencia

        if not codificacoes_ref:
            return list(alunos_presentes), ["Nenhum aluno cadastrado para verificar."]
            
        locais_faces = face_recognition.face_locations(rgb_frame_pequeno)
        codificacoes_faces = face_recognition.face_encodings(rgb_frame_pequeno, locais_faces)

        timestamp = datetime.now().strftime("%H:%M:%S")
        if not codificacoes_faces:
            mensagens.append(f"[{timestamp}] Nenhum rosto detectado no frame.")

        for codificacao in codificacoes_faces:
            matches = face_recognition.compare_faces(codificacoes_ref, codificacao, tolerance=0.5)
            nome_identificado = "Desconhecido"
            
            if True in matches:
                indice_match = matches.index(True)
                nome_identificado = nomes_ref[indice_match]
                if nome_identificado not in alunos_presentes:
                    alunos_presentes.add(nome_identificado)
                    mensagens.append(f"[{timestamp}] Presença confirmada: Aluno {nome_identificado}")
            else:
                 mensagens.append(f"[{timestamp}] Rosto não reconhecido detectado.")
        
        return list(alunos_presentes), mensagens