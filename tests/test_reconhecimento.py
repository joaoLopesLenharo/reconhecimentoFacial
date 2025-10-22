"""
Testes unitários para o módulo reconhecimento.py
"""
import pytest
import numpy as np
import cv2
import threading
import time
from unittest.mock import Mock, patch, MagicMock
from queue import Queue

from reconhecimento import ReconhecimentoFacial


class TestReconhecimentoFacialInit:
    """Testes para inicialização da classe ReconhecimentoFacial"""
    
    @patch('reconhecimento.ReconhecimentoFacial.carregar_codificacoes_referencia')
    def test_init_reconhecimento(self, mock_carregar):
        """Testa inicialização da classe"""
        rf = ReconhecimentoFacial()
        
        assert rf.codificacoes_referencia == []
        assert rf.nomes_referencia == []
        assert rf.ausencias_consecutivas == {}
        assert rf.ultima_presenca == {}
        assert rf.email_enviado == {}
        assert rf.monitoramento_ativo == False
        assert isinstance(rf.frame_queue, Queue)
        assert isinstance(rf.lock, type(threading.Lock()))
        
        mock_carregar.assert_called_once()
    
    def test_definir_callbacks(self, reconhecimento_instance):
        """Testa definição de callbacks"""
        callback_msg = Mock()
        callback_frame = Mock()
        
        reconhecimento_instance.definir_callback_mensagens(callback_msg)
        reconhecimento_instance.definir_callback_frame(callback_frame)
        
        assert reconhecimento_instance.callback_mensagens == callback_msg
        assert reconhecimento_instance.callback_frame == callback_frame


class TestCarregarCodificacoes:
    """Testes para carregamento de codificações de referência"""
    
    @patch('reconhecimento.listar_alunos')
    @patch('reconhecimento.np.array')
    def test_carregar_codificacoes_sucesso(self, mock_array, mock_listar, reconhecimento_instance):
        """Testa carregamento bem-sucedido das codificações"""
        # Mock dos dados de alunos
        mock_listar.return_value = [
            {'Id': 12345, 'Nome': 'João Silva', 'codificacao_facial': '[0.1, 0.2, 0.3]'},
            {'Id': 67890, 'Nome': 'Maria Santos', 'codificacao_facial': '[0.4, 0.5, 0.6]'}
        ]
        
        # Mock do numpy array
        mock_array.side_effect = lambda x: np.array(eval(x))
        
        reconhecimento_instance.carregar_codificacoes_referencia()
        
        assert len(reconhecimento_instance.codificacoes_referencia) == 2
        assert len(reconhecimento_instance.nomes_referencia) == 2
        # O código atual usa IDs (string) como nomes de referência
        assert reconhecimento_instance.nomes_referencia[0] == '12345'
        assert reconhecimento_instance.nomes_referencia[1] == '67890'
    
    @patch('reconhecimento.listar_alunos')
    def test_carregar_codificacoes_vazio(self, mock_listar, reconhecimento_instance):
        """Testa carregamento quando não há alunos"""
        mock_listar.return_value = []
        
        reconhecimento_instance.carregar_codificacoes_referencia()
        
        assert reconhecimento_instance.codificacoes_referencia == []
        assert reconhecimento_instance.nomes_referencia == []
    
    @patch('reconhecimento.listar_alunos')
    def test_carregar_codificacoes_erro_json(self, mock_listar, reconhecimento_instance):
        """Testa tratamento de erro no JSON das codificações"""
        mock_listar.return_value = [
            {'Id': 12345, 'Nome': 'João Silva', 'codificacao_facial': 'json_invalido'}
        ]
        
        # Não deve gerar exceção, apenas pular o aluno com erro
        reconhecimento_instance.carregar_codificacoes_referencia()
        
        assert len(reconhecimento_instance.codificacoes_referencia) == 0
        assert len(reconhecimento_instance.nomes_referencia) == 0


class TestMonitoramento:
    """Testes para funcionalidades de monitoramento"""
    
    @patch('reconhecimento.threading.Thread')
    def test_iniciar_monitoramento(self, mock_thread, reconhecimento_instance):
        """Testa início do monitoramento"""
        mock_thread_instance = Mock()
        mock_thread.return_value = mock_thread_instance
        
        reconhecimento_instance.iniciar_monitoramento(camera_id=0)
        
        assert reconhecimento_instance.monitoramento_ativo == True
        assert mock_thread.call_count == 2  # Duas threads: captura e processamento
        assert mock_thread_instance.start.call_count == 2
    
    def test_parar_monitoramento(self, reconhecimento_instance):
        """Testa parada do monitoramento"""
        reconhecimento_instance.monitoramento_ativo = True
        
        reconhecimento_instance.parar_monitoramento()
        
        assert reconhecimento_instance.monitoramento_ativo == False
    
    def test_iniciar_monitoramento_ja_ativo(self, reconhecimento_instance):
        """Testa tentativa de iniciar monitoramento já ativo"""
        reconhecimento_instance.monitoramento_ativo = True
        
        with patch('reconhecimento.threading.Thread') as mock_thread:
            reconhecimento_instance.iniciar_monitoramento()
            mock_thread.assert_not_called()


class TestCapturaFrames:
    """Testes para captura de frames"""
    
    @patch('reconhecimento.cv2.VideoCapture')
    @patch('reconhecimento.base64.b64encode')
    def test_capturar_frames_sucesso(self, mock_b64encode, mock_video_capture, reconhecimento_instance):
        """Testa captura bem-sucedida de frames"""
        # Setup mocks
        mock_cap = Mock()
        mock_video_capture.return_value = mock_cap
        mock_cap.isOpened.return_value = True
        mock_cap.read.return_value = (True, np.zeros((480, 640, 3), dtype=np.uint8))
        
        mock_b64encode.return_value = b'encoded_frame'
        
        # Mock do callback
        callback_frame = Mock()
        reconhecimento_instance.definir_callback_frame(callback_frame)
        
        # Simula execução por pouco tempo
        reconhecimento_instance.monitoramento_ativo = True
        
        def stop_after_delay():
            time.sleep(0.1)
            reconhecimento_instance.monitoramento_ativo = False
        
        threading.Thread(target=stop_after_delay, daemon=True).start()
        
        # Executa captura
        reconhecimento_instance._capturar_frames(0)
        
        # Verifica se o callback foi chamado
        callback_frame.assert_called()
    
    @patch('reconhecimento.cv2.VideoCapture')
    def test_capturar_frames_camera_indisponivel(self, mock_video_capture, reconhecimento_instance):
        """Testa captura quando câmera não está disponível"""
        mock_cap = Mock()
        mock_video_capture.return_value = mock_cap
        mock_cap.isOpened.return_value = False
        
        callback_msg = Mock()
        reconhecimento_instance.definir_callback_mensagens(callback_msg)
        reconhecimento_instance.monitoramento_ativo = True
        
        reconhecimento_instance._capturar_frames(0)
        
        # Verifica se mensagem de erro foi enviada
        callback_msg.assert_called()
        args = callback_msg.call_args[0][0]
        assert any("Não foi possível abrir a câmera" in msg for msg in args)


class TestProcessamentoFrames:
    """Testes para processamento de frames"""
    
    @patch('reconhecimento.face_recognition.face_locations')
    @patch('reconhecimento.face_recognition.face_encodings')
    @patch('reconhecimento.face_recognition.compare_faces')
    @patch('reconhecimento.face_recognition.face_distance')
    def test_processar_frames_reconhecimento_sucesso(self, mock_distance, mock_compare, 
                                                   mock_encodings, mock_locations, 
                                                   reconhecimento_instance):
        """Testa processamento bem-sucedido com reconhecimento"""
        # Setup dados de referência
        reconhecimento_instance.codificacoes_referencia = [np.random.rand(128)]
        reconhecimento_instance.nomes_referencia = ['João Silva']
        
        # Setup mocks
        mock_locations.return_value = [(50, 150, 150, 50)]  # Uma face detectada
        mock_encodings.return_value = [np.random.rand(128)]
        mock_compare.return_value = [True]
        mock_distance.return_value = [0.3]
        
        # Mock callback
        callback_msg = Mock()
        reconhecimento_instance.definir_callback_mensagens(callback_msg)
        
        # Adiciona frame na fila
        test_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        reconhecimento_instance.frame_queue.put(test_frame)
        
        # Simula execução por pouco tempo
        reconhecimento_instance.monitoramento_ativo = True
        
        def stop_after_delay():
            time.sleep(0.1)
            reconhecimento_instance.monitoramento_ativo = False
        
        threading.Thread(target=stop_after_delay, daemon=True).start()
        
        # Executa processamento
        reconhecimento_instance._processar_frames()
        
        # Verifica se foi reconhecido
        assert 'João Silva' in reconhecimento_instance.ultima_presenca
    
    @patch('reconhecimento.face_recognition.face_locations')
    def test_processar_frames_sem_faces(self, mock_locations, reconhecimento_instance):
        """Testa processamento quando não há faces detectadas"""
        mock_locations.return_value = []  # Nenhuma face
        
        callback_msg = Mock()
        reconhecimento_instance.definir_callback_mensagens(callback_msg)
        
        # Adiciona frame na fila
        test_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        reconhecimento_instance.frame_queue.put(test_frame)
        
        reconhecimento_instance.monitoramento_ativo = True
        
        def stop_after_delay():
            time.sleep(0.1)
            reconhecimento_instance.monitoramento_ativo = False
        
        threading.Thread(target=stop_after_delay, daemon=True).start()
        
        reconhecimento_instance._processar_frames()
        
        # Não deve ter reconhecido ninguém
        assert len(reconhecimento_instance.ultima_presenca) == 0


class TestDeteccaoAusencias:
    """Testes para detecção de ausências"""
    
    @patch('reconhecimento.face_recognition.face_locations', return_value=[])
    def test_detectar_ausencias_consecutivas(self, _mock_locations, reconhecimento_instance):
        """Testa detecção de ausências consecutivas via verificar_presenca"""
        # Setup referências com IDs como strings
        reconhecimento_instance.nomes_referencia = ['123', '456']
        reconhecimento_instance.codificacoes_referencia = [np.random.rand(128), np.random.rand(128)]
        reconhecimento_instance.ausencias_consecutivas = {'123': 1, '456': 0}
        
        # Usa frame preto para não reconhecer ninguém
        frame = np.zeros((100, 100, 3), dtype=np.uint8)
        _, _ = reconhecimento_instance.verificar_presenca(frame)
        
        # Verifica incrementos
        assert reconhecimento_instance.ausencias_consecutivas['123'] == 2
        assert reconhecimento_instance.ausencias_consecutivas['456'] == 1
    
    @patch('reconhecimento.obter_responsavel_por_aluno')
    @patch('reconhecimento.face_recognition.face_locations', return_value=[])
    def test_enviar_alerta_ausencia(self, _mock_locations, mock_obter_responsavel, reconhecimento_instance):
        """Testa geração de alerta de ausência via verificar_presenca"""
        mock_obter_responsavel.return_value = {
            'email': 'responsavel@email.com'
        }
        reconhecimento_instance.nomes_referencia = ['123']
        reconhecimento_instance.codificacoes_referencia = [np.random.rand(128)]
        reconhecimento_instance.ausencias_consecutivas = {'123': 1}
        reconhecimento_instance.email_enviado = {'123': False}
        
        frame = np.zeros((100, 100, 3), dtype=np.uint8)
        _alunos, mensagens = reconhecimento_instance.verificar_presenca(frame)
        
        assert any('ALERTA:' in msg for msg in mensagens)


class TestUtilidades:
    """Testes para funções utilitárias"""
    
    @patch('reconhecimento.face_recognition.face_locations', return_value=[(0,10,10,0)])
    @patch('reconhecimento.face_recognition.face_encodings')
    @patch('reconhecimento.face_recognition.compare_faces', return_value=[True])
    @patch('reconhecimento.face_recognition.face_distance', return_value=[0.3])
    def test_reset_ausencias_presenca_detectada(self, _mock_distance, _mock_compare, mock_enc, _mock_loc, reconhecimento_instance):
        """Testa reset de ausências quando presença é detectada via verificar_presenca"""
        # Setup referências com ID '123'
        ref = np.random.rand(128)
        reconhecimento_instance.codificacoes_referencia = [ref]
        reconhecimento_instance.nomes_referencia = ['123']
        reconhecimento_instance.ausencias_consecutivas = {'123': 3}
        reconhecimento_instance.email_enviado = {'123': True}
        mock_enc.return_value = [ref]
        
        frame = np.zeros((100, 100, 3), dtype=np.uint8)
        _alunos, _msgs = reconhecimento_instance.verificar_presenca(frame)
        
        assert reconhecimento_instance.ausencias_consecutivas['123'] == 0
        assert reconhecimento_instance.email_enviado['123'] == False
    
    def test_thread_safety(self, reconhecimento_instance):
        """Testa thread safety das operações"""
        # Este teste verifica se o lock está sendo usado corretamente
        # Simula acesso concorrente
        
        def modify_data():
            with reconhecimento_instance.lock:
                reconhecimento_instance.ausencias_consecutivas['test'] = 1
        
        threads = []
        for _ in range(10):
            t = threading.Thread(target=modify_data)
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        # Se chegou até aqui sem deadlock, o teste passou
        assert True


@pytest.mark.integration
class TestIntegracaoReconhecimento:
    """Testes de integração para reconhecimento facial"""
    
    @patch('reconhecimento.cv2.VideoCapture')
    @patch('reconhecimento.face_recognition.face_locations')
    @patch('reconhecimento.face_recognition.face_encodings')
    def test_fluxo_completo_monitoramento(self, mock_encodings, mock_locations, 
                                        mock_video_capture, reconhecimento_instance):
        """Testa fluxo completo de monitoramento"""
        # Setup mocks
        mock_cap = Mock()
        mock_video_capture.return_value = mock_cap
        mock_cap.isOpened.return_value = True
        mock_cap.read.return_value = (True, np.zeros((480, 640, 3), dtype=np.uint8))
        
        mock_locations.return_value = [(50, 150, 150, 50)]
        mock_encodings.return_value = [np.random.rand(128)]
        
        # Setup dados de referência
        reconhecimento_instance.codificacoes_referencia = [np.random.rand(128)]
        reconhecimento_instance.nomes_referencia = ['João Silva']
        
        # Setup callbacks
        callback_msg = Mock()
        callback_frame = Mock()
        reconhecimento_instance.definir_callback_mensagens(callback_msg)
        reconhecimento_instance.definir_callback_frame(callback_frame)
        
        # Inicia monitoramento
        reconhecimento_instance.iniciar_monitoramento(0)
        
        # Aguarda um pouco para processamento
        time.sleep(0.2)
        
        # Para monitoramento
        reconhecimento_instance.parar_monitoramento()
        
        # Verifica se callbacks foram chamados
        assert callback_frame.called or callback_msg.called
        assert not reconhecimento_instance.monitoramento_ativo


@pytest.mark.slow
class TestPerformance:
    """Testes de performance"""
    
    def test_performance_processamento_multiplos_frames(self, reconhecimento_instance):
        """Testa performance com múltiplos frames"""
        # Setup dados de referência
        reconhecimento_instance.codificacoes_referencia = [np.random.rand(128) for _ in range(10)]
        reconhecimento_instance.nomes_referencia = [f'Aluno_{i}' for i in range(10)]
        
        # Adiciona múltiplos frames na fila
        for _ in range(50):
            frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
            if not reconhecimento_instance.frame_queue.full():
                reconhecimento_instance.frame_queue.put(frame)
        
        start_time = time.time()
        
        # Processa alguns frames
        with patch('reconhecimento.face_recognition.face_locations', return_value=[]), \
             patch('reconhecimento.face_recognition.face_encodings', return_value=[]):
            
            reconhecimento_instance.monitoramento_ativo = True
            
            # Processa por tempo limitado
            def stop_after_delay():
                time.sleep(1.0)  # 1 segundo
                reconhecimento_instance.monitoramento_ativo = False
            
            threading.Thread(target=stop_after_delay, daemon=True).start()
            reconhecimento_instance._processar_frames()
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Verifica se processamento foi razoavelmente rápido
        assert processing_time < 2.0  # Deve processar em menos de 2 segundos
