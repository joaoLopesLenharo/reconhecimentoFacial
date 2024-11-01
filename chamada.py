#chamada.py
import cv2
import numpy as np
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QApplication
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import QTimer
import face_recognition  # Certifique-se de que a biblioteca face_recognition está instalada
from database import Database  # Certifique-se de que você tem um arquivo database.py para gerenciar a conexão com o banco de dados

class Chamada(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.init_ui()
        self.capture = cv2.VideoCapture(0)
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)  # Atualiza a cada 30 ms

    def init_ui(self):
        self.setWindowTitle("Chamada de Alunos")
        self.layout = QVBoxLayout()
        self.label = QLabel("Chamada de Alunos")
        self.video_label = QLabel()
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.video_label)
        self.setLayout(self.layout)

    def update_frame(self):
        ret, frame = self.capture.read()
        if ret:
            # Identifica os rostos no quadro atual
            self.recognize_faces(frame)
            # Converte a imagem BGR para RGB
            rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_image.shape
            bytes_per_line = ch * w
            convert_to_Qt_format = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
            self.video_label.setPixmap(QPixmap.fromImage(convert_to_Qt_format))

    def recognize_faces(self, frame):
        alunos = self.db.get_all_alunos()  # Obtém todos os alunos do banco de dados
        if alunos:
            # Convertemos a imagem para escala de cinza para detecção facial
            gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            face_locations = face_cascade.detectMultiScale(gray_frame, scaleFactor=1.1, minNeighbors=5)

            for (x, y, w, h) in face_locations:
                face_image = frame[y:y + h, x:x + w]
                # Simulando o reconhecimento facial
                for aluno in alunos:
                    aluno_face = cv2.imdecode(np.frombuffer(aluno['foto'], np.uint8), cv2.IMREAD_COLOR)

                    # Aqui você deve implementar a lógica de comparação
                    if self.compare_faces(face_image, aluno_face):
                        # Desenha um retângulo ao redor do rosto
                        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                        # Adiciona o nome e a ancestralidade abaixo do rosto
                        cv2.putText(frame, f"{aluno['nome']} - {aluno['ancestralidade']}", 
                                    (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
                        self.db.record_presence(aluno['id'])  # Registra presença
                        print(f"Presença registrada para: {aluno['nome']}")  # Impressão no terminal
                        break  # Se o aluno for encontrado, não precisamos continuar a busca

    def compare_faces(self, face_image, aluno_face):
        aluno_face_encoding = face_recognition.face_encodings(aluno_face)
        if len(aluno_face_encoding) == 0:
            return False

        aluno_face_encoding = aluno_face_encoding[0]

        face_image_encoding = face_recognition.face_encodings(face_image)
        if len(face_image_encoding) == 0:
            return False

        face_image_encoding = face_image_encoding[0]

        # Calcula a distância entre as duas codificações
        distance = face_recognition.face_distance([aluno_face_encoding], face_image_encoding)[0]
        
        # Define a precisão mínima como 80%
        threshold = 0.45  # Aproximadamente equivalente a 80% de fidelidade
        
        # Retorna True se a correspondência atender ao limite de fidelidade mínima
        return distance <= threshold

    def closeEvent(self, event):
        self.capture.release()  # Libera a captura da câmera
        event.accept()

def start_chamada(db):
    app = QApplication([])
    chamada_window = Chamada(db)
    chamada_window.show()
    app.exec_()
