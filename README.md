<!-- Badges das Tecnologias -->
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-2.0-black.svg)](https://flask.palletsprojects.com/)
[![Socket.IO](https://img.shields.io/badge/Socket.IO-4.5-black.svg)](https://socket.io/)
[![MySQL](https://img.shields.io/badge/MySQL-8.0-blue.svg)](https://www.mysql.com/)
[![OpenCV](https://img.shields.io/badge/OpenCV-4.7-blue.svg)](https://opencv.org/)
[![face-recognition](https://img.shields.io/badge/face--recognition-latest-green.svg)](https://github.com/ageitgey/face_recognition)
[![Bootstrap](https://img.shields.io/badge/Bootstrap-5.0-purple.svg)](https://getbootstrap.com/)

# 🎓 Sistema de Controle de Presença por Reconhecimento Facial

Este projeto é uma aplicação web completa para controle de presença de alunos, utilizando reconhecimento facial em tempo real. O sistema é construído com:

- **Backend** em Python (Flask + Flask-SocketIO)  
- **Reconhecimento Facial** com `face-recognition` e `opencv-python`  
- **Banco de Dados** MySQL  
- **Frontend** HTML5, CSS3, JavaScript, Bootstrap 5 e Socket.IO Client  

---

## ✨ Funcionalidades Principais

- **Monitoramento em Tempo Real**  
  Acompanhe o feed de vídeo da câmera e receba logs de presença e ausência a cada 30 segundos.  
- **Cadastro de Alunos via Webcam**  
  Captura de foto diretamente no navegador para registrar novos perfis faciais.  
- **Seleção de Câmera**  
  Escolha qual dispositivo de vídeo usar tanto no monitoramento quanto no cadastro.  
- **Gerenciamento de Alunos**  
  Interface para listar, editar (nome/foto) e excluir alunos cadastrados.  
- **Interface Web Moderna**  
  Layout responsivo e interativo com atualizações em tempo real via Socket.IO.  
- **Persistência em MySQL**  
  Todas as informações e encodings faciais são armazenados em banco de dados relacional.  

---

## 📂 Estrutura do Projeto

```plaintext
.
├── app.py                   # Servidor principal Flask e rotas da API
├── cadastro.py              # CRUD de alunos (MySQL)
├── reconhecimento.py        # Lógica de reconhecimento e controle de presença
├── requirements.txt         # Dependências Python
├── bd.sql                   # Script de criação do banco de dados
├── templates/
│   └── index.html           # Página principal
└── static/
    ├── css/
    │   └── style.css        # Estilos adicionais
    └── js/
        └── app.js           # Lógica front-end (API, Socket.IO, câmera)
```

---

## 🚀 Instalação e Execução

### Pré-requisitos

- Python 3.8 ou superior  
- MySQL instalado e em execução  
- Webcam conectada  

### Passo a passo

1. **Clone o repositório**  
   ```bash
   git clone https://github.com/SEU_USUARIO/SEU_REPOSITORIO.git
   cd SEU_REPOSITORIO
   ```

2. **Crie e ative um ambiente virtual**  
   ```bash
   # Linux/macOS
   python3 -m venv venv
   source venv/bin/activate

   # Windows
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Instale as dependências**  
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure o banco de dados**  
   - Abra `cadastro.py`  
   - Atualize o dicionário `DB_CONFIG` com suas credenciais MySQL:
     ```python
     DB_CONFIG = {
         'host': 'localhost',
         'user': 'seu_usuario_mysql',
         'password': 'sua_senha_mysql',
         'database': 'mydb'
     }
     ```  
   - As tabelas serão criadas automaticamente na primeira execução, ou você pode rodar manualmente:
     ```sql
     mysql -u seu_usuario_mysql -p mydb < bd.sql
     ```

5. **Inicie a aplicação**  
   ```bash
   python app.py
   ```
   Acesse em: `http://127.0.0.1:5000`

---

## 📖 Como Usar

1. **Aba de Monitoramento**  
   - Selecione a câmera  
   - Clique em “Iniciar Monitoramento”  
   - Veja o feed e acompanhe logs a cada 30s  

2. **Aba de Cadastro Rápido**  
   - Selecione a câmera  
   - Clique em “Abrir Câmera” e permita acesso  
   - Clique em “Tirar Foto” e posicione o rosto  
   - Preencha **ID** e **Nome**  
   - Clique em “Registrar Aluno”  

3. **Aba de Listagem de Alunos**  
   - Visualize todos os cadastros  
   - Edite nome/foto ou exclua um perfil  

---

## 🤝 Contribuições

1. Faça um **fork** deste repositório  
2. Crie uma **branch** com sua feature:  
   ```bash
   git checkout -b feature/nova-funcionalidade
   ```  
3. **Commit** suas mudanças:  
   ```bash
   git commit -m "Adiciona nova funcionalidade"
   ```  
4. **Push** na branch:  
   ```bash
   git push origin feature/nova-funcionalidade
   ```  
5. Abra um **Pull Request** 😉

---

## 📄 Licença

Este projeto está licenciado sob a [MIT License](LICENSE).

---

# 🎓 Facial Recognition Attendance System

This project is a complete web application for student attendance tracking using real-time facial recognition. The system is built with:

- **Backend** in Python (Flask + Flask-SocketIO)  
- **Facial Recognition** with `face-recognition` and `opencv-python`  
- **Database** MySQL  
- **Frontend** HTML5, CSS3, JavaScript, Bootstrap 5, and Socket.IO Client  

---

## ✨ Key Features

- **Real-Time Monitoring**  
  Watch the camera feed and receive presence/absence logs every 30 seconds.  
- **Webcam-Based Registration**  
  Capture a photo directly in the browser to register new face profiles.  
- **Camera Selection**  
  Choose which video device to use for both monitoring and registration.  
- **Student Management**  
  Interface to list, edit (name/photo), and delete registered students.  
- **Modern Web Interface**  
  Responsive, interactive layout with real-time updates via Socket.IO.  
- **MySQL Persistence**  
  All student information and face encodings are stored in a relational database.  

---

## 📂 Project Structure

```plaintext
.
├── app.py                   # Main Flask server and API routes
├── cadastro.py              # Student CRUD (MySQL)
├── reconhecimento.py        # Recognition and attendance control logic
├── requirements.txt         # Python dependencies
├── bd.sql                   # Database creation script
├── templates/
│   └── index.html           # Main application page
└── static/
    ├── css/
    │   └── style.css        # Additional styles
    └── js/
        └── app.js           # Frontend logic (API, Socket.IO, camera)
```

---

## 🚀 Installation and Setup

### Prerequisites

- Python 3.8+  
- MySQL installed and running  
- Connected webcam  

### Steps to Run

1. **Clone the repository**  
   ```bash
   git clone https://github.com/YOUR_USER/YOUR_REPO.git
   cd YOUR_REPO
   ```

2. **Create and activate a virtual environment**  
   ```bash
   # Linux/macOS
   python3 -m venv venv
   source venv/bin/activate

   # Windows
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Install dependencies**  
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure the database**  
   - Open `cadastro.py`  
   - Update the `DB_CONFIG` dictionary with your MySQL credentials:
     ```python
     DB_CONFIG = {
         'host': 'localhost',
         'user': 'your_mysql_user',
         'password': 'your_mysql_password',
         'database': 'mydb'
     }
     ```  
   - Tables are auto-created on first run, or run manually:
     ```sql
     mysql -u your_mysql_user -p mydb < bd.sql
     ```

5. **Start the application**  
   ```bash
   python app.py
   ```
   Visit: `http://127.0.0.1:5000`

---

## 📖 Usage

1. **Monitoring Tab**  
   - Select camera  
   - Click “Start Monitoring”  
   - View feed and logs every 30s  

2. **Quick Registration Tab**  
   - Select camera  
   - Click “Open Camera” and allow access  
   - Click “Take Photo” and position face  
   - Enter **ID** and **Name**  
   - Click “Register Student”  

3. **Student List Tab**  
   - View all registrations  
   - Edit name/photo or delete a profile  

---

## 🤝 Contributing

1. Fork this repository  
2. Create a branch for your feature:  
   ```bash
   git checkout -b feature/new-feature
   ```  
3. Commit your changes:  
   ```bash
   git commit -m "Add new feature"
   ```  
4. Push to the branch:  
   ```bash
   git push origin feature/new-feature
   ```  
5. Open a Pull Request 😉

---

## 📄 License

This project is licensed under the MIT License (LICENSE).

---