"""
Testes para operações de banco de dados
"""
import pytest
import mysql.connector
from unittest.mock import Mock, patch
from tests.factories import AlunoFactory, ResponsavelFactory, TestDataBuilder


@pytest.mark.database
class TestDatabaseOperations:
    """Testes para operações básicas do banco de dados"""
    
    def test_database_connection(self, test_database):
        """Testa conexão com banco de dados de teste"""
        cursor = test_database.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        assert result[0] == 1
    
    def test_create_tables(self, test_database):
        """Testa criação das tabelas"""
        cursor = test_database.cursor()
        
        # Verifica se tabelas existem
        cursor.execute("SHOW TABLES")
        tables = [table[0] for table in cursor.fetchall()]
        
        assert 'alunos' in tables
        assert 'presencas' in tables
        assert 'responsaveis' in tables
    
    def test_insert_student(self, test_database):
        """Testa inserção de aluno"""
        cursor = test_database.cursor()
        
        student_data = AlunoFactory()
        
        cursor.execute("""
            INSERT INTO alunos (Id, Nome, codificacao_facial)
            VALUES (%s, %s, %s)
        """, (student_data['Id'], student_data['Nome'], student_data['codificacao_facial']))
        
        test_database.commit()
        
        # Verifica inserção
        cursor.execute("SELECT * FROM alunos WHERE Id = %s", (student_data['Id'],))
        result = cursor.fetchone()
        
        assert result is not None
        assert result[0] == student_data['Id']
        assert result[1] == student_data['Nome']


@pytest.mark.database
class TestDataIntegrity:
    """Testes para integridade dos dados"""
    
    def test_foreign_key_constraint(self, test_database):
        """Testa restrições de chave estrangeira"""
        cursor = test_database.cursor()
        
        # Tenta inserir presença para aluno inexistente
        with pytest.raises(mysql.connector.IntegrityError):
            cursor.execute("""
                INSERT INTO presencas (id_aluno, local)
                VALUES (%s, %s)
            """, (99999, "Sala Teste"))
            test_database.commit()
    
    def test_unique_constraint(self, test_database):
        """Testa restrições de unicidade"""
        cursor = test_database.cursor()
        
        student_data = AlunoFactory()
        
        # Insere primeiro aluno
        cursor.execute("""
            INSERT INTO alunos (Id, Nome, codificacao_facial)
            VALUES (%s, %s, %s)
        """, (student_data['Id'], student_data['Nome'], student_data['codificacao_facial']))
        test_database.commit()
        
        # Tenta inserir aluno com mesmo ID
        with pytest.raises(mysql.connector.IntegrityError):
            cursor.execute("""
                INSERT INTO alunos (Id, Nome, codificacao_facial)
                VALUES (%s, %s, %s)
            """, (student_data['Id'], "Outro Nome", "outra_codificacao"))
            test_database.commit()


@pytest.mark.database
class TestComplexQueries:
    """Testes para consultas complexas"""
    
    def test_join_students_responsibles(self, test_database):
        """Testa join entre alunos e responsáveis"""
        cursor = test_database.cursor()
        
        # Insere dados de teste
        student_data = AlunoFactory()
        responsible_data = ResponsavelFactory(id_aluno=student_data['Id'])
        
        cursor.execute("""
            INSERT INTO alunos (Id, Nome, codificacao_facial)
            VALUES (%s, %s, %s)
        """, (student_data['Id'], student_data['Nome'], student_data['codificacao_facial']))
        
        cursor.execute("""
            INSERT INTO responsaveis (id_aluno, nome, telefone, email)
            VALUES (%s, %s, %s, %s)
        """, (responsible_data['id_aluno'], responsible_data['nome'], 
              responsible_data['telefone'], responsible_data['email']))
        
        test_database.commit()
        
        # Executa join
        cursor.execute("""
            SELECT a.Nome, r.nome, r.email
            FROM alunos a
            JOIN responsaveis r ON a.Id = r.id_aluno
            WHERE a.Id = %s
        """, (student_data['Id'],))
        
        result = cursor.fetchone()
        assert result is not None
        assert result[0] == student_data['Nome']
        assert result[1] == responsible_data['nome']
    
    def test_attendance_statistics(self, test_database):
        """Testa consultas de estatísticas de presença"""
        cursor = test_database.cursor()
        
        # Insere dados de teste
        students = TestDataBuilder.create_multiple_students(3)
        
        for student in students:
            cursor.execute("""
                INSERT INTO alunos (Id, Nome, codificacao_facial)
                VALUES (%s, %s, %s)
            """, (student['Id'], student['Nome'], student['codificacao_facial']))
            
            # Insere algumas presenças
            for i in range(5):
                cursor.execute("""
                    INSERT INTO presencas (id_aluno, local)
                    VALUES (%s, %s)
                """, (student['Id'], f"Sala {i+1}"))
        
        test_database.commit()
        
        # Consulta estatísticas
        cursor.execute("""
            SELECT COUNT(*) as total_presencas,
                   COUNT(DISTINCT id_aluno) as alunos_presentes
            FROM presencas
        """)
        
        result = cursor.fetchone()
        assert result[0] == 15  # 3 alunos * 5 presenças
        assert result[1] == 3   # 3 alunos distintos
