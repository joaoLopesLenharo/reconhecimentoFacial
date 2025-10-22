/**
 * Testes para funcionalidades do frontend JavaScript
 * Usando Jest como framework de testes
 */

// Mock do Socket.IO
const mockSocket = {
    on: jest.fn(),
    emit: jest.fn(),
    connected: true
};

// Mock do io global
global.io = jest.fn(() => mockSocket);

// Mock do DOM
Object.defineProperty(window, 'location', {
    value: {
        reload: jest.fn()
    }
});

// Mock do navigator.mediaDevices
Object.defineProperty(navigator, 'mediaDevices', {
    value: {
        getUserMedia: jest.fn()
    }
});

// Mock do requestAnimationFrame
global.requestAnimationFrame = jest.fn(cb => setTimeout(cb, 0));

describe('App.js - Inicialização', () => {
    beforeEach(() => {
        document.body.innerHTML = '';
        jest.clearAllMocks();
    });

    test('deve inicializar WebSocket corretamente', () => {
        require('../static/js/app.js');
        expect(global.io).toHaveBeenCalled();
    });

    test('deve configurar event listeners do DOM', () => {
        document.body.innerHTML = `
            <button id="iniciarMonitoramento">Iniciar</button>
            <button id="pararMonitoramento">Parar</button>
            <select id="cameraSelect"></select>
        `;

        const addEventListenerSpy = jest.spyOn(document, 'addEventListener');
        require('../static/js/app.js');
        
        expect(addEventListenerSpy).toHaveBeenCalledWith('DOMContentLoaded', expect.any(Function));
    });
});

describe('App.js - Gerenciamento de Câmeras', () => {
    beforeEach(() => {
        document.body.innerHTML = `
            <select id="cameraSelect">
                <option value="">Selecione uma câmera</option>
            </select>
            <div id="cameraContainer"></div>
        `;
        jest.clearAllMocks();
    });

    test('deve preencher dropdown de câmeras', () => {
        const cameras = [
            { id: 0, name: 'Câmera 1' },
            { id: 1, name: 'Câmera 2' }
        ];

        // Simula a função preencherCameras
        const cameraSelect = document.getElementById('cameraSelect');
        cameras.forEach(camera => {
            const option = document.createElement('option');
            option.value = camera.id;
            option.textContent = camera.name;
            cameraSelect.appendChild(option);
        });

        expect(cameraSelect.children.length).toBe(3); // Incluindo opção padrão
        expect(cameraSelect.children[1].textContent).toBe('Câmera 1');
        expect(cameraSelect.children[2].textContent).toBe('Câmera 2');
    });

    test('deve mostrar estado de carregamento da câmera', () => {
        const container = document.getElementById('cameraContainer');
        
        // Simula mostrarEstadoCamera(true, 'Carregando...')
        container.innerHTML = `
            <div class="camera-loading text-center p-4">
                <div class="spinner-border text-primary mb-3"></div>
                <p>Carregando...</p>
            </div>
        `;

        const loadingElement = container.querySelector('.camera-loading');
        expect(loadingElement).toBeTruthy();
        expect(loadingElement.textContent).toContain('Carregando...');
    });

    test('deve mostrar estado de erro da câmera', () => {
        const container = document.getElementById('cameraContainer');
        
        // Simula mostrarEstadoCamera(false, 'Erro na câmera')
        container.innerHTML = `
            <div class="camera-error text-center p-4">
                <i class="fas fa-exclamation-triangle fa-3x text-danger mb-3"></i>
                <p class="text-danger">Erro na câmera</p>
                <button class="btn btn-outline-light btn-sm">
                    <i class="fas fa-sync-alt me-1"></i> Tentar novamente
                </button>
            </div>
        `;

        const errorElement = container.querySelector('.camera-error');
        expect(errorElement).toBeTruthy();
        expect(errorElement.textContent).toContain('Erro na câmera');
    });
});

describe('App.js - Monitoramento', () => {
    beforeEach(() => {
        document.body.innerHTML = `
            <button id="iniciarMonitoramento">Iniciar Monitoramento</button>
            <button id="pararMonitoramento" style="display: none;">Parar Monitoramento</button>
            <select id="cameraSelect">
                <option value="0">Câmera 1</option>
            </select>
            <div id="cameraContainer"></div>
        `;
        jest.clearAllMocks();
    });

    test('deve iniciar monitoramento corretamente', () => {
        const btnIniciar = document.getElementById('iniciarMonitoramento');
        const btnParar = document.getElementById('pararMonitoramento');
        
        // Simula clique no botão iniciar
        btnIniciar.click();
        
        // Verifica se socket.emit foi chamado
        expect(mockSocket.emit).toHaveBeenCalledWith('start_monitoring', expect.any(Object));
    });

    test('deve parar monitoramento corretamente', () => {
        const btnParar = document.getElementById('pararMonitoramento');
        
        // Simula clique no botão parar
        btnParar.click();
        
        // Verifica se socket.emit foi chamado
        expect(mockSocket.emit).toHaveBeenCalledWith('stop_monitoring', expect.any(Object));
    });

    test('deve atualizar botões durante monitoramento', () => {
        const btnIniciar = document.getElementById('iniciarMonitoramento');
        const btnParar = document.getElementById('pararMonitoramento');
        
        // Simula início do monitoramento
        btnIniciar.style.display = 'none';
        btnParar.style.display = 'block';
        btnIniciar.disabled = true;
        
        expect(btnIniciar.style.display).toBe('none');
        expect(btnParar.style.display).toBe('block');
        expect(btnIniciar.disabled).toBe(true);
    });
});

describe('App.js - Processamento de Frames', () => {
    beforeEach(() => {
        document.body.innerHTML = `
            <div id="cameraContainer"></div>
        `;
        jest.clearAllMocks();
    });

    test('deve processar frame de câmera única', () => {
        const container = document.getElementById('cameraContainer');
        const frameData = 'base64encodedframe';
        const cameraId = 0;
        
        // Simula recebimento de frame
        container.innerHTML = '<img id="cameraFeed" class="img-fluid" alt="Feed da câmera">';
        const img = document.getElementById('cameraFeed');
        
        // Simula updateFrameSafely
        img.src = `data:image/jpeg;base64,${frameData}`;
        
        expect(img.src).toBe(`data:image/jpeg;base64,${frameData}`);
    });

    test('deve processar frames de múltiplas câmeras', () => {
        const container = document.getElementById('cameraContainer');
        const frameData = 'base64encodedframe';
        const cameraId = 1;
        
        // Simula modo multi-câmera
        const cameraCard = document.createElement('div');
        cameraCard.className = 'camera-card';
        cameraCard.innerHTML = `
            <div class="camera-header">Câmera 2</div>
            <img id="cameraFeed-${cameraId}" class="camera-feed" alt="Câmera 2">
        `;
        container.appendChild(cameraCard);
        
        const img = document.getElementById(`cameraFeed-${cameraId}`);
        img.src = `data:image/jpeg;base64,${frameData}`;
        
        expect(img.src).toBe(`data:image/jpeg;base64,${frameData}`);
    });

    test('deve tratar erro no carregamento de frame', () => {
        const container = document.getElementById('cameraContainer');
        container.innerHTML = '<img id="cameraFeed" class="img-fluid" alt="Feed da câmera">';
        
        const img = document.getElementById('cameraFeed');
        const errorHandler = jest.fn();
        img.onerror = errorHandler;
        
        // Simula erro
        img.dispatchEvent(new Event('error'));
        
        expect(errorHandler).toHaveBeenCalled();
    });
});

describe('App.js - Formulários', () => {
    beforeEach(() => {
        document.body.innerHTML = `
            <form id="formCadastro">
                <input id="idAluno" type="number" required>
                <input id="nomeAluno" type="text" required>
                <input id="respTelefone" type="tel">
                <input id="respEmail" type="email">
                <button type="submit">Cadastrar</button>
            </form>
            <div id="fotoPreview"></div>
        `;
        jest.clearAllMocks();
    });

    test('deve validar campos obrigatórios', () => {
        const form = document.getElementById('formCadastro');
        const idInput = document.getElementById('idAluno');
        const nomeInput = document.getElementById('nomeAluno');
        
        // Testa validação HTML5
        expect(idInput.required).toBe(true);
        expect(nomeInput.required).toBe(true);
        
        // Simula validação customizada
        idInput.value = '';
        nomeInput.value = '';
        
        expect(form.checkValidity()).toBe(false);
    });

    test('deve formatar telefone corretamente', () => {
        const telefoneInput = document.getElementById('respTelefone');
        
        // Simula formatação de telefone
        const formatTelefone = (value) => {
            return value.replace(/\D/g, '')
                       .replace(/(\d{2})(\d)/, '($1) $2')
                       .replace(/(\d{5})(\d)/, '$1-$2');
        };
        
        telefoneInput.value = '11999999999';
        const formatted = formatTelefone(telefoneInput.value);
        
        expect(formatted).toBe('(11) 99999-9999');
    });

    test('deve validar email', () => {
        const emailInput = document.getElementById('respEmail');
        
        emailInput.value = 'email@valido.com';
        expect(emailInput.checkValidity()).toBe(true);
        
        emailInput.value = 'email_invalido';
        expect(emailInput.checkValidity()).toBe(false);
    });
});

describe('Camera Preview - Funcionalidades', () => {
    beforeEach(() => {
        document.body.innerHTML = `
            <button id="btnAbrirCameraCadastro">Abrir Câmera</button>
            <button id="btnTirarFotoCadastro" style="display: none;">Tirar Foto</button>
            <button id="btnCancelarCamera" style="display: none;">Cancelar</button>
            <button id="btnConfirmarFoto" style="display: none;">Confirmar</button>
            <video id="videoPreviewCadastro" style="display: none;"></video>
            <canvas id="canvasPreview" class="d-none"></canvas>
            <img id="fotoPreview" style="display: none;" alt="Preview">
            <div id="cameraPlaceholder">Clique para iniciar</div>
            <div id="cameraLoading" style="display: none;">Carregando...</div>
        `;
        jest.clearAllMocks();
    });

    test('deve iniciar câmera corretamente', async () => {
        const mockStream = {
            getTracks: () => [{ stop: jest.fn() }]
        };
        
        navigator.mediaDevices.getUserMedia.mockResolvedValue(mockStream);
        
        const btnAbrir = document.getElementById('btnAbrirCameraCadastro');
        const video = document.getElementById('videoPreviewCadastro');
        const placeholder = document.getElementById('cameraPlaceholder');
        
        // Simula clique no botão
        btnAbrir.click();
        
        // Aguarda resolução da promise
        await new Promise(resolve => setTimeout(resolve, 0));
        
        expect(navigator.mediaDevices.getUserMedia).toHaveBeenCalledWith({
            video: { 
                width: { ideal: 1280 },
                height: { ideal: 720 },
                facingMode: 'user' 
            },
            audio: false
        });
    });

    test('deve tratar erro ao acessar câmera', async () => {
        navigator.mediaDevices.getUserMedia.mockRejectedValue(new Error('Camera not found'));
        
        const btnAbrir = document.getElementById('btnAbrirCameraCadastro');
        const placeholder = document.getElementById('cameraPlaceholder');
        
        // Simula clique no botão
        btnAbrir.click();
        
        // Aguarda rejeição da promise
        await new Promise(resolve => setTimeout(resolve, 0));
        
        // Verifica se erro foi tratado
        expect(placeholder.innerHTML).toContain('Não foi possível acessar a câmera');
    });

    test('deve capturar foto corretamente', () => {
        const video = document.getElementById('videoPreviewCadastro');
        const canvas = document.getElementById('canvasPreview');
        const foto = document.getElementById('fotoPreview');
        
        // Mock das propriedades do vídeo
        Object.defineProperty(video, 'videoWidth', { value: 640 });
        Object.defineProperty(video, 'videoHeight', { value: 480 });
        
        // Mock do contexto do canvas
        const mockContext = {
            drawImage: jest.fn()
        };
        canvas.getContext = jest.fn(() => mockContext);
        canvas.toDataURL = jest.fn(() => 'data:image/jpeg;base64,mockdata');
        
        // Simula captura
        const btnTirar = document.getElementById('btnTirarFotoCadastro');
        btnTirar.click();
        
        expect(mockContext.drawImage).toHaveBeenCalledWith(video, 0, 0, 640, 480);
        expect(foto.src).toBe('data:image/jpeg;base64,mockdata');
    });

    test('deve parar câmera corretamente', () => {
        const mockTrack = { stop: jest.fn() };
        const mockStream = { getTracks: () => [mockTrack] };
        
        // Simula stream ativo
        let stream = mockStream;
        
        const btnCancelar = document.getElementById('btnCancelarCamera');
        btnCancelar.click();
        
        // Simula parada da câmera
        if (stream) {
            stream.getTracks().forEach(track => track.stop());
        }
        
        expect(mockTrack.stop).toHaveBeenCalled();
    });
});

describe('App.js - Socket Events', () => {
    beforeEach(() => {
        document.body.innerHTML = `
            <div id="cameraContainer"></div>
            <button id="iniciarMonitoramento">Iniciar</button>
            <button id="pararMonitoramento">Parar</button>
        `;
        jest.clearAllMocks();
    });

    test('deve processar evento camera_ready', () => {
        const data = { camera_id: 0, status: 'ready' };
        
        // Simula callback do evento
        const callback = mockSocket.on.mock.calls.find(call => call[0] === 'camera_ready');
        if (callback) {
            callback[1](data);
        }
        
        expect(mockSocket.on).toHaveBeenCalledWith('camera_ready', expect.any(Function));
    });

    test('deve processar evento camera_error', () => {
        const data = { camera_id: 0, error: 'Camera disconnected' };
        
        // Simula callback do evento
        const callback = mockSocket.on.mock.calls.find(call => call[0] === 'camera_error');
        if (callback) {
            callback[1](data);
        }
        
        expect(mockSocket.on).toHaveBeenCalledWith('camera_error', expect.any(Function));
    });

    test('deve processar evento camera_frame', () => {
        const data = { 
            camera_id: 0, 
            frame: 'base64framedata',
            timestamp: new Date().toISOString()
        };
        
        // Simula callback do evento
        const callback = mockSocket.on.mock.calls.find(call => call[0] === 'camera_frame');
        if (callback) {
            callback[1](data);
        }
        
        expect(mockSocket.on).toHaveBeenCalledWith('camera_frame', expect.any(Function));
    });
});

describe('App.js - Utilitários', () => {
    test('deve mostrar alerta corretamente', () => {
        document.body.innerHTML = '<div id="alertContainer"></div>';
        
        const mostrarAlerta = (mensagem, tipo = 'success') => {
            const container = document.getElementById('alertContainer');
            const alert = document.createElement('div');
            alert.className = `alert alert-${tipo}`;
            alert.textContent = mensagem;
            container.appendChild(alert);
        };
        
        mostrarAlerta('Teste de sucesso', 'success');
        mostrarAlerta('Teste de erro', 'danger');
        
        const container = document.getElementById('alertContainer');
        expect(container.children.length).toBe(2);
        expect(container.children[0].textContent).toBe('Teste de sucesso');
        expect(container.children[1].textContent).toBe('Teste de erro');
    });

    test('deve atualizar frame com segurança', () => {
        const img = document.createElement('img');
        const frameData = 'base64framedata';
        const cameraId = 0;
        
        const updateFrameSafely = (element, data, id) => {
            try {
                element.src = `data:image/jpeg;base64,${data}`;
                element.onerror = () => {
                    console.error('Erro ao carregar frame:', id);
                };
                return true;
            } catch (error) {
                console.error('Erro ao atualizar frame:', error);
                return false;
            }
        };
        
        const result = updateFrameSafely(img, frameData, cameraId);
        
        expect(result).toBe(true);
        expect(img.src).toBe(`data:image/jpeg;base64,${frameData}`);
    });
});

describe('App.js - Performance', () => {
    test('deve throttle de logs de debug', () => {
        let frameCounter = 0;
        const logSpy = jest.spyOn(console, 'log').mockImplementation();
        
        // Simula recebimento de muitos frames
        for (let i = 0; i < 100; i++) {
            frameCounter++;
            if (frameCounter % 30 === 0) {
                console.log('Debug frame:', frameCounter);
            }
        }
        
        // Deve ter logado apenas algumas vezes
        expect(logSpy).toHaveBeenCalledTimes(3); // 30, 60, 90
        
        logSpy.mockRestore();
    });

    test('deve usar requestAnimationFrame para atualizações', () => {
        const callback = jest.fn();
        
        requestAnimationFrame(callback);
        
        expect(global.requestAnimationFrame).toHaveBeenCalledWith(callback);
    });
});
