"""
Configurações e fixtures compartilhadas para os testes
"""
import pytest
import os
import tempfile
import shutil
from unittest.mock import Mock, patch
import mysql.connector
from mysql.connector import Error
import cv2
import numpy as np
import base64
from flask import Flask
from flask_socketio import SocketIO

# Importa os módulos do projeto
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, socketio
from cadastro import DB_CONFIG
from reconhecimento import ReconhecimentoFacial

# Configuração do banco de dados de teste
TEST_DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'root',
    'database': 'test_mydb'
}

@pytest.fixture(scope='session')
def test_app():
    """Cria uma instância da aplicação Flask para testes"""
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test_secret_key'
    return app

@pytest.fixture(scope='session')
def test_client(test_app):
    """Cria um cliente de teste para a aplicação Flask"""
    return test_app.test_client()

@pytest.fixture(scope='session')
def test_socketio_client(test_app):
    """Cria um cliente SocketIO para testes"""
    return socketio.test_client(test_app)

@pytest.fixture(scope='function')
def mock_database():
    """Mock do banco de dados MySQL"""
    with patch('cadastro.conectar_mysql') as mock_connect:
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        yield mock_conn, mock_cursor

@pytest.fixture(scope='function')
def test_database():
    """Cria um banco de dados de teste real (use com cuidado)"""
    try:
        # Conecta ao MySQL e cria o banco de teste
        conn_init = mysql.connector.connect(
            host=TEST_DB_CONFIG['host'],
            user=TEST_DB_CONFIG['user'],
            password=TEST_DB_CONFIG['password']
        )
        cursor_init = conn_init.cursor()
        cursor_init.execute(f"DROP DATABASE IF EXISTS `{TEST_DB_CONFIG['database']}`")
        cursor_init.execute(f"CREATE DATABASE `{TEST_DB_CONFIG['database']}` DEFAULT CHARACTER SET utf8")
        cursor_init.close()
        conn_init.close()
        
        # Conecta ao banco de teste
        conn = mysql.connector.connect(**TEST_DB_CONFIG)
        
        # Cria as tabelas
        cursor = conn.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS alunos (
            Id INT NOT NULL,
            Nome VARCHAR(90) NOT NULL,
            codificacao_facial TEXT NOT NULL,
            PRIMARY KEY (Id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8;
        ''')
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS presencas (
            id_lancamento INT NOT NULL AUTO_INCREMENT,
            id_aluno INT NOT NULL,
            local VARCHAR(90) NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (id_lancamento),
            FOREIGN KEY (id_aluno) REFERENCES alunos(Id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8;
        ''')
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS responsavel (
            id_responsavel INT NOT NULL AUTO_INCREMENT,
            id_aluno INT NOT NULL,
            telefone VARCHAR(20) NOT NULL,
            email VARCHAR(100) NOT NULL,
            PRIMARY KEY (id_responsavel),
            UNIQUE KEY uq_responsavel_aluno (id_aluno),
            CONSTRAINT fk_responsavel_aluno FOREIGN KEY (id_aluno)
                REFERENCES alunos (Id)
                ON DELETE CASCADE ON UPDATE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8;
        ''')
        conn.commit()
        
        yield conn
        
        # Cleanup
        cursor.execute(f"DROP DATABASE IF EXISTS `{TEST_DB_CONFIG['database']}`")
        conn.close()
        
    except Error as e:
        pytest.skip(f"Não foi possível conectar ao banco de dados de teste: {e}")

@pytest.fixture
def mock_camera():
    """Mock da câmera OpenCV"""
    with patch('cv2.VideoCapture') as mock_cap:
        mock_instance = Mock()
        mock_cap.return_value = mock_instance
        
        # Simula um frame de teste
        test_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        mock_instance.read.return_value = (True, test_frame)
        mock_instance.isOpened.return_value = True
        
        yield mock_instance

@pytest.fixture
def sample_face_image():
    """Cria uma imagem de teste com um rosto simulado"""
    # Cria uma imagem simples de 200x200 pixels
    image = np.zeros((200, 200, 3), dtype=np.uint8)
    # Adiciona um retângulo para simular um rosto
    cv2.rectangle(image, (50, 50), (150, 150), (255, 255, 255), -1)
    return image

@pytest.fixture
def sample_face_encoding():
    """Cria uma codificação facial de teste"""
    return np.random.rand(128).tolist()

@pytest.fixture
def mock_face_recognition():
    """Mock do módulo face_recognition"""
    with patch('face_recognition.face_encodings') as mock_encodings, \
         patch('face_recognition.compare_faces') as mock_compare, \
         patch('face_recognition.face_distance') as mock_distance:
        
        # Simula uma codificação facial
        mock_encodings.return_value = [np.random.rand(128)]
        mock_compare.return_value = [True]
        mock_distance.return_value = [0.3]
        
        yield {
            'encodings': mock_encodings,
            'compare': mock_compare,
            'distance': mock_distance
        }

@pytest.fixture
def mock_email_service():
    """Mock do serviço de email"""
    with patch('smtp_service.send_email') as mock_send:
        mock_send.return_value = {'success': True, 'message': 'Email enviado com sucesso'}
        yield mock_send

@pytest.fixture
def reconhecimento_instance():
    """Cria uma instância do ReconhecimentoFacial para testes"""
    with patch('reconhecimento.listar_alunos', return_value=[]):
        instance = ReconhecimentoFacial()
        yield instance

@pytest.fixture
def temp_directory():
    """Cria um diretório temporário para testes"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

@pytest.fixture
def sample_student_data():
    """Dados de exemplo para um aluno"""
    return {
        'id': 12345,
        'nome': 'João Silva',
        'resp_telefone': '(11) 99999-9999',
        'resp_email': 'responsavel@email.com'
    }

@pytest.fixture
def base64_image():
    """Imagem em formato base64 para testes"""
    # Cria uma imagem simples
    image = np.zeros((100, 100, 3), dtype=np.uint8)
    cv2.rectangle(image, (25, 25), (75, 75), (255, 255, 255), -1)
    
    # Converte para base64
    _, buffer = cv2.imencode('.jpg', image)
    image_base64 = base64.b64encode(buffer).decode('utf-8')
    
    return f"data:image/jpeg;base64,{image_base64}"

# Configurações globais para os testes
def pytest_configure(config):
    """Configuração global do pytest"""
    # Desabilita warnings desnecessários
    import warnings
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    warnings.filterwarnings("ignore", category=PendingDeprecationWarning)

def pytest_collection_modifyitems(config, items):
    """Modifica os itens de teste coletados"""
    # Nenhuma modificação automática de marcadores necessária
    return
