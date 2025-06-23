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
        # Inicializar atributos básicos
        self.codificacoes_referencia = []
        self.nomes_referencia = []
        self.ausencias_consecutivas = {}
        self.monitoramento_ativo = False
        self.frame_queue = Queue(maxsize=2)
        self.ultima_verificacao = {}
        self.lock = threading.Lock()
        
        # Carregar codificações após inicializar todos os atributos
        self.carregar_codificacoes_referencia()
        
    def iniciar_monitoramento(self, camera_id=0):
        """Inicia o monitoramento assíncrono da câmera."""
        if self.monitoramento_ativo:
            return
            
        self.monitoramento_ativo = True
        self.frame_queue = Queue(maxsize=2)
        
        # Thread para captura de frames
        self.capture_thread = threading.Thread(
            target=self._capturar_frames,
            args=(camera_id,),
            daemon=True
        )
        
        # Thread para processamento de frames
        self.process_thread = threading.Thread(
            target=self._processar_frames,
            daemon=True
        )
        
        self.capture_thread.start()
        self.process_thread.start()
    
    def parar_monitoramento(self):
        """Para o monitoramento assíncrono."""
        self.monitoramento_ativo = False
        if hasattr(self, 'capture_thread'):
            self.capture_thread.join(timeout=1.0)
        if hasattr(self, 'process_thread'):
            self.process_thread.join(timeout=1.0)
    
    def _capturar_frames(self, camera_id):
        """Thread para captura contínua de frames."""
        try:
            if os.name == 'nt':
                cap = cv2.VideoCapture(camera_id, cv2.CAP_DSHOW)
            else:
                cap = cv2.VideoCapture(camera_id)
            
            if not cap.isOpened():
                if os.name == 'nt':
                    cap = cv2.VideoCapture(camera_id)
                    if not cap.isOpened():
                        raise RuntimeError(f"Não foi possível acessar a câmera {camera_id}")
                else:
                    raise RuntimeError(f"Não foi possível acessar a câmera {camera_id}")
            
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            
            while self.monitoramento_ativo:
                ret, frame = cap.read()
                if ret:
                    # Converter frame para base64
                    _, buffer = cv2.imencode('.jpg', frame)
                    frame_base64 = base64.b64encode(buffer).decode('utf-8')
                    
                    # Enviar frame para a interface
                    if hasattr(self, 'callback_frame'):
                        self.callback_frame(f'data:image/jpeg;base64,{frame_base64}')
                    
                    if not self.frame_queue.full():
                        self.frame_queue.put(frame)
                    else:
                        try:
                            self.frame_queue.get_nowait()
                            self.frame_queue.put(frame)
                        except:
                            pass
                time.sleep(0.033)  # ~30 FPS
                
        except Exception as e:
            print(f"Erro na captura de frames: {str(e)}")
            if hasattr(self, 'callback_mensagens'):
                self.callback_mensagens([f"Erro na captura de frames: {str(e)}"])
        finally:
            if 'cap' in locals():
                cap.release()
    
    def _processar_frames(self):
        """Thread para processamento de frames e verificação de presença."""
        ultima_verificacao = time.time()
        
        while self.monitoramento_ativo:
            try:
                # Verificar presença a cada 30 segundos
                if time.time() - ultima_verificacao >= 30:
                    if not self.frame_queue.empty():
                        frame = self.frame_queue.get()
                        alunos_presentes, mensagens = self.verificar_presenca(frame)
                        
                        # Atualizar ausências consecutivas
                        with self.lock:
                            for aluno in self.nomes_referencia:
                                if aluno in alunos_presentes:
                                    self.ausencias_consecutivas[aluno] = 0
                                else:
                                    self.ausencias_consecutivas[aluno] = self.ausencias_consecutivas.get(aluno, 0) + 1
                                    
                                    # Verificar se aluno está ausente há 2 verificações consecutivas
                                    if self.ausencias_consecutivas[aluno] >= 2:
                                        mensagens.append(f"ALERTA: Aluno {aluno} ausente em {self.ausencias_consecutivas[aluno]} verificações consecutivas!")
                        
                        # Emitir mensagens para a interface
                        if hasattr(self, 'callback_mensagens'):
                            self.callback_mensagens(mensagens)
                        
                        ultima_verificacao = time.time()
                
                time.sleep(1)  # Evitar uso excessivo de CPU
                
            except Exception as e:
                print(f"Erro no processamento de frames: {str(e)}")
                if hasattr(self, 'callback_mensagens'):
                    self.callback_mensagens([f"Erro no processamento de frames: {str(e)}"])
                time.sleep(5)  # Aguardar mais tempo em caso de erro
    
    def definir_callback_mensagens(self, callback):
        """Define a função de callback para mensagens."""
        self.callback_mensagens = callback
    
    def definir_callback_frame(self, callback):
        """Define a função de callback para frames da câmera."""
        self.callback_frame = callback

    def carregar_codificacoes_referencia(self):
        """Carrega as codificações faciais de referência do banco de dados MySQL."""
        try:
            alunos = listar_alunos()
            self.codificacoes_referencia = []
            self.nomes_referencia = []
            self.ausencias_consecutivas = {}
            for aluno in alunos:
                codificacao = aluno.get('codificacao_facial')
                if codificacao:
                    self.codificacoes_referencia.append(np.array(codificacao))
                    self.nomes_referencia.append(aluno['Id'])
                    self.ausencias_consecutivas[aluno['Id']] = 0
            return self.codificacoes_referencia, self.nomes_referencia
        except Exception as e:
            raise RuntimeError(f"Erro ao carregar codificações: {str(e)}")

    def verificar_presenca(self, frame):
        """Verifica a presença dos alunos em um frame."""
        alunos_presentes = []
        mensagens = []
        
        try:
            # Converter BGR para RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Detectar faces
            locais_faces = face_recognition.face_locations(frame_rgb)
            codificacoes_faces = face_recognition.face_encodings(frame_rgb, locais_faces)
            
            # Verificar cada face detectada
            for codificacao_face in codificacoes_faces:
                matches = face_recognition.compare_faces(self.codificacoes_referencia, codificacao_face)
                
                if True in matches:
                    indice_match = matches.index(True)
                    id_aluno = self.nomes_referencia[indice_match]
                    alunos_presentes.append(id_aluno)
                    
                    # Registrar presença
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    mensagens.append(f"[{timestamp}] Aluno {id_aluno} presente")
                else:
                    mensagens.append(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Face não reconhecida")
            
        except Exception as e:
            mensagens.append(f"Erro no reconhecimento facial: {str(e)}")
        
        return alunos_presentes, mensagens

    def capturar_frame_camera(self, camera_id=0):
        """
        Captura um frame da câmera especificada.
        
        Args:
            camera_id (int): ID da câmera a ser utilizada
            
        Returns:
            numpy.ndarray: Frame capturado da câmera
            
        Raises:
            RuntimeError: Se não for possível acessar a câmera
        """
        try:
            # No Windows, tentar primeiro com DirectShow
            if os.name == 'nt':
                cap = cv2.VideoCapture(camera_id, cv2.CAP_DSHOW)
            else:
                cap = cv2.VideoCapture(camera_id)
            
            if not cap.isOpened():
                # Se falhar com DirectShow, tentar com backend padrão
                if os.name == 'nt':
                    cap = cv2.VideoCapture(camera_id)
                    if not cap.isOpened():
                        raise RuntimeError(f"Não foi possível acessar a câmera {camera_id}")
                else:
                    raise RuntimeError(f"Não foi possível acessar a câmera {camera_id}")
            
            # Configurar resolução
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            
            # Capturar frame
            ret, frame = cap.read()
            cap.release()
            
            if not ret:
                raise RuntimeError("Falha ao capturar frame da câmera")
                
            return frame
        except Exception as e:
            raise RuntimeError(f"Erro ao acessar câmera {camera_id}: {str(e)}") 