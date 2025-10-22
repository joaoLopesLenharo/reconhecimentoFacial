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
from cadastro import listar_alunos, obter_responsavel_por_aluno
from smtp_service import send_email

class ReconhecimentoFacial:
    def __init__(self):
        self.codificacoes_referencia = []
        self.nomes_referencia = []
        self.ausencias_consecutivas = {}
        self.ultima_presenca = {}  # Para rastrear quando o aluno foi visto pela última vez
        self.email_enviado = {}  # Para rastrear se já foi enviado e-mail de ausência
        self.monitoramento_ativo = False
        self.frame_queue = Queue(maxsize=5)  # Fila para comunicação entre threads
        self.lock = threading.Lock()
        self.callback_mensagens = None
        self.callback_frame = None
        
        self.carregar_codificacoes_referencia()
        
        # Classificador Haar para fallback de detecção de rosto
        self._haar_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        
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

            # Codifica um frame REDUZIDO para enviar à interface (mais leve e fluido)
            try:
                h, w = frame.shape[:2]
                target_w = 640
                if w > target_w:
                    scale = target_w / float(w)
                    display_frame = cv2.resize(frame, (int(w * scale), int(h * scale)))
                else:
                    display_frame = frame
                
                ret_encode, buffer = cv2.imencode('.jpg', display_frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                if ret_encode:
                    frame_base64 = base64.b64encode(buffer).decode('utf-8')
                    if self.callback_frame:
                        self.callback_frame(frame_base64)
            except Exception as e:
                print(f"[AVISO] Falha ao codificar frame para UI: {e}")
            
            # Alvo de ~20-24 FPS para feed da UI
            time.sleep(1 / 24)

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
            
            # Processa a cada 5 segundos para respostas mais rápidas
            if time.time() - ultima_verificacao >= 5:
                print(f"[PROCESSAMENTO] Timer de 5s atingido. Processando um frame...")
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
                    # Primeiro, verifica os alunos que estavam ausentes e agora estão presentes
                    for id_aluno in list(self.ausencias_consecutivas.keys()):
                        if id_aluno in alunos_presentes and self.ausencias_consecutivas.get(id_aluno, 0) >= 2:
                            # Aluno que estava ausente e agora está presente
                            mensagens.append(f"ALERTA: Aluno {id_aluno} retornou após {self.ausencias_consecutivas[id_aluno]} verificações de ausência.")
                            self.ausencias_consecutivas[id_aluno] = 0
                            self.ultima_presenca[id_aluno] = datetime.now()
                            
                            # Envia e-mail de retorno se um e-mail de ausência foi enviado anteriormente
                            if self.email_enviado.get(id_aluno, False):
                                self._enviar_email_retorno(id_aluno)
                                self.email_enviado[id_aluno] = False
                    
                    # Atualiza o status de presença/ausência
                    for id_aluno in self.nomes_referencia:
                        nome_aluno_str = str(id_aluno)
                        if nome_aluno_str in alunos_presentes:
                            # Se o aluno estava ausente e agora está presente
                            if self.ausencias_consecutivas.get(nome_aluno_str, 0) > 0:
                                mensagens.append(f"ALERTA: Aluno {nome_aluno_str} retornou após {self.ausencias_consecutivas[nome_aluno_str]} verificações de ausência.")
                                if self.email_enviado.get(nome_aluno_str, False):
                                    self._enviar_email_retorno(nome_aluno_str)
                                    self.email_enviado[nome_aluno_str] = False
                            self.ausencias_consecutivas[nome_aluno_str] = 0
                            self.ultima_presenca[nome_aluno_str] = datetime.now()
                        else:
                            # Incrementa o contador de ausências
                            self.ausencias_consecutivas[nome_aluno_str] = self.ausencias_consecutivas.get(nome_aluno_str, 0) + 1
                            
                            # Verifica se é necessário enviar e-mail de ausência
                            if self.ausencias_consecutivas[nome_aluno_str] == 2:  # Após 2 verificações ausentes
                                mensagens.append(f"ALERTA: Aluno {nome_aluno_str} ausente há {self.ausencias_consecutivas[nome_aluno_str]} verificações.")
                                self._enviar_email_ausencia(nome_aluno_str)
                                self.email_enviado[nome_aluno_str] = True
                
                if self.callback_mensagens and mensagens:
                    print("[PROCESSAMENTO] Enviando mensagens para a interface.")
                    self.callback_mensagens(mensagens)
                
                ultima_verificacao = time.time()

    def carregar_codificacoes_referencia(self):
        try:
            alunos = listar_alunos()
            with self.lock:
                # Inicializa os dicionários de rastreamento para cada aluno
                for aluno in alunos:
                    aluno_id = str(aluno['Id'])
                    self.ultima_presenca[aluno_id] = None
                    self.email_enviado[aluno_id] = False
                self.codificacoes_referencia = [np.array(aluno['codificacao_facial']) for aluno in alunos]
                self.nomes_referencia = [str(aluno['Id']) for aluno in alunos]
                self.ausencias_consecutivas = {str(aluno['Id']): 0 for aluno in alunos}
            print("[INFO] Codificações de referência recarregadas.")
        except Exception as e:
            msg = f"Erro ao carregar codificações: {e}"
            print(f"[ERRO] {msg}")
            if self.callback_mensagens:
                self.callback_mensagens([msg])

    def _enviar_email_ausencia(self, id_aluno):
        """Envia um e-mail de notificação de ausência para o responsável do aluno."""
        try:
            # Converter para string para evitar problemas com tipos
            id_aluno_str = str(id_aluno)
            responsavel = obter_responsavel_por_aluno(id_aluno_str)
            
            if not responsavel or 'email' not in responsavel or not responsavel['email']:
                print(f"[AVISO] Nenhum e-mail encontrado para o aluno {id_aluno_str}")
                return False
                
            assunto = f"Alerta de Ausência - Aluno {id_aluno_str}"
            mensagem = f"""
            <html>
                <body>
                    <p>Prezado Responsável,</p>
                    <p>O aluno {id_aluno_str} está ausente há 2 verificações consecutivas.</p>
                    <p>Por favor, entre em contato com a instituição para mais informações.</p>
                    <br>
                    <p>Atenciosamente,<br>Sistema de Monitoramento de Presença</p>
                </body>
            </html>
            """
            
            # Envia o e-mail usando o SMTP Service
            resultado = send_email(
                to_email=responsavel['email'],
                subject=assunto,
                body_text=mensagem.strip()
            )
            
            if resultado.get('success', False):
                print(f"[EMAIL] E-mail de ausência enviado para {responsavel['email']}")
                return True
            else:
                print(f"[ERRO] Falha ao enviar e-mail para {responsavel['email']}: {resultado.get('message', 'Erro desconhecido')}")
                return False
                
        except Exception as e:
            print(f"[ERRO] Ao tentar enviar e-mail de ausência: {str(e)}")
            return False

    def _enviar_email_retorno(self, id_aluno):
        """Envia um e-mail de notificação de retorno do aluno."""
        try:
            # Verifica se o ID do aluno está no dicionário de e-mails enviados
            if id_aluno not in self.email_enviado or not self.email_enviado[id_aluno]:
                print(f"[INFO] Nenhum e-mail de ausência anterior para o aluno {id_aluno}, ignorando retorno")
                return False
                
            id_aluno_str = str(id_aluno)
            responsavel = obter_responsavel_por_aluno(id_aluno_str)
            
            if not responsavel or 'email' not in responsavel or not responsavel['email']:
                print(f"[AVISO] Nenhum e-mail encontrado para o aluno {id_aluno_str}")
                return False
                
            assunto = f"Aluno {id_aluno_str} Retornou"
            mensagem = f"""
            <html>
                <body>
                    <p>Prezado Responsável,</p>
                    <p>O aluno {id_aluno_str} retornou após período de ausência.</p>
                    <br>
                    <p>Atenciosamente,<br>Sistema de Monitoramento de Presença</p>
                </body>
            </html>
            """
            
            # Envia o e-mail usando o SMTP Service
            resultado = send_email(
                to_email=responsavel['email'],
                subject=assunto,
                body_text=mensagem.strip()
            )
            
            if resultado.get('success', False):
                print(f"[EMAIL] E-mail de retorno enviado para {responsavel['email']}")
                return True
            else:
                print(f"[ERRO] Falha ao enviar e-mail de retorno para {responsavel['email']}: {resultado.get('message', 'Erro desconhecido')}")
                return False
                
        except Exception as e:
            print(f"[ERRO] Ao tentar enviar e-mail de retorno: {str(e)}")
            return False
    
    def verificar_presenca(self, frame):
        alunos_presentes = set()
        mensagens = []
        agora = datetime.now()
        timestamp = agora.strftime("%H:%M:%S")
        
        # Debug: Verificar se o frame é válido
        if frame is None or frame.size == 0:
            mensagens.append(f"[{timestamp}] Frame inválido ou vazio.")
            return list(alunos_presentes), mensagens
        
        print(f"[DEBUG] Frame shape: {frame.shape}")
        
        # Redimensionar frame para melhor performance
        frame_pequeno = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
        rgb_frame_pequeno = cv2.cvtColor(frame_pequeno, cv2.COLOR_BGR2RGB)

        with self.lock:
            codificacoes_ref = self.codificacoes_referencia
            nomes_ref = self.nomes_referencia

        print(f"[DEBUG] Alunos cadastrados: {len(codificacoes_ref) if codificacoes_ref else 0}")
        
        if not codificacoes_ref:
            mensagens.append(f"[{timestamp}] Nenhum aluno cadastrado para verificar.")
            return list(alunos_presentes), mensagens
            
        # Detectar faces no frame (pipeline com fallbacks)
        print("[DEBUG] Iniciando detecção de faces (HOG, upsample=0)...")
        locais_faces = face_recognition.face_locations(rgb_frame_pequeno, model="hog", number_of_times_to_upsample=0)
        print(f"[DEBUG] Faces detectadas (upsample=0): {len(locais_faces)}")

        usar_full_frame = False

        # Se não detectou, tentar com upsample=1 no frame reduzido
        if not locais_faces:
            print("[DEBUG] Tentando detecção com upsample=1 (reduzido)...")
            locais_faces = face_recognition.face_locations(rgb_frame_pequeno, model="hog", number_of_times_to_upsample=1)
            print(f"[DEBUG] Faces detectadas (upsample=1 reduzido): {len(locais_faces)}")

        # Fallback 1: usar Haar Cascade no frame reduzido
        if not locais_faces:
            print("[DEBUG] Fallback para Haar Cascade (reduzido)...")
            gray_small = cv2.cvtColor(frame_pequeno, cv2.COLOR_BGR2GRAY)
            detected = self._haar_cascade.detectMultiScale(gray_small, scaleFactor=1.05, minNeighbors=3, minSize=(40, 40))
            print(f"[DEBUG] Haar detections (reduzido): {len(detected)}")
            if len(detected) > 0:
                locais_faces = []
                for (x, y, w, h) in detected:
                    top = y
                    right = x + w
                    bottom = y + h
                    left = x
                    locais_faces.append((top, right, bottom, left))

        # Fallback 2: tentar no frame em tamanho real com HOG
        if not locais_faces:
            print("[DEBUG] Tentando detecção no frame completo (HOG, upsample=1)...")
            rgb_full = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            locais_full = face_recognition.face_locations(rgb_full, model="hog", number_of_times_to_upsample=1)
            print(f"[DEBUG] Faces detectadas no frame completo: {len(locais_full)}")
            if locais_full:
                usar_full_frame = True
                locais_faces = locais_full

        if not locais_faces:
            mensagens.append(f"[{timestamp}] Nenhum rosto detectado no frame.")
            return list(alunos_presentes), mensagens
        
        # Extrair codificações das faces detectadas
        print("[DEBUG] Extraindo codificações faciais...")
        if usar_full_frame:
            rgb_for_enc = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            codificacoes_faces = face_recognition.face_encodings(rgb_for_enc, locais_faces)
        else:
            codificacoes_faces = face_recognition.face_encodings(rgb_frame_pequeno, locais_faces)
        print(f"[DEBUG] Codificações extraídas: {len(codificacoes_faces)}")

        if not codificacoes_faces:
            mensagens.append(f"[{timestamp}] Falha ao extrair codificações faciais.")
            return list(alunos_presentes), mensagens

        # Verificar presenças
        for i, codificacao in enumerate(codificacoes_faces):
            print(f"[DEBUG] Comparando face {i+1}/{len(codificacoes_faces)}...")
            matches = face_recognition.compare_faces(codificacoes_ref, codificacao, tolerance=0.6)
            face_distances = face_recognition.face_distance(codificacoes_ref, codificacao)
            
            print(f"[DEBUG] Matches: {matches}")
            print(f"[DEBUG] Distâncias: {face_distances}")
            
            if True in matches:
                indice_match = matches.index(True)
                nome_identificado = nomes_ref[indice_match]
                distancia = face_distances[indice_match]
                print(f"[DEBUG] Match encontrado: {nome_identificado} (distância: {distancia:.3f})")
                
                if nome_identificado not in alunos_presentes:
                    alunos_presentes.add(nome_identificado)
                    mensagens.append(f"[{timestamp}] Presença confirmada: Aluno {nome_identificado}")
                    
                    # Verifica se é um retorno após ausência
                    if nome_identificado in self.ausencias_consecutivas and self.ausencias_consecutivas[nome_identificado] >= 2:
                        mensagens.append(f"[{timestamp}] ALERTA: Aluno {nome_identificado} retornou após {self.ausencias_consecutivas[nome_identificado]} verificações de ausência.")
                        self._enviar_email_retorno(nome_identificado)
                        self.email_enviado[nome_identificado] = False  # Reseta o status de e-mail enviado
                    
                    # Reseta o contador de ausências
                    with self.lock:
                        self.ausencias_consecutivas[nome_identificado] = 0
                        self.ultima_presenca[nome_identificado] = agora
            else:
                # Encontrar a menor distância para debug
                if len(face_distances) > 0:
                    min_distance = min(face_distances)
                    min_index = list(face_distances).index(min_distance)
                    closest_name = nomes_ref[min_index]
                    print(f"[DEBUG] Rosto não reconhecido. Mais próximo: {closest_name} (distância: {min_distance:.3f})")
                mensagens.append(f"[{timestamp}] Rosto não reconhecido detectado.")
        
        # Verificar ausências
        with self.lock:
            for aluno in self.nomes_referencia:
                aluno_str = str(aluno)
                if aluno_str not in self.ausencias_consecutivas:
                    self.ausencias_consecutivas[aluno_str] = 0
                if aluno_str not in alunos_presentes:
                    self.ausencias_consecutivas[aluno_str] = self.ausencias_consecutivas.get(aluno_str, 0) + 1
                else:
                    self.ausencias_consecutivas[aluno_str] = 0
                
                if self.ausencias_consecutivas[aluno_str] == 2:
                    mensagens.append(f"[{timestamp}] ALERTA: Aluno {aluno} ausente há {self.ausencias_consecutivas[aluno_str]} verificações consecutivas.")
                    if not self.email_enviado.get(aluno_str, False):
                        if self._enviar_email_ausencia(aluno_str):
                            self.email_enviado[aluno_str] = True
                        if not self.email_enviado.get(aluno, False):
                            if self._enviar_email_ausencia(aluno):
                                self.email_enviado[aluno] = True
                    
                    # Atualiza a última verificação de presença
                    if aluno not in self.ultima_presenca:
                        self.ultima_presenca[aluno] = agora
        
        return list(alunos_presentes), mensagens