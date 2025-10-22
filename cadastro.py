# cadastro.py
import cv2
import face_recognition
import numpy as np
import json
import mysql.connector
from mysql.connector import Error
import os

# --- CONFIGURAÇÃO DO BANCO DE DADOS ---
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'root',
    'database': 'mydb'
}

def conectar_mysql():
    try:
        conn_init = mysql.connector.connect(
            host=DB_CONFIG['host'],
            user=DB_CONFIG['user'],
            password=DB_CONFIG['password']
        )
        cursor_init = conn_init.cursor()
        cursor_init.execute(f"CREATE DATABASE IF NOT EXISTS `{DB_CONFIG['database']}` DEFAULT CHARACTER SET utf8;")
        cursor_init.close()
        conn_init.close()
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        raise RuntimeError(f"Erro ao conectar ao MySQL: {str(e)}")

def criar_tabelas_se_nao_existir(conn):
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
        INDEX fk_presencas_alunos_idx (id_aluno ASC),
        CONSTRAINT fk_presencas_alunos FOREIGN KEY (id_aluno)
            REFERENCES alunos (Id)
            ON DELETE CASCADE ON UPDATE CASCADE
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
    cursor.close()

try:
    conn_tmp = conectar_mysql()
    criar_tabelas_se_nao_existir(conn_tmp)
    conn_tmp.close()
except RuntimeError as e:
    print(f"ERRO CRÍTICO: Não foi possível inicializar o banco de dados. Verifique a configuração em `cadastro.py`. Detalhes: {e}")


def listar_cameras_disponiveis():
    """Lista todas as câmeras disponíveis no sistema com diagnóstico."""
    print("\n[BACKEND] Sondando câmeras com OpenCV para o monitoramento...")
    cameras_disponiveis = []
    
    for i in range(10):
        try:
            cap = cv2.VideoCapture(i, cv2.CAP_DSHOW if os.name == 'nt' else cv2.CAP_ANY)
            if cap is not None and cap.isOpened():
                ret, _ = cap.read()
                if ret:
                    print(f"[BACKEND] Câmera no índice {i} funcional. Adicionando à lista.")
                    cameras_disponiveis.append(i)
                else:
                    print(f"[BACKEND] Câmera no índice {i} abriu, mas falhou ao ler um frame.")
                cap.release()
        except Exception as e:
            print(f"[BACKEND] Exceção ao testar câmera no índice {i}: {e}")
            continue
    
    if not cameras_disponiveis:
        print("[BACKEND] AVISO: Nenhuma câmera foi detectada pelo OpenCV.")
    else:
        print(f"[BACKEND] Câmeras encontradas pelo OpenCV: {cameras_disponiveis}")
    return cameras_disponiveis

def extrair_codificacao_facial(frame):
    """Extrai codificação facial de um frame BGR (uint8). Retorna lista ou None se não houver face."""
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    codificacoes = face_recognition.face_encodings(rgb_frame)
    if codificacoes:
        return codificacoes[0].tolist()
    return None

def cadastrar_aluno(id_aluno, nome, frame, resp_telefone=None, resp_email=None):
    # Validações de entrada
    if id_aluno is None or (isinstance(id_aluno, (int, float)) and int(id_aluno) <= 0):
        raise ValueError("ID de aluno inválido.")
    if not nome:
        raise ValueError("ID e nome são obrigatórios.")
    if frame is None or not isinstance(frame, np.ndarray) or frame.size == 0:
        raise ValueError("Imagem inválida.")
    if frame.dtype != np.uint8:
        # Normaliza para uint8 quando possível
        try:
            frame = frame.astype(np.uint8)
        except Exception:
            raise ValueError("Imagem inválida.")
    
    codificacao_facial = extrair_codificacao_facial(frame)
    if codificacao_facial is None:
        raise RuntimeError("Nenhum rosto detectado na imagem para cadastro.")
    
    conn = conectar_mysql()
    cursor = conn.cursor()
    try:
        codificacao_json = json.dumps(codificacao_facial)
        cursor.execute(
            "INSERT INTO alunos (Id, Nome, codificacao_facial) VALUES (%s, %s, %s)",
            (id_aluno, nome, codificacao_json)
        )
        # Se dados do responsável forem informados, cria o vínculo 1:1
        if resp_telefone and resp_email:
            cursor.execute(
                "INSERT INTO responsavel (id_aluno, telefone, email) VALUES (%s, %s, %s)",
                (id_aluno, resp_telefone, resp_email)
            )
        conn.commit()
    except mysql.connector.IntegrityError:
        conn.rollback()
        raise ValueError(f"O ID '{id_aluno}' já existe no sistema.")
    finally:
        cursor.close()
        conn.close()

def listar_alunos():
    conn = conectar_mysql()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        """
        SELECT a.Id, a.Nome, a.codificacao_facial,
               r.telefone AS resp_telefone, r.email AS resp_email
        FROM alunos a
        LEFT JOIN responsavel r ON r.id_aluno = a.Id
        """
    )
    alunos = cursor.fetchall()
    cursor.close()
    conn.close()
    for aluno in alunos:
        aluno['codificacao_facial'] = json.loads(aluno['codificacao_facial'])
    return alunos

def editar_aluno(id_aluno, novo_nome, frame=None, resp_telefone=None, resp_email=None):
    if not novo_nome:
        raise ValueError("O novo nome é obrigatório.")
        
    conn = conectar_mysql()
    cursor = conn.cursor()
    try:
        if frame is not None:
            # Valida imagem antes de processar
            if not isinstance(frame, np.ndarray) or frame.size == 0:
                raise ValueError("A nova imagem é inválida.")
            if frame.dtype != np.uint8:
                try:
                    frame = frame.astype(np.uint8)
                except Exception:
                    raise ValueError("A nova imagem é inválida.")
            
            codificacao = extrair_codificacao_facial(frame)
            if codificacao is None:
                raise RuntimeError("Nenhum rosto detectado na nova imagem.")
            
            cursor.execute(
                "UPDATE alunos SET Nome = %s, codificacao_facial = %s WHERE Id = %s",
                (novo_nome, json.dumps(codificacao), id_aluno)
            )
        else:
            cursor.execute(
                "UPDATE alunos SET Nome = %s WHERE Id = %s", (novo_nome, id_aluno)
            )
        
        if cursor.rowcount == 0:
            raise ValueError(f"Aluno com ID {id_aluno} não encontrado.")

        # Atualiza ou cria registro de responsável se os dados forem fornecidos
        if resp_telefone is not None or resp_email is not None:
            # Busca existência atual
            cursor_check = conn.cursor()
            cursor_check.execute("SELECT 1 FROM responsavel WHERE id_aluno = %s", (id_aluno,))
            existe = cursor_check.fetchone() is not None
            cursor_check.close()

            if existe:
                if resp_telefone is not None and resp_email is not None:
                    cursor.execute(
                        "UPDATE responsavel SET telefone = %s, email = %s WHERE id_aluno = %s",
                        (resp_telefone, resp_email, id_aluno)
                    )
                elif resp_telefone is not None:
                    cursor.execute(
                        "UPDATE responsavel SET telefone = %s WHERE id_aluno = %s",
                        (resp_telefone, id_aluno)
                    )
                elif resp_email is not None:
                    cursor.execute(
                        "UPDATE responsavel SET email = %s WHERE id_aluno = %s",
                        (resp_email, id_aluno)
                    )
            else:
                if resp_telefone and resp_email:
                    cursor.execute(
                        "INSERT INTO responsavel (id_aluno, telefone, email) VALUES (%s, %s, %s)",
                        (id_aluno, resp_telefone, resp_email)
                    )
                # Se apenas um dos campos vier sem existir registro, ignora para manter consistência

        conn.commit()
    finally:
        cursor.close()
        conn.close()

def excluir_aluno(id_aluno):
    conn = conectar_mysql()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM alunos WHERE Id = %s", (id_aluno,))
        if cursor.rowcount == 0:
            raise ValueError(f"Aluno com ID {id_aluno} não encontrado para exclusão.")
        conn.commit()
    finally:
        cursor.close()
        conn.close()

def obter_responsavel_por_aluno(id_aluno):
    """Retorna dict com telefone e email do responsável do aluno, ou None se não existir."""
    conn = conectar_mysql()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(
            "SELECT telefone, email FROM responsavel WHERE id_aluno = %s",
            (id_aluno,)
        )
        row = cursor.fetchone()
        return row
    finally:
        cursor.close()
        conn.close()