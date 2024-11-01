# camera.py
import cv2
import numpy as np
import face_recognition  # Certifique-se de que a biblioteca face_recognition está instalada

class Camera:
    def __init__(self):
        """Inicializa a câmera e o classificador de rosto."""
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            print("Erro ao acessar a câmera.")
            raise Exception("Câmera não encontrada.")

        # Carrega o classificador de rosto em cascata da OpenCV
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

    def capture(self):
        """Captura uma imagem da câmera com detecção de rosto."""
        ret, frame = self.cap.read()  # Captura um quadro
        if ret:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)  # Converte para escala de cinza
            faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)

            # Desenha retângulos ao redor dos rostos detectados
            for (x, y, w, h) in faces:
                cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)  # Desenha um retângulo azul

            return frame  # Retorna a imagem com os rostos destacados
        return None

    def recognize_faces(self, frame, alunos):
        """Reconhece rostos no quadro atual e compara com os alunos cadastrados."""
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

        return detected_students

    def release(self):
        """Libera a câmera quando não for mais necessária."""
        self.cap.release()
