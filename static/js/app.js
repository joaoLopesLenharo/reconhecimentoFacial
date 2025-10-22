// static/js/app.js

// --- INICIALIZAÇÃO E VARIÁVEIS GLOBAIS ---
console.log('Initializing WebSocket connection...');
const socket = io();
// Expose socket globally for other modules (e.g., camera-system.js)
window.socket = socket;

// Debug WebSocket connection events
socket.on('connect', () => {
    console.log('WebSocket connected with ID:', socket.id);
});

socket.on('disconnect', () => {
    console.log('WebSocket disconnected');
});

socket.on('connect_error', (error) => {
    console.error('WebSocket connection error:', error);
});
let fotoCapturada = null;
let streamAtivo = null;
let testMode = false;
let multiCameraView = false;
let activeCameras = [];
let testVideos = [];
let isMonitoring = false;

// Configuração de e-mail padrão
let emailConfig = {
    SMTP_SERVER: '',
    SMTP_PORT: 587,
    SMTP_USERNAME: '',
    SMTP_PASSWORD: '',
    SMTP_SENDER_EMAIL: '',
    SMTP_SENDER_NAME: 'Sistema de Monitoramento'
};

// Função para preencher o dropdown de câmeras
function preencherCameras(cameras) {
    const select = document.getElementById('cameraSelect');
    if (!select) return;
    
    // Limpa opções existentes
    select.innerHTML = '';
    
    // Adiciona opção padrão
    const defaultOption = document.createElement('option');
    defaultOption.value = '';
    defaultOption.textContent = 'Selecione uma câmera';
    defaultOption.disabled = true;
    defaultOption.selected = true;
    select.appendChild(defaultOption);
    
    // Adiciona as câmeras disponíveis
    cameras.forEach(camera => {
        const option = document.createElement('option');
        option.value = camera.id;
        option.textContent = camera.name;
        select.appendChild(option);
    });
}

// Função para preencher a tabela de alunos
function preencherTabelaAlunos(alunos) {
    const tbody = document.querySelector('#tabelaAlunos tbody');
    if (!tbody) return;
    
    // Limpa a tabela
    tbody.innerHTML = '';
    
    // Adiciona cada aluno na tabela
    alunos.forEach(aluno => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${aluno.Id}</td>
            <td>${aluno.Nome}</td>
            <td>${aluno.resp_email || 'Não informado'}</td>
            <td>${aluno.resp_telefone || 'Não informado'}</td>
            <td>
                <button class="btn btn-sm btn-warning btn-editar" data-id="${aluno.Id}">
                    <i class="fas fa-edit"></i> Editar
                </button>
                <button class="btn btn-sm btn-danger btn-excluir" data-id="${aluno.Id}">
                    <i class="fas fa-trash"></i> Excluir
                </button>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

// Função para carregar dados iniciais
async function carregarDadosIniciais() {
    try {
        console.log('Carregando configuração de e-mail...');
        const emailResponse = await fetch('/api/email-config');
        if (!emailResponse.ok) throw new Error('Erro ao carregar configuração de e-mail');
        const emailData = await emailResponse.json();
        
        if (emailData.success && emailData.config) {
            console.log('Configuração de e-mail carregada:', emailData.config);
            emailConfig = { ...emailConfig, ...emailData.config };
        } else {
            console.warn('Configuração de e-mail não encontrada, usando padrão');
        }

        console.log('Carregando lista de câmeras...');
        const camerasResponse = await fetch('/api/cameras');
        if (!camerasResponse.ok) throw new Error('Erro ao carregar lista de câmeras');
        const camerasData = await camerasResponse.json();
        console.log('Câmeras disponíveis:', camerasData);
        
        // Preenche o dropdown de câmeras
        if (camerasData.success && camerasData.cameras) {
            preencherCameras(camerasData.cameras);
        }

        console.log('Carregando lista de alunos...');
        const alunosResponse = await fetch('/api/alunos');
        if (!alunosResponse.ok) throw new Error('Erro ao carregar lista de alunos');
        const alunosData = await alunosResponse.json();
        console.log('Alunos carregados:', alunosData);
        
        // Preenche a tabela de alunos
        if (alunosData.success && alunosData.alunos) {
            preencherTabelaAlunos(alunosData.alunos);
        }
        
    } catch (error) {
        console.error('Erro ao carregar dados iniciais:', error);
        mostrarAlerta(`Erro ao carregar dados: ${error.message}`, 'danger');
    }
}

// Inicializa tooltips
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM carregado, iniciando carregamento de dados...');
    
    // Inicializa tooltips do Bootstrap
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Inicializa validação de formulário
    const forms = document.querySelectorAll('.needs-validation');
    Array.from(forms).forEach(form => {
        form.addEventListener('submit', event => {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });
    
    // Inicia carregamento dos dados
    carregarDadosIniciais();
});

// Atualiza um frame de forma segura com tratamento de erros
function updateFrameSafely(element, frameData, cameraId) {
    try {
        // Usa requestAnimationFrame para suavizar a atualização
        requestAnimationFrame(() => {
            try {
                // Verifica se o elemento ainda está no DOM
                if (!document.body.contains(element)) {
                    console.log('Elemento da câmera não encontrado no DOM');
                    return;
                }
                
                // Atualiza a fonte da imagem
                element.src = `data:image/jpeg;base64,${frameData}`;
                
                // Configura tratamento de erros
                element.onerror = () => {
                    console.error('Erro ao carregar o frame da câmera:', cameraId);
                    element.src = '';
                    mostrarEstadoCamera(false, `Erro ao carregar o vídeo da câmera ${cameraId}`);
                };
                
                // Quando a imagem carrega com sucesso
                element.onload = () => {
                    // Remove qualquer mensagem de erro/loading
                    const container = document.getElementById('cameraContainer');
                    if (container) {
                        const errorElements = container.querySelectorAll('.camera-error, .camera-loading');
                        errorElements.forEach(el => el.remove());
                    }
                };
                
            } catch (e) {
                console.error('Erro ao atualizar o frame da câmera:', e);
                mostrarEstadoCamera(false, 'Erro ao exibir o vídeo da câmera');
            }
        });
    } catch (e) {
        console.error('Erro ao agendar atualização do frame:', e);
    }
}

// --- FUNÇÕES AUXILIARES ---
function mostrarAlerta(mensagem, tipo = 'success') {
    const alerta = document.createElement('div');
    alerta.className = `alert alert-${tipo} alert-dismissible fade show alerta-persistente`;
    alerta.innerHTML = `
        ${mensagem}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    document.body.appendChild(alerta);
    setTimeout(() => bootstrap.Alert.getOrCreateInstance(alerta)?.close(), 6000);
}

function pararStreamDeVideo(stream = streamAtivo) {
    if (stream) {
        stream.getTracks().forEach(track => track.stop());
        if (stream === streamAtivo) {
            streamAtivo = null;
        }
    }
}

// Função para carregar vídeos de teste
async function carregarVideosTeste() {
    try {
        const response = await fetch('/api/test-videos');
        if (!response.ok) {
            throw new Error('Erro ao carregar vídeos de teste');
        }
        const data = await response.json();
        return data.videos || [];
    } catch (error) {
        console.error('Erro ao carregar vídeos de teste:', error);
        mostrarAlerta('Erro ao carregar vídeos de teste', 'danger');
        return [];
    }
}

// Função para atualizar a visualização das câmeras
function atualizarVisualizacaoCameras() {
    const container = document.getElementById('cameraContainer');
    if (!container) return;
    
    container.innerHTML = '';
    
    if (multiCameraView && activeCameras.length > 0) {
        // Modo grade para múltiplas câmeras
        const row = document.createElement('div');
        row.className = 'row g-2';
        
        activeCameras.forEach((camera, index) => {
            const col = document.createElement('div');
            col.className = 'col-md-6';
            
            const card = document.createElement('div');
            card.className = 'card bg-dark border-secondary mb-2';
            
            const cardBody = document.createElement('div');
            cardBody.className = 'card-body p-2';
            
            const title = document.createElement('h6');
            title.className = 'card-title text-center small';
            title.textContent = camera.name || `Câmera ${index + 1}`;
            
            const video = document.createElement('img');
            video.id = `cameraFeed-${camera.id}`;
            video.className = 'img-fluid rounded';
            video.alt = `Feed da ${camera.name || `Câmera ${index + 1}`}`;
            
            cardBody.appendChild(title);
            cardBody.appendChild(video);
            card.appendChild(cardBody);
            col.appendChild(card);
            row.appendChild(col);
        });
        
        container.appendChild(row);
    } else if (activeCameras.length > 0) {
        // Modo de visualização única
        const video = document.createElement('img');
        video.id = 'cameraFeed';
        video.className = 'img-fluid';
        video.alt = `Feed da ${activeCameras[0].name || 'Câmera'}`;
        container.appendChild(video);
    } else {
        // Nenhuma câmera ativa
        const alert = document.createElement('div');
        alert.className = 'alert alert-info';
    }
}

// Mostra o estado de carregamento da câmera
function mostrarEstadoCamera(carregando = true, mensagem = '') {
    const container = document.getElementById('cameraContainer');
    if (!container) return;
    
    if (carregando) {
        container.innerHTML = `
            <div class="camera-loading text-center py-5">
                <div class="spinner-border text-primary mb-3" role="status">
                    <span class="visually-hidden">Carregando...</span>
                </div>
                <p class="text-light">${mensagem || 'Iniciando câmera...'}</p>
            </div>
        `;
    } else if (mensagem) {
        container.innerHTML = `
            <div class="camera-error text-center py-5">
                <i class="fas fa-video-slash text-danger mb-3" style="font-size: 3rem;"></i>
                <p class="text-light">${mensagem}</p>
                <button class="btn btn-primary mt-3" onclick="carregarDadosIniciais()">
                    <i class="fas fa-sync"></i> Tentar novamente
                </button>
            </div>
        `;
    } else {
        container.innerHTML = '<img id="cameraFeed" class="img-fluid" alt="Feed da câmera">';
    }
}

// --- LÓGICA DE MONITORAMENTO ---
function configurarMonitoramento() {
    const cameraFeed = document.getElementById('cameraFeed');
    const iniciarBtn = document.getElementById('iniciarMonitoramento');
    const pararBtn = document.getElementById('pararMonitoramento');
    
    if (!iniciarBtn || !pararBtn) {
        console.error('Botões de monitoramento não encontrados');
        return;
    }
    
    // Configura timeout global para operações de câmera
    let cameraTimeout;
    const CAMERA_TIMEOUT_MS = 10000; // 10 segundos
    
    function limparCameraTimeout() {
        if (cameraTimeout) {
            clearTimeout(cameraTimeout);
            cameraTimeout = null;
        }
    }
    
    async function iniciarMonitoramento() {
        try {
            const cameraSelect = document.getElementById('cameraSelect');
            const cameraId = cameraSelect ? cameraSelect.value : null;
            
            // Mostra estado de carregamento
            mostrarEstadoCamera(true, 'Iniciando câmera...');
            
            // Configura timeout
            limparCameraTimeout();
            cameraTimeout = setTimeout(() => {
                mostrarEstadoCamera(false, 'Tempo esgotado ao tentar conectar à câmera.');
                iniciarBtn.disabled = false;
                iniciarBtn.innerHTML = '<i class="fas fa-play"></i> Iniciar Monitoramento';
            }, CAMERA_TIMEOUT_MS);
            
            // Atualiza estado dos botões
            iniciarBtn.disabled = true;
            iniciarBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Iniciando...';
            pararBtn.disabled = true;
            
            if (testMode) {
                // No modo teste, carrega todos os vídeos disponíveis
                testVideos = await carregarVideosTeste();
                if (testVideos.length === 0) {
                    mostrarAlerta('Nenhum vídeo de teste encontrado na pasta test_videos!', 'warning');
                    return;
                }
                
                // Para cada vídeo, inicia um monitoramento
                for (let i = 0; i < testVideos.length; i++) {
                    socket.emit('start_monitoring', { 
                        camera_id: i, 
                        test_mode: true 
                    });
                    
                    // Adiciona a câmera à lista de ativas
                    if (!activeCameras.some(cam => cam.id === i)) {
                        activeCameras.push({ 
                            id: i, 
                            name: testVideos[i].name || `Vídeo ${i+1}` 
                        });
                    }
                }
            } else {
                // Modo normal: usa câmera selecionada
                const cameraId = document.getElementById('cameraSelect').value;
                if (!cameraId) {
                    mostrarAlerta('Selecione uma câmera primeiro!', 'warning');
                    return;
                }
                
                socket.emit('start_monitoring', { 
                    camera_id: cameraId, 
                    test_mode: false 
                });
                
                // Adiciona a câmera à lista de ativas
                if (!activeCameras.some(cam => cam.id === cameraId)) {
                    activeCameras.push({ 
                        id: cameraId, 
                        name: `Câmera ${cameraId}` 
                    });
                }
            }
            
            // Atualiza a interface
            atualizarVisualizacaoCameras();
            isMonitoring = true;
            document.getElementById('iniciarMonitoramento').disabled = true;
            document.getElementById('pararMonitoramento').disabled = false;
        } catch (error) {
            console.error('Erro ao iniciar monitoramento:', error);
            mostrarAlerta(`Erro ao iniciar monitoramento: ${error.message}`, 'danger');
        }
    }
    
    function pararMonitoramento() {
        try {
            // Mostra estado de carregamento
            mostrarEstadoCamera(true, 'Parando monitoramento...');
            
            // Para todas as câmeras ativas
            const stopPromises = activeCameras.map(camera => {
                return new Promise((resolve) => {
                    socket.emit('stop_monitoring', { camera_id: camera.id }, resolve);
                });
            });
            
            // Aguarda todas as paradas serem confirmadas
            Promise.all(stopPromises).then(() => {
                // Limpa a lista de câmeras ativas
                activeCameras = [];
                isMonitoring = false;
                
                // Atualiza a interface
                const iniciarBtn = document.getElementById('iniciarMonitoramento');
                const pararBtn = document.getElementById('pararMonitoramento');
                
                if (iniciarBtn) iniciarBtn.disabled = false;
                if (pararBtn) pararBtn.disabled = true;
                
                // Mostra mensagem de sucesso
                mostrarEstadoCamera(false, 'Monitoramento parado com sucesso.');
                
                // Limpa o estado após 2 segundos
                setTimeout(() => {
                    mostrarEstadoCamera(false);
                }, 2000);
            });
        } catch (error) {
            console.error('Erro ao parar monitoramento:', error);
            mostrarAlerta(`Erro ao parar monitoramento: ${error.message}`, 'danger');
        }
    }
    
    // Configura os eventos dos botões
    if (iniciarBtn) iniciarBtn.addEventListener('click', iniciarMonitoramento);
    if (pararBtn) pararBtn.addEventListener('click', pararMonitoramento);
}

// Configura os eventos de câmera (LEGADO)
if (typeof window.CameraSystem === 'undefined') {
socket.on('camera_ready', (data) => {
    console.log('Câmera pronta:', data);
    limparCameraTimeout();
    mostrarEstadoCamera(false);
    
    const iniciarBtn = document.getElementById('iniciarMonitoramento');
    const pararBtn = document.getElementById('pararMonitoramento');
    
    if (iniciarBtn) iniciarBtn.disabled = true;
    if (pararBtn) pararBtn.disabled = false;
});

socket.on('camera_error', (error) => {
    console.error('Erro na câmera:', error);
    mostrarEstadoCamera(false, `Erro na câmera: ${error.message || 'Erro desconhecido'}`);
    
    const iniciarBtn = document.getElementById('iniciarMonitoramento');
    const pararBtn = document.getElementById('pararMonitoramento');
    
    if (iniciarBtn) iniciarBtn.disabled = false;
    if (pararBtn) pararBtn.disabled = true;
    
    limparCameraTimeout();
});

// --- SOCKET.IO E EVENTOS GERAIS ---
const logsContainer = document.getElementById('logs');

// Configura os eventos do WebSocket (LEGADO)
socket.on('camera_frame', (data) => {
    try {
        // Debug: Log apenas uma vez a cada 60 frames para não sobrecarregar o console
        if (!window.frameCounter) window.frameCounter = 0;
        if (window.frameCounter++ % 60 === 0) {
            console.log('Recebendo frames da câmera:', data.camera_id, 'Tamanho do frame:', data.frame ? data.frame.length + ' bytes' : 'vazio');
        }
        
        const cameraId = data.camera_id;
        
        // Se não houver frame, não faz nada
        if (!data.frame) {
            if (window.frameCounter % 30 === 0) { // Avisa apenas a cada 30 frames ausentes
                console.warn('Frame vazio recebido da câmera:', cameraId);
            }
            return;
        }
        
        if (multiCameraView) {
            // Modo multi-câmera: atualiza o frame específico
            const elementId = `cameraFeed-${cameraId}`;
            let feedElement = document.getElementById(elementId);
            
            // Se não encontrou o elemento, tenta criá-lo
            if (!feedElement) {
                const container = document.getElementById('cameraContainer');
                if (container) {
                    const cameraInfo = activeCameras.find(cam => cam.id == cameraId);
                    const cameraName = cameraInfo ? cameraInfo.name : `Câmera ${cameraId}`;
                    
                    const cameraCard = document.createElement('div');
                    cameraCard.className = 'camera-card';
                    cameraCard.innerHTML = `
                        <div class="camera-header">${cameraName}</div>
                        <img id="${elementId}" class="camera-feed" alt="${cameraName}">
                    `;
                    container.appendChild(cameraCard);
                    feedElement = document.getElementById(elementId);
                }
            }
            
            // Atualiza o frame se o elemento existir
            if (feedElement) {
                updateFrameSafely(feedElement, data.frame, cameraId);
            }
        } else {
            // Modo de visualização única: atualiza apenas se for a câmera ativa
            if (activeCameras.length > 0 && activeCameras[0].id == cameraId) {
                let cameraFeed = document.getElementById('cameraFeed');
                
                // Se não existe, cria o elemento
                if (!cameraFeed) {
                    const container = document.getElementById('cameraContainer');
                    if (container) {
                        container.innerHTML = '<img id="cameraFeed" class="img-fluid" alt="Feed da câmera">';
                        cameraFeed = document.getElementById('cameraFeed');
                    }
                }
                
                // Se encontrou o elemento, atualiza a imagem
                if (cameraFeed) {
                    updateFrameSafely(cameraFeed, data.frame, cameraId);
                }
            }
        }
    } catch (error) {
        console.error('Erro ao processar frame:', error);
    }
});

// Trata erros do servidor
socket.on('error', (error) => {
    console.error('Erro no servidor:', error);
    mostrarAlerta(`Erro: ${error.message || 'Erro desconhecido'}`, 'danger');
});

// --- INICIALIZAÇÃO ---
document.addEventListener('DOMContentLoaded', () => {
    // Configura os controles de visualização
    const testModeToggle = document.getElementById('testModeToggle');
    const multiCameraToggle = document.getElementById('multiCameraView');
    
    if (testModeToggle) {
        testModeToggle.addEventListener('change', (e) => {
            testMode = e.target.checked;
            // Se estiver monitorando, reinicia o monitoramento com o novo modo
            if (isMonitoring) {
                const btnIniciar = document.getElementById('iniciarMonitoramento');
                const btnParar = document.getElementById('pararMonitoramento');
                
                if (btnParar && !btnParar.disabled) {
                    // Simula o clique no botão de parar e depois no de iniciar
                    btnParar.click();
                    setTimeout(() => {
                        btnIniciar.click();
                    }, 500);
                }
            }
        });
    }
    
    if (multiCameraToggle) {
        multiCameraToggle.addEventListener('change', (e) => {
            multiCameraView = e.target.checked;
            // Atualiza a visualização sem reiniciar o monitoramento
            atualizarVisualizacaoCameras();
        });
    }
    
    // Inicializa o monitoramento (LEGADO)
    // Se o novo CameraSystem estiver presente, não inicializa o fluxo legado para evitar conflitos
    if (window.CameraSystem) {
        console.log('[app.js] CameraSystem detectado. Ignorando UI legada de monitoramento.');
    } else {
        configurarMonitoramento();
    }
});

// Expose socket globally
window.socket = socket;