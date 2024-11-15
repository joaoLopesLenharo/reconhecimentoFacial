import cv2
import numpy as np
import face_recognition  # Certifique-se de que a biblioteca face_recognition está instalada
import threading


class Camera:
    def __init__(self, camera_index=0):
        """Inicializa a câmera e configura os parâmetros."""
        self.cap = cv2.VideoCapture(camera_index)
        if not self.cap.isOpened():
            print("Erro ao acessar a câmera.")
            raise Exception("Câmera não encontrada.")
        
        # Configura resolução padrão para reduzir o processamento
        self.set_resolution(640, 480)
        
        # Carrega o classificador de rosto em cascata da OpenCV
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        
        # Controle de threading
        self.lock = threading.Lock()
        self.last_recognized_faces = []  # Cache para os últimos rostos reconhecidos

    def set_resolution(self, width, height):
        """Configura a resolução da câmera."""
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

    def capture(self):
        """Captura uma imagem da câmera."""
        ret, frame = self.cap.read()
        if ret:
            return frame  # Retorna a imagem capturada
        return None

    def recognize_faces(self, frame, alunos):
        """
        Reconhece rostos no quadro atual e compara com os alunos cadastrados.
        Executa o processamento de maneira segura com threading.
        """
        if self.lock.locked():
            # Se outro processo de reconhecimento está rodando, retorna o último resultado
            return self.last_recognized_faces

        # Bloqueia o recurso para processamento
        self.lock.acquire()

        try:
            detected_students = []
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            face_locations = face_recognition.face_locations(rgb_frame)
            face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

            for face_encoding, (top, right, bottom, left) in zip(face_encodings, face_locations):
                for aluno in alunos:
                    # Decodifica a imagem armazenada em bytes para formato do OpenCV
                    aluno_face = cv2.imdecode(np.frombuffer(aluno['foto'], np.uint8), cv2.IMREAD_COLOR)
                    if aluno_face is None:
                        continue

                    # Codifica a imagem do aluno
                    aluno_face_encoding = face_recognition.face_encodings(aluno_face)
                    if not aluno_face_encoding:
                        continue

                    # Calcula a distância e verifica fidelidade
                    distancia = face_recognition.face_distance(aluno_face_encoding, face_encoding)[0]
                    if distancia < 0.4:  # 80% de fidelidade corresponde a uma distância de até 0.4
                        detected_students.append({
                            "id": aluno['id'],
                            "nome": aluno['nome'],
                            "bbox": (left, top, right - left, bottom - top)
                        })
                        break  # Aluno encontrado, não precisa continuar

            # Atualiza os rostos reconhecidos no cache
            self.last_recognized_faces = detected_students
            return detected_students

        finally:
            # Libera o bloqueio após o processamento
            self.lock.release()

    def release(self):
        """Libera a câmera quando não for mais necessária."""
        self.cap.release()
