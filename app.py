from flask import Flask, render_template, jsonify, request, send_file
from flask_socketio import SocketIO
import os
import cv2
import base64
import numpy as np
from datetime import datetime
import threading
import time
from cadastro import (
    cadastrar_aluno, listar_alunos, editar_aluno, 
    excluir_aluno, capturar_imagem_camera, listar_cameras_disponiveis
)
from reconhecimento import ReconhecimentoFacial

app = Flask(__name__)
app.config['SECRET_KEY'] = 'sua_chave_secreta_aqui'
socketio = SocketIO(app, cors_allowed_origins="*")

# Inicializar o reconhecimento facial
reconhecimento = ReconhecimentoFacial()

# Configurar callbacks
def callback_mensagens(mensagens):
    for mensagem in mensagens:
        socketio.emit('log', {'mensagem': mensagem})

def callback_frame(frame_base64):
    socketio.emit('frame', {'frame': frame_base64})

reconhecimento.definir_callback_mensagens(callback_mensagens)
reconhecimento.definir_callback_frame(callback_frame)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/cameras')
def get_cameras():
    try:
        cameras = listar_cameras_disponiveis()
        return jsonify({'success': True, 'cameras': cameras})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/alunos')
def get_alunos():
    try:
        alunos = listar_alunos()
        # Ajustar campos para compatibilidade com frontend
        for aluno in alunos:
            aluno['_id'] = aluno['Id']
            aluno['nome'] = aluno['Nome']
        return jsonify({'success': True, 'alunos': alunos})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/alunos', methods=['POST'])
def create_aluno():
    try:
        data = request.json
        id_aluno = data.get('id')
        nome = data.get('nome')
        frame_base64 = data.get('frame')
        
        if not all([id_aluno, nome, frame_base64]):
            return jsonify({'success': False, 'error': 'Dados incompletos'})
        
        # Converter base64 para frame
        frame_data = base64.b64decode(frame_base64.split(',')[1])
        frame_array = np.frombuffer(frame_data, np.uint8)
        frame = cv2.imdecode(frame_array, cv2.IMREAD_COLOR)
        
        # Salvar aluno
        cadastrar_aluno(id_aluno, nome, frame)
        
        # Recarregar codificações
        reconhecimento.carregar_codificacoes_referencia()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/alunos/<id_aluno>', methods=['PUT'])
def update_aluno(id_aluno):
    try:
        data = request.json
        nome = data.get('nome')
        frame_base64 = data.get('frame')
        
        if not nome:
            return jsonify({'success': False, 'error': 'Nome não fornecido'})
        
        if frame_base64:
            # Converter base64 para frame
            frame_data = base64.b64decode(frame_base64.split(',')[1])
            frame_array = np.frombuffer(frame_data, np.uint8)
            frame = cv2.imdecode(frame_array, cv2.IMREAD_COLOR)
            
            # Atualizar aluno com nova foto
            editar_aluno(id_aluno, nome, frame)
        else:
            # Atualizar apenas o nome
            editar_aluno(id_aluno, nome)
        
        # Recarregar codificações
        reconhecimento.carregar_codificacoes_referencia()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/alunos/<id_aluno>', methods=['DELETE'])
def delete_aluno(id_aluno):
    try:
        excluir_aluno(id_aluno)
        
        # Recarregar codificações
        reconhecimento.carregar_codificacoes_referencia()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/monitoramento/start', methods=['POST'])
def start_monitoring():
    try:
        data = request.json
        camera_id = data.get('camera_id', 0)
        
        # Iniciar monitoramento
        reconhecimento.iniciar_monitoramento(camera_id)
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/monitoramento/stop', methods=['POST'])
def stop_monitoring():
    try:
        reconhecimento.parar_monitoramento()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/camera/capture', methods=['POST'])
def capture_photo():
    try:
        data = request.json
        camera_id = data.get('camera_id', 0)
        
        # Capturar imagem da câmera
        frame = capturar_imagem_camera(camera_id)
        
        # Converter frame para base64
        _, buffer = cv2.imencode('.jpg', frame)
        frame_base64 = base64.b64encode(buffer).decode('utf-8')
        
        return jsonify({
            'success': True,
            'frame': f'data:image/jpeg;base64,{frame_base64}'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000) 