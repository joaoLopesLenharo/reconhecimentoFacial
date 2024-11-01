# database.py
import sqlite3
from datetime import datetime

class Database:
    def __init__(self, db_name="alunos.db"):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()

    def create_tables(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS alunos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                foto BLOB,
                descricao TEXT
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS presenca (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                aluno_id INTEGER,
                data_hora TEXT,
                status TEXT,
                FOREIGN KEY (aluno_id) REFERENCES alunos (id)
            )
        """)
        self.conn.commit()

    def insert_aluno(self, nome, foto, descricao):
        self.cursor.execute("INSERT INTO alunos (nome, foto, descricao) VALUES (?, ?, ?)", (nome, foto, descricao))
        self.conn.commit()

    def get_all_alunos(self):
        self.cursor.execute("SELECT id, nome, foto, descricao FROM alunos")
        return [{"id": row[0], "nome": row[1], "foto": row[2], "descricao": row[3]} for row in self.cursor.fetchall()]

    def record_presence(self, aluno_id, status="Presente"):
        data_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.cursor.execute("INSERT INTO presenca (aluno_id, data_hora, status) VALUES (?, ?, ?)", (aluno_id, data_hora, status))
        self.conn.commit()

        # Obter o nome do aluno para exibir no terminal
        self.cursor.execute("SELECT nome FROM alunos WHERE id = ?", (aluno_id,))
        aluno_nome = self.cursor.fetchone()[0]
        
        # Print no terminal
        print(f"Presença registrada para {aluno_nome} às {data_hora}")

    def close(self):
        self.conn.close()

if __name__ == "__main__":
    db = Database()
    db.create_tables()  # Certifique-se de que as tabelas existam antes de consultar
    
    alunos = db.get_all_alunos()
    if alunos:
        print("Lista de todos os alunos cadastrados:")
        for aluno in alunos:
            print(f"ID: {aluno['id']}, Nome: {aluno['nome']}, descricao: {aluno['descricao']}")
    else:
        print("Nenhum aluno cadastrado no banco de dados.")

    db.close()
