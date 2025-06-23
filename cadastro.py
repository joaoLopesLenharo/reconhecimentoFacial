import os
import cv2
import face_recognition
import numpy as np
import json
from datetime import datetime
import mysql.connector
from mysql.connector import Error

def conectar_mysql():
    try:
        conn = mysql.connector.connect(
            host='localhost',
            user='root',
            password='root'
        )
        cursor = conn.cursor()
        cursor.execute("CREATE DATABASE IF NOT EXISTS mydb DEFAULT CHARACTER SET utf8;")
        conn.database = 'mydb'
        # Criação das tabelas se não existirem
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS reconhecimento_aluno (
            id_rn INT NOT NULL,
            infoRec TEXT NOT NULL,
            PRIMARY KEY (id_rn)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8;
        ''')
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS alunos (
            Id INT NOT NULL,
            Nome VARCHAR(90) NOT NULL,
            reconhecimento_aluno_id_rn INT NOT NULL,
            PRIMARY KEY (Id),
            INDEX fk_alunos_reconhecimento_aluno1_idx (reconhecimento_aluno_id_rn ASC),
            CONSTRAINT fk_alunos_reconhecimento_aluno1 FOREIGN KEY (reconhecimento_aluno_id_rn)
                REFERENCES reconhecimento_aluno (id_rn)
                ON DELETE NO ACTION ON UPDATE NO ACTION
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8;
        ''')
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS presencas (
            id_lancamento INT NOT NULL AUTO_INCREMENT,
            id_aluno INT NOT NULL,
            local VARCHAR(90) NOT NULL,
            PRIMARY KEY (id_lancamento),
            INDEX id_aluno_idx (id_aluno ASC),
            CONSTRAINT id_aluno FOREIGN KEY (id_aluno)
                REFERENCES alunos (Id)
                ON DELETE NO ACTION ON UPDATE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8;
        ''')
        cursor.close()
        return conn
    except Error as e:
        raise RuntimeError(f"Erro ao conectar/criar banco MySQL: {str(e)}")

def listar_cameras_disponiveis():
    """Lista todas as câmeras disponíveis no sistema."""
    cameras_disponiveis = []
    
    # No Windows, tentar primeiro com DirectShow
    if os.name == 'nt':
        for i in range(10):
            try:
                cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
                if cap.isOpened():
                    ret, _ = cap.read()
                    if ret:
                        cameras_disponiveis.append(i)
                    cap.release()
            except:
                continue
    
    # Se nenhuma câmera foi encontrada com DirectShow, tentar com backend padrão
    if not cameras_disponiveis:
        for i in range(10):
            try:
                cap = cv2.VideoCapture(i)
                if cap.isOpened():
                    ret, _ = cap.read()
                    if ret:
                        cameras_disponiveis.append(i)
                    cap.release()
            except:
                continue
    
    return cameras_disponiveis

def capturar_imagem_camera(camera_id=0):
    """Captura uma imagem da câmera especificada."""
    # No Windows, tentar primeiro com DirectShow
    if os.name == 'nt':
        cap = cv2.VideoCapture(camera_id, cv2.CAP_DSHOW)
    else:
        cap = cv2.VideoCapture(camera_id)
    
    if not cap.isOpened():
        # Se falhar com DirectShow, tentar com backend padrão
        if os.name == 'nt':
            cap = cv2.VideoCapture(camera_id)
            if not cap.isOpened():
                raise RuntimeError(f"Não foi possível acessar a câmera {camera_id}")
        else:
            raise RuntimeError(f"Não foi possível acessar a câmera {camera_id}")
    
    # Configurar resolução
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    
    # Capturar frame
    ret, frame = cap.read()
    cap.release()
    
    if not ret:
        raise RuntimeError("Falha ao capturar imagem da câmera")
    
    return frame

def extrair_codificacao_facial(frame):
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    codificacoes = face_recognition.face_encodings(rgb_frame)
    if codificacoes:
        return codificacoes[0].tolist()
    return None

def cadastrar_aluno(id, nome, frame):
    if not id or not nome:
        raise ValueError("ID e nome são obrigatórios")
    codificacao_facial = extrair_codificacao_facial(frame)
    if codificacao_facial is None:
        raise RuntimeError("Nenhum rosto detectado na imagem para cadastro.")
    conn = conectar_mysql()
    cursor = conn.cursor()
    try:
        # Salvar codificação facial em reconhecimento_aluno
        cursor.execute("INSERT INTO reconhecimento_aluno (id_rn, infoRec) VALUES (%s, %s)", (id, json.dumps(codificacao_facial)))
        # Salvar aluno
        cursor.execute("INSERT INTO alunos (Id, Nome, reconhecimento_aluno_id_rn) VALUES (%s, %s, %s)", (id, nome, id))
        conn.commit()
    except mysql.connector.IntegrityError:
        conn.rollback()
        raise ValueError(f"ID {id} já existe no sistema")
    finally:
        cursor.close()
        conn.close()
    return {'Id': id, 'Nome': nome}

def atualizar_foto_aluno(id, frame):
    conn = conectar_mysql()
    cursor = conn.cursor()
    cursor.execute("SELECT Id FROM alunos WHERE Id = %s", (id,))
    if not cursor.fetchone():
        cursor.close()
        conn.close()
        raise ValueError(f"Aluno com ID {id} não encontrado")
    codificacao_facial = extrair_codificacao_facial(frame)
    if codificacao_facial is None:
        cursor.close()
        conn.close()
        raise RuntimeError("Nenhum rosto detectado na imagem para atualização.")
    try:
        cursor.execute("UPDATE reconhecimento_aluno SET infoRec = %s WHERE id_rn = %s", (json.dumps(codificacao_facial), id))
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise RuntimeError(f"Erro ao atualizar codificação facial: {str(e)}")
    finally:
        cursor.close()
        conn.close()
    return True

def listar_alunos():
    conn = conectar_mysql()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT a.Id, a.Nome, r.infoRec FROM alunos a JOIN reconhecimento_aluno r ON a.reconhecimento_aluno_id_rn = r.id_rn")
    alunos = cursor.fetchall()
    # Converter infoRec de JSON para lista
    for aluno in alunos:
        aluno['codificacao_facial'] = json.loads(aluno['infoRec'])
        del aluno['infoRec']
    cursor.close()
    conn.close()
    return alunos

def editar_aluno(id, novo_nome, frame=None):
    if not novo_nome:
        raise ValueError("Novo nome é obrigatório")
    conn = conectar_mysql()
    cursor = conn.cursor()
    cursor.execute("SELECT Id FROM alunos WHERE Id = %s", (id,))
    if not cursor.fetchone():
        cursor.close()
        conn.close()
        raise ValueError(f"Aluno com ID {id} não encontrado")
    try:
        if frame is not None:
            codificacao_facial = extrair_codificacao_facial(frame)
            if codificacao_facial is None:
                raise RuntimeError("Nenhum rosto detectado na imagem para atualização.")
            cursor.execute("UPDATE alunos SET Nome = %s WHERE Id = %s", (novo_nome, id))
            cursor.execute("UPDATE reconhecimento_aluno SET infoRec = %s WHERE id_rn = %s", (json.dumps(codificacao_facial), id))
        else:
            cursor.execute("UPDATE alunos SET Nome = %s WHERE Id = %s", (novo_nome, id))
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise RuntimeError(f"Erro ao editar aluno: {str(e)}")
    finally:
        cursor.close()
        conn.close()
    return True

def excluir_aluno(id):
    conn = conectar_mysql()
    cursor = conn.cursor()
    cursor.execute("SELECT Id FROM alunos WHERE Id = %s", (id,))
    if not cursor.fetchone():
        cursor.close()
        conn.close()
        raise ValueError(f"Aluno com ID {id} não encontrado")
    try:
        cursor.execute("DELETE FROM presencas WHERE id_aluno = %s", (id,))
        cursor.execute("DELETE FROM alunos WHERE Id = %s", (id,))
        cursor.execute("DELETE FROM reconhecimento_aluno WHERE id_rn = %s", (id,))
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise RuntimeError(f"Erro ao excluir aluno: {str(e)}")
    finally:
        cursor.close()
        conn.close()
    return True 