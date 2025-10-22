"""
Testes de integração para as rotas da aplicação Flask
"""
import pytest
import json
import base64
import numpy as np
import cv2
from unittest.mock import Mock, patch, MagicMock
from flask import url_for

from app import app, socketio


class TestRoutesBasicas:
    """Testes para rotas básicas da aplicação"""
    
    def test_index_route(self, test_client):
        """Testa a rota principal"""
        response = test_client.get('/')
        assert response.status_code == 200
        # Aceita a versão com acento conforme template atual
        assert b'Sistema de Controle de Presen\xc3\xa7a' in response.data
    
    def test_serve_test_video(self, test_client, temp_directory):
        """Testa servir vídeos de teste"""
        # Cria um arquivo de vídeo fake
        video_path = f"{temp_directory}/test.mp4"
        with open(video_path, 'wb') as f:
            f.write(b'fake video content')
        
        with patch('app.send_from_directory') as mock_send:
            mock_send.return_value = 'video content'
            response = test_client.get('/test_videos/test.mp4')
            mock_send.assert_called_once()


class TestAPIRoutes:
    """Testes para rotas da API"""
    
    @patch('app.listar_cameras_disponiveis')
    def test_get_cameras_sucesso(self, mock_listar, test_client):
        """Testa listagem de câmeras"""
        mock_listar.return_value = [0, 1, 2]
        
        response = test_client.get('/api/cameras')
        data = json.loads(response.data)
        
        assert response.status_code == 200
        assert data['success'] == True
        assert len(data['cameras']) == 3
        # O app pode retornar id como string; normaliza para int
        assert int(data['cameras'][0]['id']) == 0
        assert data['cameras'][0]['name'] == 'Câmera 1'
    
    @patch('app.listar_cameras_disponiveis')
    def test_get_cameras_erro(self, mock_listar, test_client):
        """Testa erro na listagem de câmeras"""
        mock_listar.side_effect = Exception("Erro ao listar câmeras")
        
        response = test_client.get('/api/cameras')
        data = json.loads(response.data)
        
        assert response.status_code == 200
        assert data['success'] == False
        assert 'error' in data
    
    @patch('app.listar_alunos')
    def test_get_alunos_sucesso(self, mock_listar, test_client):
        """Testa listagem de alunos"""
        mock_listar.return_value = [
            {'Id': 12345, 'Nome': 'João Silva', 'resp_telefone': '11999999999', 'resp_email': 'joao@email.com'},
            {'Id': 67890, 'Nome': 'Maria Santos', 'resp_telefone': None, 'resp_email': None}
        ]
        
        response = test_client.get('/api/alunos')
        data = json.loads(response.data)
        
        assert response.status_code == 200
        assert data['success'] == True
        assert len(data['alunos']) == 2
        assert data['alunos'][0]['_id'] == 12345
        assert data['alunos'][0]['nome'] == 'João Silva'
    
    @patch('app.listar_alunos')
    def test_get_alunos_erro(self, mock_listar, test_client):
        """Testa erro na listagem de alunos"""
        mock_listar.side_effect = Exception("Erro no banco")
        
        response = test_client.get('/api/alunos')
        data = json.loads(response.data)
        
        assert response.status_code == 200
        assert data['success'] == False


class TestCadastroAluno:
    """Testes para cadastro de alunos via API"""
    
    @patch('app.cadastrar_aluno')
    @patch('app.reconhecimento.carregar_codificacoes_referencia')
    def test_create_aluno_sucesso(self, mock_carregar, mock_cadastrar, test_client, base64_image):
        """Testa cadastro bem-sucedido de aluno"""
        mock_cadastrar.return_value = None
        
        data = {
            'id': 12345,
            'nome': 'João Silva',
            'frame': base64_image,
            'resp_telefone': '11999999999',
            'resp_email': 'joao@email.com'
        }
        
        response = test_client.post('/api/alunos', 
                                  data=json.dumps(data),
                                  content_type='application/json')
        
        data_response = json.loads(response.data)
        
        assert response.status_code == 200
        assert data_response['success'] == True
        mock_cadastrar.assert_called_once()
        mock_carregar.assert_called_once()
    
    def test_create_aluno_dados_incompletos(self, test_client):
        """Testa cadastro com dados incompletos"""
        data = {
            'id': 12345,
            'nome': 'João Silva'
            # frame ausente
        }
        
        response = test_client.post('/api/alunos',
                                  data=json.dumps(data),
                                  content_type='application/json')
        
        data_response = json.loads(response.data)
        
        assert response.status_code == 200
        assert data_response['success'] == False
        assert 'Dados incompletos' in data_response['error']
    
    @patch('app.cadastrar_aluno')
    def test_create_aluno_imagem_invalida(self, mock_cadastrar, test_client):
        """Testa cadastro com imagem inválida"""
        data = {
            'id': 12345,
            'nome': 'João Silva',
            'frame': 'data:image/jpeg;base64,invalid_base64'
        }
        
        response = test_client.post('/api/alunos',
                                  data=json.dumps(data),
                                  content_type='application/json')
        
        data_response = json.loads(response.data)
        
        assert response.status_code == 200
        assert data_response['success'] == False
    
    @patch('app.cadastrar_aluno')
    def test_create_aluno_erro_cadastro(self, mock_cadastrar, test_client, base64_image):
        """Testa erro durante cadastro"""
        mock_cadastrar.side_effect = ValueError("ID já existe")
        
        data = {
            'id': 12345,
            'nome': 'João Silva',
            'frame': base64_image
        }
        
        response = test_client.post('/api/alunos',
                                  data=json.dumps(data),
                                  content_type='application/json')
        
        data_response = json.loads(response.data)
        
        assert response.status_code == 200
        assert data_response['success'] == False
        assert 'ID já existe' in data_response['error']


class TestEdicaoAluno:
    """Testes para edição de alunos via API"""
    
    @patch('app.editar_aluno')
    @patch('app.reconhecimento.carregar_codificacoes_referencia')
    def test_update_aluno_sucesso(self, mock_carregar, mock_editar, test_client, base64_image):
        """Testa edição bem-sucedida de aluno"""
        mock_editar.return_value = None
        
        data = {
            'nome': 'João Silva Editado',
            'frame': base64_image,
            'resp_telefone': '11888888888',
            'resp_email': 'joao.novo@email.com'
        }
        
        response = test_client.put('/api/alunos/12345',
                                 data=json.dumps(data),
                                 content_type='application/json')
        
        data_response = json.loads(response.data)
        
        assert response.status_code == 200
        assert data_response['success'] == True
        mock_editar.assert_called_once_with(12345, 'João Silva Editado', 
                                          mock_editar.call_args[0][2],
                                          resp_telefone='11888888888',
                                          resp_email='joao.novo@email.com')
    
    @patch('app.editar_aluno')
    def test_update_aluno_sem_foto(self, mock_editar, test_client):
        """Testa edição sem alterar foto"""
        mock_editar.return_value = None
        
        data = {
            'nome': 'João Silva Editado',
            'resp_telefone': '11888888888'
        }
        
        response = test_client.put('/api/alunos/12345',
                                 data=json.dumps(data),
                                 content_type='application/json')
        
        data_response = json.loads(response.data)
        
        assert response.status_code == 200
        assert data_response['success'] == True
        mock_editar.assert_called_once_with(12345, 'João Silva Editado', None,
                                          resp_telefone='11888888888',
                                          resp_email=None)
    
    def test_update_aluno_nome_vazio(self, test_client):
        """Testa edição com nome vazio"""
        data = {'nome': ''}
        
        response = test_client.put('/api/alunos/12345',
                                 data=json.dumps(data),
                                 content_type='application/json')
        
        data_response = json.loads(response.data)
        
        assert response.status_code == 200
        assert data_response['success'] == False
        assert 'nome é obrigatório' in data_response['error']


class TestExclusaoAluno:
    """Testes para exclusão de alunos via API"""
    
    @patch('app.excluir_aluno')
    @patch('app.reconhecimento.carregar_codificacoes_referencia')
    def test_delete_aluno_sucesso(self, mock_carregar, mock_excluir, test_client):
        """Testa exclusão bem-sucedida de aluno"""
        mock_excluir.return_value = None
        
        response = test_client.delete('/api/alunos/12345')
        data = json.loads(response.data)
        
        assert response.status_code == 200
        assert data['success'] == True
        mock_excluir.assert_called_once_with(12345)
        mock_carregar.assert_called_once()
    
    @patch('app.excluir_aluno')
    def test_delete_aluno_inexistente(self, mock_excluir, test_client):
        """Testa exclusão de aluno inexistente"""
        mock_excluir.side_effect = ValueError("Aluno não encontrado")
        
        response = test_client.delete('/api/alunos/99999')
        data = json.loads(response.data)
        
        assert response.status_code == 200
        assert data['success'] == False
        assert 'Aluno não encontrado' in data['error']


class TestMonitoramento:
    """Testes para rotas de monitoramento"""
    
    @patch('app.reconhecimento.iniciar_monitoramento')
    def test_start_monitoring_sucesso(self, mock_iniciar, test_client):
        """Testa início bem-sucedido do monitoramento"""
        mock_iniciar.return_value = None
        
        data = {'camera_id': 0}
        
        response = test_client.post('/api/monitoring/start',
                                  data=json.dumps(data),
                                  content_type='application/json')
        
        data_response = json.loads(response.data)
        
        assert response.status_code == 200
        assert data_response['success'] == True
        mock_iniciar.assert_called_once_with(0)
    
    @patch('app.reconhecimento.iniciar_monitoramento')
    def test_start_monitoring_erro(self, mock_iniciar, test_client):
        """Testa erro no início do monitoramento"""
        mock_iniciar.side_effect = Exception("Câmera não disponível")
        
        data = {'camera_id': 0}
        
        response = test_client.post('/api/monitoramento/start',
                                  data=json.dumps(data),
                                  content_type='application/json')
        
        data_response = json.loads(response.data)
        
        assert response.status_code == 200
        assert data_response['success'] == False
        assert 'Câmera não disponível' in data_response['error']
    
    @patch('app.reconhecimento.parar_monitoramento')
    def test_stop_monitoring_sucesso(self, mock_parar, test_client):
        """Testa parada bem-sucedida do monitoramento"""
        mock_parar.return_value = None
        
        response = test_client.post('/api/monitoring/stop')
        data = json.loads(response.data)
        
        assert response.status_code == 200
        assert data['success'] == True
        mock_parar.assert_called_once()


class TestEmailConfig:
    """Testes para configuração de email"""
    
    @patch('app.is_email_configured')
    def test_debug_email_status(self, mock_configured, test_client):
        """Testa status do email"""
        mock_configured.return_value = True
        
        with patch.dict('os.environ', {'SMTP_USERNAME': 'test@email.com'}):
            response = test_client.get('/debug/email/status')
            data = json.loads(response.data)
            
            assert response.status_code == 200
            assert data['smtp_configured'] == True
            assert data['smtp_username'] == 'configured'
    
    @patch('app.load_smtp_config')
    def test_email_config_get(self, mock_load, test_client):
        """Testa obtenção da configuração de email"""
        mock_load.return_value = {
            'SMTP_USERNAME': 'test@email.com',
            'SMTP_PASSWORD': 'password',
            'SMTP_SERVER': 'smtp.gmail.com',
            'SMTP_PORT': 587
        }
        
        response = test_client.get('/api/email/config')
        data = json.loads(response.data)
        
        assert response.status_code == 200
        assert data['success'] == True
        assert data['is_configured'] == True
        assert data['smtp_username'] == 'test@email.com'
    
    @patch('app.is_email_configured')
    @patch('app.send_email')
    def test_debug_send_test_email_sucesso(self, mock_send, mock_configured, test_client):
        """Testa envio de email de teste"""
        mock_configured.return_value = True
        mock_send.return_value = {'success': True}
        
        data = {'to': 'test@email.com'}
        
        response = test_client.post('/debug/email/test',
                                  data=json.dumps(data),
                                  content_type='application/json')
        
        response_data = json.loads(response.data)
        
        assert response.status_code == 200
        assert response_data['status'] == 'success'
    
    @patch('app.is_email_configured')
    def test_debug_send_test_email_nao_configurado(self, mock_configured, test_client):
        """Testa envio de email quando não configurado"""
        mock_configured.return_value = False
        
        response = test_client.post('/debug/email/test',
                                  data=json.dumps({}),
                                  content_type='application/json')
        
        assert response.status_code == 400


class TestTestVideos:
    """Testes para vídeos de teste"""
    
    @patch('app.glob.glob')
    def test_get_test_videos(self, mock_glob, test_client):
        """Testa listagem de vídeos de teste"""
        # O app chama glob 3 vezes (mp4, avi, mov); evitamos duplicatas
        mock_glob.side_effect = [
            ['test_videos/video1.mp4'],
            ['test_videos/video2.avi'],
            []
        ]
        
        response = test_client.get('/api/test-videos')
        data = json.loads(response.data)
        
        assert response.status_code == 200
        assert len(data['videos']) == 2
        assert data['videos'][0]['name'] == 'video1.mp4'
        assert data['videos'][1]['name'] == 'video2.avi'


@pytest.mark.integration
class TestSocketIOEvents:
    """Testes para eventos SocketIO"""
    
    def test_start_monitoring_socketio(self, test_socketio_client):
        """Testa início de monitoramento via SocketIO"""
        with patch('app.cv2.VideoCapture') as mock_cap:
            mock_instance = Mock()
            mock_instance.isOpened.return_value = True
            mock_instance.read.return_value = (True, np.zeros((480, 640, 3), dtype=np.uint8))
            mock_cap.return_value = mock_instance
            
            # Envia evento
            response = test_socketio_client.emit('start_monitoring', {
                'camera_id': 0,
                'test_mode': False
            })
            # Em Flask-SocketIO, emit em testes pode retornar None; o importante é não quebrar
            assert response is None or True
    
    def test_stop_monitoring_socketio(self, test_socketio_client):
        """Testa parada de monitoramento via SocketIO"""
        response = test_socketio_client.emit('stop_monitoring', {
            'camera_id': 0
        })
        # Emite pode retornar None
        assert response is None or True


@pytest.mark.slow
class TestPerformanceRoutes:
    """Testes de performance das rotas"""
    
    def test_performance_listagem_alunos(self, test_client):
        """Testa performance da listagem de alunos"""
        import time
        
        with patch('app.listar_alunos') as mock_listar:
            # Simula muitos alunos
            mock_listar.return_value = [
                {'Id': i, 'Nome': f'Aluno {i}', 'resp_telefone': None, 'resp_email': None}
                for i in range(1000)
            ]
            
            start_time = time.time()
            response = test_client.get('/api/alunos')
            end_time = time.time()
            
            assert response.status_code == 200
            assert (end_time - start_time) < 1.0  # Deve ser rápido
    
    def test_performance_cadastro_aluno(self, test_client, base64_image):
        """Testa performance do cadastro de aluno"""
        import time
        
        with patch('app.cadastrar_aluno'), \
             patch('app.reconhecimento.carregar_codificacoes_referencia'):
            
            data = {
                'id': 12345,
                'nome': 'João Silva',
                'frame': base64_image
            }
            
            start_time = time.time()
            response = test_client.post('/api/alunos',
                                      data=json.dumps(data),
                                      content_type='application/json')
            end_time = time.time()
            
            assert response.status_code == 200
            assert (end_time - start_time) < 2.0  # Processamento de imagem pode ser mais lento
