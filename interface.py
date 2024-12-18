from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QScrollArea, QPushButton, QLineEdit, QHBoxLayout, QMessageBox
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QImage, QPixmap
from PyQt5 import QtCore

import cv2
import pyttsx3  # Adiciona a importação para narração de texto

from camera import Camera
from groq_api import GroQAPI
from database import Database

alunosPresentes = []


class ControlePresencaWindow(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.groq_api = GroQAPI()
        self.camera = Camera()
        self.init_ui()
        
        # Timer para atualizar a imagem da câmera
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(80)  # Atualiza a cada 30 ms para exibir vídeo ao vivo

    def init_ui(self):
        self.setWindowTitle("Controle de Presença")
        
        # Layout principal
        layout = QHBoxLayout()
        
        # Label para exibir a câmera
        self.camera_label = QLabel(self)
        layout.addWidget(self.camera_label)
    
        self.setLayout(layout)

    def update_frame(self):
        """Captura o quadro da câmera, realiza reconhecimento facial e exibe na interface."""
        frame = self.camera.capture()
        if frame is not None:
            # Converte a imagem de BGR (OpenCV) para RGB (Qt)
            rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            alunos = self.db.get_all_alunos()
            alunos_detectados = self.camera.recognize_faces(frame, alunos)

            # Adiciona círculo ao redor do rosto e exibe informações do aluno
            for aluno in alunos_detectados:
                if "id" in aluno and "nome" in aluno and "bbox" in aluno:
                    x, y, w, h = aluno["bbox"]
                    nome = aluno["nome"]
                    aluno_id = aluno["id"]
                    cv2.rectangle(rgb_image, (x, y), (x + w, y + h), (0, 255, 0), 2)
                    cv2.putText(rgb_image, nome, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                    if aluno['nome'] not in alunosPresentes:
                        self.db.record_presence(aluno_id, status="Presente")
                        alunosPresentes.append(aluno['nome'])
            
            # Converte para QImage e exibe
            qt_image = QImage(rgb_image.data, rgb_image.shape[1], rgb_image.shape[0], QImage.Format_RGB888)
            self.camera_label.setPixmap(QPixmap.fromImage(qt_image))

    def closeEvent(self, event):
        """Libera a câmera ao fechar a janela."""
        self.timer.stop()  # Para o timer
        self.camera.release()  # Libera a câmera
        super().closeEvent(event)



class CameraFeedbackWindow(QWidget):
    def __init__(self, camera, capture_callback):
        super().__init__()
        self.camera = camera
        self.capture_callback = capture_callback
        self.init_ui()
        
        # Timer para atualizar a imagem da câmera
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)  # Atualiza a cada 30 ms para exibir vídeo ao vivo

    def init_ui(self):
        self.setWindowTitle("Visor da Câmera")
        
        # Layout principal
        layout = QVBoxLayout()
        
        # Label para exibir a câmera
        self.camera_label = QLabel(self)
        layout.addWidget(self.camera_label)

        self.instruction_label = QLabel("Pressione Enter para capturar a foto")
        layout.addWidget(self.instruction_label)

        self.setLayout(layout)

    def update_frame(self):
        """Captura o quadro da câmera e exibe na interface."""
        frame = self.camera.capture()
        if frame is not None:
            # Converte a imagem de BGR (OpenCV) para RGB (Qt)
            rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Converte para QImage e exibe
            qt_image = QImage(rgb_image.data, rgb_image.shape[1], rgb_image.shape[0], QImage.Format_RGB888)
            self.camera_label.setPixmap(QPixmap.fromImage(qt_image))

    def keyPressEvent(self, event):
        """Detecta o pressionamento da tecla Enter para capturar a foto."""
        if event.key() == QtCore.Qt.Key_Return:
            # Captura a foto e exibe o alerta
            self.capture_callback()
            
            # Exibe um alerta informando que a foto foi capturada
            self.show_capture_alert()
            
            # Fecha a janela de feedback
            self.close()

    def show_capture_alert(self):
        """Exibe um alerta informando que a foto foi capturada."""
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setText("Foto capturada com sucesso!")
        msg.setWindowTitle("Captura de Foto")
        msg.exec_()

    def closeEvent(self, event):
        """Libera a câmera ao fechar a janela."""
        self.timer.stop()  # Para o timer
        self.camera.release()  # Libera a câmera
        super().closeEvent(event)


class MainWindow(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.groq_api = GroQAPI()
        self.camera = Camera()
        self.init_ui()
        self.captured_photo = None

    def init_ui(self):
        self.setWindowTitle("Sistema de Gestão de Alunos")
        layout = QVBoxLayout()
        
        self.label = QLabel("Sistema de Gestão de Alunos")
        self.name_input = QLineEdit(self)
        self.name_input.setPlaceholderText("Nome do Aluno")
        
        self.capture_button = QPushButton("Capturar Foto")
        self.cadastro_button = QPushButton("Cadastrar Aluno")
        self.presenca_button = QPushButton("Controle de Presença")
        self.list_aluno_button = QPushButton("Ver Alunos Cadastrados")
        
        self.capture_button.clicked.connect(self.open_camera_feedback)
        self.cadastro_button.clicked.connect(self.cadastrar_aluno)
        self.presenca_button.clicked.connect(self.open_controle_presenca)
        self.list_aluno_button.clicked.connect(self.show_aluno_list)

        layout.addWidget(self.label)
        layout.addWidget(self.name_input)
        layout.addWidget(self.capture_button)
        layout.addWidget(self.cadastro_button)
        layout.addWidget(self.presenca_button)
        layout.addWidget(self.list_aluno_button)
        
        self.setLayout(layout)

    def open_camera_feedback(self):
        """Abre a janela de feedback da câmera."""
        self.camera_feedback_window = CameraFeedbackWindow(self.camera, self.capture_photo)
        self.camera_feedback_window.show()

    def capture_photo(self):
        """Captura a imagem da câmera."""
        self.captured_photo = self.camera.capture()
        if self.captured_photo is not None:
            self.label.setText("Foto capturada com sucesso!")
        else:
            self.label.setText("Erro ao capturar foto.")

    def cadastrar_aluno(self):
        """Cadastra o aluno com nome e foto capturada."""
        nome = self.name_input.text()
        if self.captured_photo is not None and nome:
            _, buffer = cv2.imencode('.jpg', self.captured_photo)
            foto_blob = buffer.tobytes()
            descricao = self.groq_api.get_description(self.captured_photo)  # Substitua pela chamada real
            
            self.db.insert_aluno(nome, foto_blob, descricao)
            self.label.setText("Aluno cadastrado com sucesso!")
            self.name_input.clear()
        else:
            self.label.setText("Por favor, capture a foto e insira o nome.")

    def open_controle_presenca(self):
        """Abre a janela de controle de presença."""
        self.controle_presenca_window = ControlePresencaWindow(self.db)
        self.controle_presenca_window.show()

    def show_aluno_list(self):
        self.aluno_list_window = AlunoListWindow(self.db)
        self.aluno_list_window.show()

class AlunoListWindow(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.engine = pyttsx3.init()  # Inicializa o mecanismo de fala
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Alunos Cadastrados")
        self.setFixedSize(800, 600)
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        
        alunos = self.db.get_all_alunos()
        for aluno in alunos:
            name_label = QLabel(f"Nome: {aluno['nome']}")
            desc_label = QLabel(f"Descrição: {aluno['descricao']}")
            desc_label.setWordWrap(True)
            image_label = QLabel()
            image = QImage.fromData(aluno['foto'])
            image_label.setPixmap(QPixmap.fromImage(image))

            # Botão para narrar a descrição
            narrate_button = QPushButton("Ouvir Descrição")
            narrate_button.clicked.connect(lambda _, desc=aluno['descricao']: self.narrar_descricao(desc))
            
            layout.addWidget(name_label)
            layout.addWidget(desc_label)
            layout.addWidget(image_label)
            layout.addWidget(narrate_button)
        
        scroll_area.setWidget(content_widget)
        
        main_layout = QVBoxLayout()
        main_layout.addWidget(scroll_area)
        self.setLayout(main_layout)

    def narrar_descricao(self, descricao):
        """Faz a narração da descrição do aluno usando voz artificial."""
        self.engine.say(descricao)
        self.engine.runAndWait()

if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    db = Database()  # Instância do banco de dados
    main_window = MainWindow(db)
    main_window.show()
    sys.exit(app.exec_())
