# app.py
from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO
import cv2
import base64
import numpy as np
from cadastro import (
    cadastrar_aluno, listar_alunos, editar_aluno,
    excluir_aluno, listar_cameras_disponiveis
)
from reconhecimento import ReconhecimentoFacial

app = Flask(__name__)
app.config['SECRET_KEY'] = 'uma_chave_secreta_muito_segura'
socketio = SocketIO(app, cors_allowed_origins="*")

reconhecimento = ReconhecimentoFacial()

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
        return jsonify({'success': True, 'cameras': listar_cameras_disponiveis()})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/alunos')
def get_alunos():
    try:
        alunos = listar_alunos()
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
            return jsonify({'success': False, 'error': 'Dados incompletos: ID, nome e foto são obrigatórios.'})
        
        id_aluno = int(id_aluno)
        
        frame_data = base64.b64decode(frame_base64.split(',')[1])
        frame = cv2.imdecode(np.frombuffer(frame_data, np.uint8), cv2.IMREAD_COLOR)
        if frame is None:
             return jsonify({'success': False, 'error': 'Imagem inválida ou corrompida.'})

        cadastrar_aluno(id_aluno, nome, frame)
        reconhecimento.carregar_codificacoes_referencia()
        return jsonify({'success': True})
    except (ValueError, TypeError) as e:
        return jsonify({'success': False, 'error': str(e)})
    except Exception as e:
        return jsonify({'success': False, 'error': f'Erro inesperado: {str(e)}'})

@app.route('/api/alunos/<int:id_aluno>', methods=['PUT'])
def update_aluno(id_aluno):
    try:
        data = request.json
        nome = data.get('nome')
        frame_base64 = data.get('frame')
        frame = None
        
        if not nome:
            return jsonify({'success': False, 'error': 'O campo nome é obrigatório.'})

        if frame_base64:
            frame_data = base64.b64decode(frame_base64.split(',')[1])
            frame = cv2.imdecode(np.frombuffer(frame_data, np.uint8), cv2.IMREAD_COLOR)
            if frame is None:
                return jsonify({'success': False, 'error': 'A nova imagem é inválida ou corrompida.'})
        
        editar_aluno(id_aluno, nome, frame)
        reconhecimento.carregar_codificacoes_referencia()
        return jsonify({'success': True})
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)})
    except Exception as e:
        return jsonify({'success': False, 'error': f'Erro inesperado: {str(e)}'})

@app.route('/api/alunos/<int:id_aluno>', methods=['DELETE'])
def delete_aluno(id_aluno):
    try:
        excluir_aluno(id_aluno)
        reconhecimento.carregar_codificacoes_referencia()
        return jsonify({'success': True})
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)})
    except Exception as e:
        return jsonify({'success': False, 'error': f'Erro inesperado: {str(e)}'})

@app.route('/api/monitoramento/start', methods=['POST'])
def start_monitoring():
    try:
        camera_id = int(request.json.get('camera_id', 0))
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

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)