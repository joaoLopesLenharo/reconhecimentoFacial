# app.py
import os
from flask import Flask, render_template, jsonify, request, redirect, url_for, send_from_directory
from flask_socketio import SocketIO, emit
import cv2
import base64
import numpy as np
import os
import json
import glob
from dotenv import load_dotenv
from pathlib import Path
from datetime import datetime, timedelta
from cadastro import (
    cadastrar_aluno, listar_alunos, editar_aluno,
    excluir_aluno, listar_cameras_disponiveis, obter_responsavel_por_aluno
)
from reconhecimento import ReconhecimentoFacial
from smtp_service import send_email, is_configured as is_email_configured, smtp_service

# Carregar variáveis de ambiente
load_dotenv()

# Caminho para o arquivo de configuração
CONFIG_FILE = Path('.smtp_config.json')

def load_smtp_config():
    """Carrega as configurações SMTP do arquivo"""
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_smtp_config(config):
    """Salva as configurações SMTP no arquivo"""
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)
    # Atualiza as configurações no serviço SMTP
    smtp_service.__init__()  # Reinicializa o serviço com as novas configurações

app = Flask(__name__)
app.config['SECRET_KEY'] = 'uma_chave_secreta_muito_segura'
socketio = SocketIO(app, cors_allowed_origins="*")

reconhecimento = ReconhecimentoFacial()

@app.route('/debug/email/status')
def debug_email_status():
    """Rota para verificar o status do serviço de e-mail"""
    status = {
        'smtp_configured': is_email_configured(),
        'smtp_username': 'configured' if os.getenv('SMTP_USERNAME') else 'not configured'
    }
    return jsonify(status)

@app.route('/api/email/config', methods=['GET'])
def email_config():
    """Endpoint para verificar se o e-mail está configurado"""
    config = load_smtp_config()
    is_configured = bool(config.get('SMTP_USERNAME') and config.get('SMTP_PASSWORD'))
    
    return jsonify({
        'success': True,
        'is_configured': is_configured,
        'smtp_server': config.get('SMTP_SERVER', ''),
        'smtp_port': config.get('SMTP_PORT', 587),
        'smtp_username': config.get('SMTP_USERNAME', ''),
        'sender_email': config.get('SMTP_SENDER_EMAIL', '')
    })

@app.route('/debug/email/test', methods=['POST'])
def debug_send_test_email():
    """Rota para testar o envio de e-mail"""
    if not is_email_configured():
        return jsonify({
            'status': 'error',
            'message': 'Serviço de e-mail não configurado. Configure as credenciais SMTP primeiro.'
        }), 400
        
    try:
        to_email = request.json.get('to', 'joao.pedro.lopes.lenharo@gmail.com')
        result = send_email(
            to_email=to_email,
            subject='Teste de Envio de E-mail',
            body_text='Este é um e-mail de teste do sistema de monitoramento de presença.'
        )
        
        if result.get('success'):
            return jsonify({'status': 'success', 'message': 'E-mail de teste enviado com sucesso!'})
        else:
            return jsonify({
                'status': 'error',
                'message': result.get('error', 'Falha ao enviar e-mail de teste'),
                'details': result.get('smtp_error', '')
            }), 500
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'Erro ao enviar e-mail: {str(e)}'}), 500

@app.route('/debug/token')
def debug_token():
    """Rota para visualizar o status do token (com informações sensíveis ocultas)"""
    import json
    from flask import current_app, send_file
    
    if not os.path.exists('token.json'):
        return jsonify({'status': 'error', 'message': 'Arquivo token.json não encontrado'}), 404
    
    try:
        with open('token.json', 'r') as f:
            token_data = json.load(f)
            
        # Ocultar informações sensíveis
        safe_token_data = {
            'token': '***' if 'token' in token_data else None,
            'refresh_token': '***' if 'refresh_token' in token_data else None,
            'token_uri': token_data.get('token_uri'),
            'client_id': token_data.get('client_id'),
            'client_secret': '***' if 'client_secret' in token_data else None,
            'scopes': token_data.get('scopes'),
            'expiry': token_data.get('expiry')
        }
        
        return jsonify({
            'status': 'success',
            'token_exists': True,
            'token_data': safe_token_data,
            'raw_scopes': token_data.get('scopes', [])
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Erro ao ler token: {str(e)}'
        }), 500

def callback_mensagens(mensagens):
    for mensagem in mensagens:
        socketio.emit('log', {'mensagem': mensagem})
        # Enviar email para alertas
        if mensagem.startswith('ALERTA:'):
            # Espera formato: "ALERTA: Aluno {id} ausente ..."
            try:
                partes = mensagem.split('Aluno')
                if len(partes) > 1:
                    resto = partes[1].strip()
                    id_str = ''
                    for ch in resto:
                        if ch.isdigit():
                            id_str += ch
                        else:
                            break
                    if id_str:
                        responsavel = obter_responsavel_por_aluno(int(id_str))
                        if responsavel and 'email' in responsavel:
                            # Cria o conteúdo HTML do e-mail
                            html_content = f"""
                            <html>
                                <body>
                                    <p>Prezado Responsável,</p>
                                    <p>O aluno {id_str} está ausente há 2 verificações consecutivas.</p>
                                    <p>Por favor, entre em contato com a instituição para mais informações.</p>
                                    <br>
                                    <p>Atenciosamente,<br>Sistema de Monitoramento de Presença</p>
                                </body>
                            </html>
                            """
                            
                            result = send_email(
                                to_email=responsavel['email'],
                                subject='Alerta de Monitoramento - Ausência de Aluno',
                                body_text=mensagem,
                                html_content=html_content.strip()
                            )
                            if not result.get('success'):
                                print(f"Erro ao enviar e-mail: {result.get('error')}")
                            else:
                                print(f"E-mail de alerta enviado para {responsavel['email']}")
            except Exception as e:
                print(f"Erro ao processar alerta: {e}")

def callback_frame(frame_base64, camera_id=0):
    socketio.emit('camera_frame', {
        'camera_id': camera_id,
        'frame': frame_base64,
        'timestamp': datetime.now().isoformat()
    })

reconhecimento.definir_callback_mensagens(callback_mensagens)
reconhecimento.definir_callback_frame(callback_frame)

# Cria o diretório de vídeos de teste se não existir
TEST_VIDEOS_DIR = Path('test_videos')
TEST_VIDEOS_DIR.mkdir(exist_ok=True)

# Dicionário para armazenar os estados das câmeras
camera_states = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/test-videos')
def get_test_videos():
    """Endpoint para listar os vídeos de teste disponíveis"""
    videos = []
    for ext in ['*.mp4', '*.avi', '*.mov']:
        videos.extend([f for f in glob.glob(str(TEST_VIDEOS_DIR / ext))])
    
    # Retorna apenas os nomes dos arquivos
    video_names = [{
        'id': i,
        'name': os.path.basename(video),
        'path': f'/test_videos/{os.path.basename(video)}'
    } for i, video in enumerate(videos)]
    
    return jsonify({'videos': video_names})

@app.route('/test_videos/<path:filename>')
def serve_test_video(filename):
    """Serve os vídeos de teste"""
    return send_from_directory('test_videos', filename)

@socketio.on('start_monitoring')
def handle_start_monitoring(data):
    """Inicia o monitoramento de uma câmera"""
    camera_id = data.get('camera_id', 0)
    is_test_mode = data.get('test_mode', False)
    
    # Para qualquer monitoramento existente
    if 'monitor_thread' in camera_states.get(camera_id, {}):
        camera_states[camera_id]['running'] = False
        if camera_states[camera_id]['monitor_thread'].is_alive():
            camera_states[camera_id]['monitor_thread'].join()
    
    # Inicia um novo monitoramento
    if camera_id not in camera_states:
        camera_states[camera_id] = {
            'running': True,
            'last_frame': None,
            'last_update': datetime.now()
        }
    else:
        camera_states[camera_id]['running'] = True
    
    # Inicia a thread de monitoramento
    def monitor_camera():
        cap = None
        try:
            if is_test_mode:
                # Modo teste: usa vídeo do arquivo
                video_path = os.path.join('test_videos', f'test_{camera_id}.mp4')
                if not os.path.exists(video_path):
                    emit('error', {'message': f'Vídeo de teste não encontrado: {video_path}'})
                    return
                cap = cv2.VideoCapture(video_path)
            else:
                # Modo normal: usa câmera real
                cap = cv2.VideoCapture(camera_id, cv2.CAP_DSHOW if os.name == 'nt' else cv2.CAP_ANY)
            
            while camera_states.get(camera_id, {}).get('running', False):
                ret, frame = cap.read()
                if not ret:
                    # Se for vídeo, volta para o início
                    if is_test_mode:
                        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                        continue
                    else:
                        break
                
                # Converte o frame para base64
                _, buffer = cv2.imencode('.jpg', frame)
                frame_base64 = base64.b64encode(buffer).decode('utf-8')
                
                # Atualiza o estado da câmera
                camera_states[camera_id]['last_frame'] = frame_base64
                camera_states[camera_id]['last_update'] = datetime.now()
                
                # Envia o frame via WebSocket
                emit('camera_frame', {
                    'camera_id': camera_id,
                    'frame': frame_base64,
                    'timestamp': datetime.now().isoformat()
                })
                
                # Pequena pausa para não sobrecarregar
                socketio.sleep(0.03)  # ~30 FPS
                
        except Exception as e:
            emit('error', {'message': f'Erro no monitoramento: {str(e)}'})
        finally:
            if cap and cap.isOpened():
                cap.release()
    
    # Inicia a thread de monitoramento
    camera_states[camera_id]['monitor_thread'] = socketio.start_background_task(monitor_camera)
    
    return {'status': 'started', 'camera_id': camera_id}

@socketio.on('stop_monitoring')
def handle_stop_monitoring(data):
    """Para o monitoramento de uma câmera"""
    camera_id = data.get('camera_id', 0)
    if camera_id in camera_states:
        camera_states[camera_id]['running'] = False
        if 'monitor_thread' in camera_states[camera_id] and camera_states[camera_id]['monitor_thread'].is_alive():
            camera_states[camera_id]['monitor_thread'].join()
        return {'status': 'stopped', 'camera_id': camera_id}
    return {'status': 'not_found', 'camera_id': camera_id}

# -------------------- Configuração de E-mail --------------------
# As configurações de e-mail são feitas através de variáveis de ambiente
# Configure as seguintes variáveis:
# - SMTP_SERVER (opcional, padrão: smtp.gmail.com)
# - SMTP_PORT (opcional, padrão: 587)
# - SMTP_USERNAME (obrigatório)
# - SMTP_PASSWORD (obrigatório)
# - SMTP_SENDER_EMAIL (opcional, usa SMTP_USERNAME se não definido)
# - SMTP_SENDER_NAME (opcional, padrão: 'Sistema de Monitoramento')

@app.route('/api/email-config')
def get_email_config():
    """Retorna a configuração de e-mail do servidor"""
    try:
        config = {}
        if os.path.exists('email_config.json'):
            with open('email_config.json', 'r') as f:
                config = json.load(f)
        return jsonify({
            'success': True,
            'config': config
        })
    except Exception as e:
        print(f"Erro ao carregar configuração de e-mail: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/cameras')
def get_cameras():
    try:
        cameras = listar_cameras_disponiveis()
        # Retorna um array de dicionários com id e nome da câmera
        camera_list = [{"id": str(i), "name": f"Câmera {i+1}"} for i in cameras]
        return jsonify({'success': True, 'cameras': camera_list})
    except Exception as e:
        print(f"Erro ao listar câmeras: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/alunos')
def get_alunos():
    try:
        alunos = listar_alunos()
        for aluno in alunos:
            aluno['_id'] = aluno['Id']
            aluno['nome'] = aluno['Nome']
            # Mapeia dados do responsável (podem ser None)
            aluno['resp_telefone'] = aluno.get('resp_telefone')
            aluno['resp_email'] = aluno.get('resp_email')
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
        resp_telefone = data.get('resp_telefone')
        resp_email = data.get('resp_email')
        
        if not all([id_aluno, nome, frame_base64]):
            return jsonify({'success': False, 'error': 'Dados incompletos: ID, nome e foto são obrigatórios.'})
        
        id_aluno = int(id_aluno)
        
        frame_data = base64.b64decode(frame_base64.split(',')[1])
        frame = cv2.imdecode(np.frombuffer(frame_data, np.uint8), cv2.IMREAD_COLOR)
        if frame is None:
             return jsonify({'success': False, 'error': 'Imagem inválida ou corrompida.'})

        cadastrar_aluno(id_aluno, nome, frame, resp_telefone=resp_telefone, resp_email=resp_email)
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
        resp_telefone = data.get('resp_telefone')
        resp_email = data.get('resp_email')
        frame = None
        
        if not nome:
            return jsonify({'success': False, 'error': 'O campo nome é obrigatório.'})

        if frame_base64:
            frame_data = base64.b64decode(frame_base64.split(',')[1])
            frame = cv2.imdecode(np.frombuffer(frame_data, np.uint8), cv2.IMREAD_COLOR)
            if frame is None:
                return jsonify({'success': False, 'error': 'A nova imagem é inválida ou corrompida.'})
        
        editar_aluno(id_aluno, nome, frame, resp_telefone=resp_telefone, resp_email=resp_email)
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
def start_monitoring_pt():
    return start_monitoring()


@app.route('/api/monitoring/start', methods=['POST'])
def start_monitoring():
    try:
        data = request.get_json()
        camera_id = data.get('camera_id')
        test_mode = data.get('test_mode', False)
        
        if test_mode:
            # In test mode, just return success
            return jsonify({'success': True, 'message': 'Modo de teste iniciado'})
        
        # Convert camera_id to int if it's a string
        if camera_id is not None:
            try:
                camera_id = int(camera_id)
            except (ValueError, TypeError):
                camera_id = 0
        else:
            camera_id = 0
        
        # Start real monitoring
        reconhecimento.iniciar_monitoramento(camera_id)
        return jsonify({'success': True, 'message': 'Monitoramento iniciado'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/monitoring/stop', methods=['POST'])
def stop_monitoring():
    try:
        reconhecimento.parar_monitoramento()
        return jsonify({'success': True, 'message': 'Monitoramento parado'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000, use_reloader=False)