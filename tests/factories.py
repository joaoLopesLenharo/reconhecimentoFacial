"""
Factory classes para criação de dados de teste
"""
import factory
import numpy as np
import cv2
import base64
from faker import Faker
from datetime import datetime, timedelta
import json

fake = Faker('pt_BR')


class AlunoFactory(factory.Factory):
    """Factory para criar dados de alunos"""
    
    class Meta:
        model = dict
    
    Id = factory.Sequence(lambda n: 10000 + n)
    Nome = factory.LazyAttribute(lambda obj: fake.name())
    codificacao_facial = factory.LazyFunction(
        lambda: json.dumps(np.random.rand(128).tolist())
    )
    resp_telefone = factory.LazyAttribute(lambda obj: fake.phone_number())
    resp_email = factory.LazyAttribute(lambda obj: fake.email())


class ResponsavelFactory(factory.Factory):
    """Factory para criar dados de responsáveis"""
    
    class Meta:
        model = dict
    
    id = factory.Sequence(lambda n: n)
    id_aluno = factory.SubFactory(AlunoFactory)
    nome = factory.LazyAttribute(lambda obj: fake.name())
    telefone = factory.LazyAttribute(lambda obj: fake.phone_number())
    email = factory.LazyAttribute(lambda obj: fake.email())


class PresencaFactory(factory.Factory):
    """Factory para criar registros de presença"""
    
    class Meta:
        model = dict
    
    id_lancamento = factory.Sequence(lambda n: n)
    id_aluno = factory.SubFactory(AlunoFactory)
    local = factory.LazyAttribute(lambda obj: f"Sala {fake.random_int(1, 20)}")
    timestamp = factory.LazyAttribute(
        lambda obj: fake.date_time_between(start_date='-30d', end_date='now')
    )


class CameraFactory(factory.Factory):
    """Factory para criar dados de câmeras"""
    
    class Meta:
        model = dict
    
    id = factory.Sequence(lambda n: n)
    name = factory.LazyAttribute(lambda obj: f"Câmera {obj.id + 1}")
    status = factory.Iterator(['active', 'inactive', 'error'])
    location = factory.LazyAttribute(lambda obj: f"Entrada {fake.random_int(1, 5)}")


class ImageFactory:
    """Factory para criar imagens de teste"""
    
    @staticmethod
    def create_face_image(width=200, height=200):
        """Cria uma imagem simples com um rosto simulado"""
        image = np.zeros((height, width, 3), dtype=np.uint8)
        
        # Adiciona um círculo para simular um rosto
        center = (width // 2, height // 2)
        radius = min(width, height) // 4
        cv2.circle(image, center, radius, (255, 255, 255), -1)
        
        # Adiciona olhos
        eye_offset = radius // 3
        cv2.circle(image, (center[0] - eye_offset, center[1] - eye_offset), 
                  radius // 6, (0, 0, 0), -1)
        cv2.circle(image, (center[0] + eye_offset, center[1] - eye_offset), 
                  radius // 6, (0, 0, 0), -1)
        
        # Adiciona boca
        mouth_y = center[1] + eye_offset
        cv2.ellipse(image, (center[0], mouth_y), (eye_offset, eye_offset // 2), 
                   0, 0, 180, (0, 0, 0), 2)
        
        return image
    
    @staticmethod
    def create_base64_image(width=200, height=200):
        """Cria uma imagem em formato base64"""
        image = ImageFactory.create_face_image(width, height)
        _, buffer = cv2.imencode('.jpg', image)
        image_base64 = base64.b64encode(buffer).decode('utf-8')
        return f"data:image/jpeg;base64,{image_base64}"
    
    @staticmethod
    def create_random_image(width=640, height=480):
        """Cria uma imagem aleatória para testes"""
        return np.random.randint(0, 255, (height, width, 3), dtype=np.uint8)


class EmailConfigFactory(factory.Factory):
    """Factory para configurações de email"""
    
    class Meta:
        model = dict
    
    SMTP_SERVER = 'smtp.gmail.com'
    SMTP_PORT = 587
    SMTP_USERNAME = factory.LazyAttribute(lambda obj: fake.email())
    SMTP_PASSWORD = 'test_password'
    SMTP_SENDER_EMAIL = factory.LazyAttribute(lambda obj: obj.SMTP_USERNAME)
    SMTP_SENDER_NAME = 'Sistema de Monitoramento'


class TestDataBuilder:
    """Builder para criar conjuntos de dados de teste"""
    
    @staticmethod
    def create_student_with_responsible():
        """Cria um aluno com responsável"""
        aluno = AlunoFactory()
        responsavel = ResponsavelFactory(id_aluno=aluno['Id'])
        return aluno, responsavel
    
    @staticmethod
    def create_multiple_students(count=5):
        """Cria múltiplos alunos"""
        return [AlunoFactory() for _ in range(count)]
    
    @staticmethod
    def create_attendance_history(student_id, days=30):
        """Cria histórico de presença para um aluno"""
        presencas = []
        for i in range(days):
            date = datetime.now() - timedelta(days=i)
            # Simula presença aleatória (80% de chance de estar presente)
            if fake.boolean(chance_of_getting_true=80):
                presenca = PresencaFactory(
                    id_aluno=student_id,
                    timestamp=date
                )
                presencas.append(presenca)
        return presencas
    
    @staticmethod
    def create_camera_setup(count=3):
        """Cria configuração de múltiplas câmeras"""
        cameras = []
        for i in range(count):
            camera = CameraFactory(id=i)
            cameras.append(camera)
        return cameras
    
    @staticmethod
    def create_face_encodings(count=10):
        """Cria múltiplas codificações faciais"""
        encodings = []
        names = []
        for i in range(count):
            encoding = np.random.rand(128).tolist()
            name = fake.name()
            encodings.append(encoding)
            names.append(name)
        return encodings, names


class MockDataGenerator:
    """Gerador de dados mock para testes específicos"""
    
    @staticmethod
    def generate_socket_events():
        """Gera eventos de socket para testes"""
        return {
            'camera_ready': {
                'camera_id': 0,
                'status': 'ready',
                'timestamp': datetime.now().isoformat()
            },
            'camera_error': {
                'camera_id': 0,
                'error': 'Camera disconnected',
                'timestamp': datetime.now().isoformat()
            },
            'camera_frame': {
                'camera_id': 0,
                'frame': base64.b64encode(b'fake_frame_data').decode('utf-8'),
                'timestamp': datetime.now().isoformat()
            }
        }
    
    @staticmethod
    def generate_api_responses():
        """Gera respostas de API para testes"""
        return {
            'success_response': {
                'success': True,
                'message': 'Operação realizada com sucesso'
            },
            'error_response': {
                'success': False,
                'error': 'Erro simulado para teste'
            },
            'cameras_response': {
                'success': True,
                'cameras': [
                    {'id': 0, 'name': 'Câmera 1'},
                    {'id': 1, 'name': 'Câmera 2'}
                ]
            },
            'students_response': {
                'success': True,
                'alunos': TestDataBuilder.create_multiple_students(3)
            }
        }
    
    @staticmethod
    def generate_form_data():
        """Gera dados de formulário para testes"""
        return {
            'valid_student': {
                'id': 12345,
                'nome': 'João Silva',
                'frame': ImageFactory.create_base64_image(),
                'resp_telefone': '(11) 99999-9999',
                'resp_email': 'responsavel@email.com'
            },
            'invalid_student': {
                'id': '',  # ID inválido
                'nome': '',  # Nome vazio
                'frame': 'invalid_base64'  # Imagem inválida
            },
            'partial_student': {
                'id': 67890,
                'nome': 'Maria Santos'
                # frame ausente
            }
        }


# Fixtures pré-definidas para casos comuns
SAMPLE_STUDENTS = TestDataBuilder.create_multiple_students(5)
SAMPLE_CAMERAS = TestDataBuilder.create_camera_setup(3)
SAMPLE_FACE_ENCODINGS, SAMPLE_NAMES = TestDataBuilder.create_face_encodings(5)
SAMPLE_EMAIL_CONFIG = EmailConfigFactory()
SAMPLE_SOCKET_EVENTS = MockDataGenerator.generate_socket_events()
SAMPLE_API_RESPONSES = MockDataGenerator.generate_api_responses()
SAMPLE_FORM_DATA = MockDataGenerator.generate_form_data()
