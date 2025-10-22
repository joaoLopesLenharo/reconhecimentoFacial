"""
Testes unitários para o módulo cadastro.py
"""
import pytest
import numpy as np
import cv2
from unittest.mock import Mock, patch, MagicMock
import mysql.connector
from mysql.connector import Error

from cadastro import (
    conectar_mysql, criar_tabelas_se_nao_existir, cadastrar_aluno,
    listar_alunos, editar_aluno, excluir_aluno, obter_responsavel_por_aluno,
    listar_cameras_disponiveis
)


class TestConexaoBancoDados:
    """Testes para funções de conexão com banco de dados"""
    
    @patch('cadastro.mysql.connector.connect')
    def test_conectar_mysql_sucesso(self, mock_connect):
        """Testa conexão bem-sucedida com MySQL"""
        mock_conn = Mock()
        mock_connect.return_value = mock_conn
        
        result = conectar_mysql()
        
        assert result == mock_conn
        mock_connect.assert_called()
    
    @patch('cadastro.mysql.connector.connect')
    def test_conectar_mysql_erro(self, mock_connect):
        """Testa erro na conexão com MySQL"""
        mock_connect.side_effect = Error("Connection failed")
        
        with pytest.raises(RuntimeError, match="Erro ao conectar ao MySQL"):
            conectar_mysql()
    
    def test_criar_tabelas_se_nao_existir(self, mock_database):
        """Testa criação das tabelas no banco"""
        mock_conn, mock_cursor = mock_database
        
        criar_tabelas_se_nao_existir(mock_conn)
        
        # Verifica se as queries de criação foram executadas
        assert mock_cursor.execute.call_count >= 3  # alunos, presencas, responsaveis
        mock_conn.commit.assert_called_once()


class TestCadastroAluno:
    """Testes para operações de cadastro de alunos"""
    
    @patch('cadastro.conectar_mysql')
    @patch('cadastro.face_recognition.face_encodings')
    def test_cadastrar_aluno_sucesso(self, mock_encodings, mock_connect, sample_face_image):
        """Testa cadastro bem-sucedido de aluno"""
        # Setup mocks
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        
        # Mock face recognition
        mock_encodings.return_value = [np.random.rand(128)]
        
        # Executa o cadastro
        cadastrar_aluno(12345, "João Silva", sample_face_image, 
                       resp_telefone="11999999999", resp_email="test@email.com")
        
        # Verifica se as operações foram executadas
        mock_cursor.execute.assert_called()
        mock_conn.commit.assert_called()
        mock_conn.close.assert_called()
    
    @patch('cadastro.conectar_mysql')
    @patch('cadastro.face_recognition.face_encodings')
    def test_cadastrar_aluno_sem_face(self, mock_encodings, mock_connect, sample_face_image):
        """Testa cadastro quando não encontra face na imagem"""
        mock_conn = Mock()
        mock_connect.return_value = mock_conn
        mock_encodings.return_value = []  # Nenhuma face encontrada
        
        # Código atual lança RuntimeError com mensagem diferente
        with pytest.raises(RuntimeError, match="Nenhum rosto detectado"):
            cadastrar_aluno(12345, "João Silva", sample_face_image)
    
    @patch('cadastro.extrair_codificacao_facial', return_value=[0.1]*128)
    @patch('cadastro.conectar_mysql')
    def test_cadastrar_aluno_id_duplicado(self, mock_connect, _mock_extract):
        """Testa cadastro com ID duplicado"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        
        # Simula erro de chave duplicada com IntegrityError
        import mysql.connector
        mock_cursor.execute.side_effect = mysql.connector.IntegrityError("Duplicate entry")
        
        with pytest.raises(ValueError, match="já existe"):
            cadastrar_aluno(12345, "João Silva", np.zeros((100, 100, 3), dtype=np.uint8))


class TestListarAlunos:
    """Testes para listagem de alunos"""
    
    @patch('cadastro.conectar_mysql')
    def test_listar_alunos_sucesso(self, mock_connect):
        """Testa listagem bem-sucedida de alunos"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        
        # Mock dos dados retornados (cursor dictionary=True)
        mock_cursor.fetchall.return_value = [
            {"Id": 12345, "Nome": "João Silva", "codificacao_facial": "[]"},
            {"Id": 67890, "Nome": "Maria Santos", "codificacao_facial": "[]"},
        ]
        
        result = listar_alunos()
        
        assert len(result) == 2
        assert result[0]['Id'] == 12345
        assert result[0]['Nome'] == "João Silva"
        assert result[1]['Id'] == 67890
        assert result[1]['Nome'] == "Maria Santos"
    
    @patch('cadastro.conectar_mysql')
    def test_listar_alunos_vazio(self, mock_connect):
        """Testa listagem quando não há alunos"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        
        mock_cursor.fetchall.return_value = []
        
        result = listar_alunos()
        
        assert result == []


class TestEditarAluno:
    """Testes para edição de alunos"""
    
    @patch('cadastro.conectar_mysql')
    @patch('cadastro.face_recognition.face_encodings')
    def test_editar_aluno_com_nova_foto(self, mock_encodings, mock_connect, sample_face_image):
        """Testa edição de aluno com nova foto"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        
        mock_encodings.return_value = [np.random.rand(128)]
        mock_cursor.rowcount = 1  # Simula que uma linha foi afetada
        
        editar_aluno(12345, "João Silva Editado", sample_face_image)
        
        mock_cursor.execute.assert_called()
        mock_conn.commit.assert_called()
    
    @patch('cadastro.conectar_mysql')
    def test_editar_aluno_sem_foto(self, mock_connect):
        """Testa edição de aluno sem alterar foto"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        
        mock_cursor.rowcount = 1
        
        editar_aluno(12345, "João Silva Editado", None)
        
        mock_cursor.execute.assert_called()
        mock_conn.commit.assert_called()
    
    @patch('cadastro.conectar_mysql')
    def test_editar_aluno_inexistente(self, mock_connect):
        """Testa edição de aluno que não existe"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        
        mock_cursor.rowcount = 0  # Nenhuma linha afetada
        
        with pytest.raises(ValueError, match="Aluno com ID .* não encontrado"):
            editar_aluno(99999, "Nome Inexistente", None)


class TestExcluirAluno:
    """Testes para exclusão de alunos"""
    
    @patch('cadastro.conectar_mysql')
    def test_excluir_aluno_sucesso(self, mock_connect):
        """Testa exclusão bem-sucedida de aluno"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        
        mock_cursor.rowcount = 1
        
        excluir_aluno(12345)
        
        mock_cursor.execute.assert_called()
        mock_conn.commit.assert_called()
    
    @patch('cadastro.conectar_mysql')
    def test_excluir_aluno_inexistente(self, mock_connect):
        """Testa exclusão de aluno que não existe"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        
        mock_cursor.rowcount = 0
        
        with pytest.raises(ValueError, match="Aluno com ID .* não encontrado"):
            excluir_aluno(99999)


class TestResponsaveis:
    """Testes para operações com responsáveis"""
    
    @patch('cadastro.conectar_mysql')
    def test_obter_responsavel_existente(self, mock_connect):
        """Testa obtenção de responsável existente"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        
        mock_cursor.fetchone.return_value = {"telefone": "11999999999", "email": "maria@email.com"}
        
        result = obter_responsavel_por_aluno(12345)
        
        assert result is not None
        assert result['telefone'] == "11999999999"
        assert result['email'] == "maria@email.com"
    
    @patch('cadastro.conectar_mysql')
    def test_obter_responsavel_inexistente(self, mock_connect):
        """Testa obtenção de responsável que não existe"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        
        mock_cursor.fetchone.return_value = None
        
        result = obter_responsavel_por_aluno(99999)
        
        assert result is None


class TestCameras:
    """Testes para operações com câmeras"""
    
    @patch('cadastro.cv2.VideoCapture')
    def test_listar_cameras_disponiveis(self, mock_video_capture):
        """Testa listagem de câmeras disponíveis"""
        import numpy as np
        def vc_side_effect(index, backend):
            m = Mock()
            m.isOpened.return_value = (index < 2)
            m.read.return_value = ((index < 2), np.zeros((10,10,3), dtype=np.uint8))
            return m
        mock_video_capture.side_effect = vc_side_effect
        
        result = listar_cameras_disponiveis()
        
        assert result == [0, 1]  # Apenas as duas primeiras câmeras
    
    @patch('cadastro.cv2.VideoCapture')
    def test_listar_cameras_nenhuma_disponivel(self, mock_video_capture):
        """Testa quando não há câmeras disponíveis"""
        mock_instance = Mock()
        mock_instance.isOpened.return_value = False
        mock_video_capture.return_value = mock_instance
        
        result = listar_cameras_disponiveis()
        
        assert result == []


class TestValidacoes:
    """Testes para validações de entrada"""
    
    def test_validacao_id_aluno_invalido(self):
        """Testa validação de ID de aluno inválido"""
        with pytest.raises(ValueError):
            cadastrar_aluno(-1, "Nome", np.zeros((100, 100, 3), dtype=np.uint8))
        
        with pytest.raises(ValueError):
            cadastrar_aluno(0, "Nome", np.zeros((100, 100, 3), dtype=np.uint8))
    
    def test_validacao_nome_vazio(self):
        """Testa validação de nome vazio"""
        with pytest.raises(ValueError):
            cadastrar_aluno(12345, "", np.zeros((100, 100, 3)))
        
        with pytest.raises(ValueError):
            cadastrar_aluno(12345, None, np.zeros((100, 100, 3)))
    
    def test_validacao_imagem_invalida(self):
        """Testa validação de imagem inválida"""
        with pytest.raises(ValueError):
            cadastrar_aluno(12345, "Nome", None)
        
        with pytest.raises(ValueError):
            cadastrar_aluno(12345, "Nome", np.array([], dtype=np.uint8))


@pytest.mark.integration
class TestIntegracaoCadastro:
    """Testes de integração para o módulo cadastro"""
    
    @pytest.mark.database
    def test_fluxo_completo_aluno(self, test_database, sample_face_image):
        """Testa o fluxo completo de CRUD de aluno"""
        with patch('cadastro.conectar_mysql', return_value=test_database), \
             patch('cadastro.face_recognition.face_encodings', return_value=[np.random.rand(128)]):
            
            # Cadastra aluno
            cadastrar_aluno(12345, "João Silva", sample_face_image, 
                           resp_telefone="11999999999", resp_email="joao@email.com")
            
            # Lista alunos
            alunos = listar_alunos()
            assert len(alunos) == 1
            assert alunos[0]['Id'] == 12345
            assert alunos[0]['Nome'] == "João Silva"
            
            # Edita aluno
            editar_aluno(12345, "João Silva Editado", None)
            
            # Verifica edição
            alunos = listar_alunos()
            assert alunos[0]['Nome'] == "João Silva Editado"
            
            # Exclui aluno
            excluir_aluno(12345)
            
            # Verifica exclusão
            alunos = listar_alunos()
            assert len(alunos) == 0
