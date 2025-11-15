// static/js/app.js

// --- FUNÇÕES AUXILIARES (definidas primeiro para garantir disponibilidade) ---
function mostrarAlerta(mensagem, tipo = 'success') {
    const alerta = document.createElement('div');
    alerta.className = `alert alert-${tipo} alert-dismissible fade show alerta-persistente`;
    alerta.innerHTML = `
        ${mensagem}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    document.body.appendChild(alerta);
    setTimeout(() => {
        const bsAlert = bootstrap.Alert.getOrCreateInstance(alerta);
        if (bsAlert) bsAlert.close();
    }, 6000);
}

// Expor mostrarAlerta globalmente imediatamente
window.mostrarAlerta = mostrarAlerta;

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
    console.log('[preencherTabelaAlunos] Iniciando preenchimento da tabela...');
    console.log('[preencherTabelaAlunos] Dados recebidos:', alunos);
    console.log('[preencherTabelaAlunos] Tipo:', typeof alunos);
    console.log('[preencherTabelaAlunos] É array?', Array.isArray(alunos));
    console.log('[preencherTabelaAlunos] Tamanho:', alunos ? alunos.length : 'null/undefined');
    
    const tbody = document.querySelector('#tabelaAlunos tbody');
    if (!tbody) {
        console.error('[preencherTabelaAlunos] ERRO: Elemento #tabelaAlunos tbody não encontrado!');
        console.error('[preencherTabelaAlunos] Tentando encontrar elementos relacionados...');
        const table = document.querySelector('#tabelaAlunos');
        console.log('[preencherTabelaAlunos] Tabela encontrada?', !!table);
        if (table) {
            console.log('[preencherTabelaAlunos] HTML da tabela:', table.outerHTML.substring(0, 200));
        }
        return;
    }
    
    console.log('[preencherTabelaAlunos] Tbody encontrado, limpando conteúdo...');
    
    // Limpa a tabela
    tbody.innerHTML = '';
    
    if (!Array.isArray(alunos)) {
        console.error('[preencherTabelaAlunos] ERRO: Dados recebidos não são um array:', typeof alunos, alunos);
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td colspan="5" class="text-center text-danger">
                Erro: Dados inválidos recebidos do servidor. Tipo: ${typeof alunos}
            </td>
        `;
        tbody.appendChild(tr);
        return;
    }
    
    if (alunos.length === 0) {
        console.log('[preencherTabelaAlunos] Nenhum aluno encontrado no banco de dados');
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td colspan="5" class="text-center text-muted">
                Nenhum aluno cadastrado até o momento.
            </td>
        `;
        tbody.appendChild(tr);
        return;
    }
    
    console.log(`[preencherTabelaAlunos] Processando ${alunos.length} aluno(s)...`);
    
    // Adiciona cada aluno na tabela
    alunos.forEach((aluno, index) => {
        try {
            // Suporta tanto Id quanto _id, tanto Nome quanto nome
            const alunoId = aluno.Id || aluno._id || aluno.id || 'N/A';
            const alunoNome = aluno.Nome || aluno.nome || 'Sem nome';
            const alunoTelefone = aluno.resp_telefone || aluno.telefone || null;
            const alunoEmail = aluno.resp_email || aluno.email || null;
            
            console.log(`[preencherTabelaAlunos] Processando aluno ${index + 1}/${alunos.length}:`, {
                id: alunoId,
                nome: alunoNome,
                telefone: alunoTelefone,
                email: alunoEmail,
                dadosCompletos: aluno
            });
            
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${alunoId}</td>
                <td>${alunoNome}</td>
                <td>${alunoTelefone || 'Não informado'}</td>
                <td>${alunoEmail || 'Não informado'}</td>
                <td>
                    <button class="btn btn-sm btn-warning btn-editar" data-id="${alunoId}" data-nome="${alunoNome}" data-telefone="${alunoTelefone || ''}" data-email="${alunoEmail || ''}">
                        <i class="fas fa-edit"></i> Editar
                    </button>
                    <button class="btn btn-sm btn-danger btn-excluir" data-id="${alunoId}" data-nome="${alunoNome}">
                        <i class="fas fa-trash"></i> Excluir
                    </button>
                </td>
            `;
            tbody.appendChild(tr);
            console.log(`[preencherTabelaAlunos] Aluno ${index + 1} adicionado à tabela`);
        } catch (error) {
            console.error(`[preencherTabelaAlunos] Erro ao processar aluno ${index + 1}:`, error);
            console.error(`[preencherTabelaAlunos] Dados do aluno problemático:`, aluno);
        }
    });
    
    console.log(`[preencherTabelaAlunos] Tabela preenchida com ${alunos.length} aluno(s)`);
    console.log(`[preencherTabelaAlunos] Total de linhas na tabela agora: ${tbody.children.length}`);
    
    // Configura event listeners para os botões
    configurarEventListenersTabela();
    console.log('[preencherTabelaAlunos] Event listeners configurados');
}

// Função para configurar event listeners da tabela
function configurarEventListenersTabela() {
    // Event listeners para editar
    document.querySelectorAll('.btn-editar').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const alunoId = btn.getAttribute('data-id');
            const alunoNome = btn.getAttribute('data-nome');
            const alunoTelefone = btn.getAttribute('data-telefone');
            const alunoEmail = btn.getAttribute('data-email');
            abrirModalEditar(alunoId, alunoNome, alunoTelefone, alunoEmail);
        });
    });
    
    // Event listeners para excluir
    document.querySelectorAll('.btn-excluir').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            const alunoId = btn.getAttribute('data-id');
            const alunoNome = btn.getAttribute('data-nome');
            if (confirm(`Tem certeza que deseja excluir o aluno "${alunoNome}" (ID: ${alunoId})?`)) {
                await excluirAluno(alunoId);
            }
        });
    });
}

// Função para abrir modal de edição
function abrirModalEditar(id, nome, telefone, email) {
    document.getElementById('editNome').value = nome || '';
    document.getElementById('editRespTelefone').value = telefone || '';
    document.getElementById('editRespEmail').value = email || '';
    
    // Armazena o ID do aluno no botão de salvar
    const btnSalvar = document.getElementById('btnSalvarEdit');
    btnSalvar.setAttribute('data-aluno-id', id);
    
    // Carrega câmeras disponíveis no select de edição
    carregarCamerasParaEdicao();
    
    // Abre o modal
    const modal = new bootstrap.Modal(document.getElementById('modalEditar'));
    modal.show();
}

// Função para carregar câmeras no select de edição
async function carregarCamerasParaEdicao() {
    const select = document.getElementById('cameraSelectEdit');
    if (!select) return;
    
    try {
        const response = await fetch('/api/cameras');
        const data = await response.json();
        
        select.innerHTML = '<option value="">Selecione uma câmera...</option>';
        if (data.success && data.cameras) {
            data.cameras.forEach(camera => {
                const option = document.createElement('option');
                option.value = camera.id;
                option.textContent = camera.name;
                select.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Erro ao carregar câmeras para edição:', error);
    }
}

// Função para excluir aluno
async function excluirAluno(id) {
    try {
        const response = await fetch(`/api/alunos/${id}`, {
            method: 'DELETE'
        });
        
        const result = await response.json();
        
        if (result.success) {
            mostrarAlerta('Aluno excluído com sucesso!', 'success');
            await carregarAlunos();
        } else {
            throw new Error(result.error || 'Erro ao excluir aluno');
        }
    } catch (error) {
        console.error('Erro ao excluir aluno:', error);
        mostrarAlerta(`Erro ao excluir aluno: ${error.message}`, 'danger');
    }
}

// Função para atualizar lista de alunos (exposta globalmente)
async function atualizarListaAlunos() {
    await carregarAlunos();
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

        await carregarAlunos();
    } catch (error) {
        console.error('Erro ao carregar dados iniciais:', error);
        mostrarAlerta(`Erro ao carregar dados: ${error.message}`, 'danger');
    }
}

async function carregarAlunos() {
    try {
        console.log('[carregarAlunos] Iniciando carregamento...');
        const response = await fetch('/api/alunos', {
            method: 'GET',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            },
            cache: 'no-cache'
        });
        
        console.log('[carregarAlunos] Resposta HTTP:', response.status, response.statusText);
        console.log('[carregarAlunos] Content-Type:', response.headers.get('Content-Type'));
        
        if (!response.ok) {
            const errorText = await response.text();
            console.error('[carregarAlunos] Erro na resposta:', errorText);
            throw new Error(`Erro ao carregar lista de alunos: ${response.status} ${response.statusText}`);
        }
        
        const responseText = await response.text();
        console.log('[carregarAlunos] Resposta texto bruto:', responseText.substring(0, 500));
        
        let data;
        try {
            data = JSON.parse(responseText);
        } catch (parseError) {
            console.error('[carregarAlunos] Erro ao fazer parse do JSON:', parseError);
            console.error('[carregarAlunos] Texto recebido:', responseText);
            throw new Error('Resposta do servidor não é um JSON válido');
        }
        
        console.log('[carregarAlunos] Dados parseados:', data);
        console.log('[carregarAlunos] Tipo de data:', typeof data);
        console.log('[carregarAlunos] data.success:', data.success);
        console.log('[carregarAlunos] data.alunos:', data.alunos);
        console.log('[carregarAlunos] É array?', Array.isArray(data.alunos));
        console.log('[carregarAlunos] Tipo de data.alunos:', typeof data.alunos);
        
        // Verifica se a resposta é válida
        if (data === null || data === undefined) {
            throw new Error('Resposta do servidor está vazia ou inválida');
        }
        
        // Aceita tanto success === true quanto success === undefined (para compatibilidade)
        if (data.success === true || (data.success === undefined && data.alunos !== undefined)) {
            const alunosArray = data.alunos || [];
            console.log(`[carregarAlunos] Encontrados ${alunosArray.length} aluno(s) no array`);
            
            if (Array.isArray(alunosArray)) {
                if (alunosArray.length > 0) {
                    console.log('[carregarAlunos] Primeiro aluno do array:', alunosArray[0]);
                }
                preencherTabelaAlunos(alunosArray);
            } else {
                console.error('[carregarAlunos] data.alunos não é um array:', alunosArray);
                console.error('[carregarAlunos] Tipo:', typeof alunosArray);
                throw new Error('Dados de alunos não estão no formato esperado (não é um array)');
            }
        } else {
            console.error('[carregarAlunos] Resposta inválida:', {
                success: data.success,
                alunos: data.alunos,
                error: data.error,
                dadosCompletos: data
            });
            throw new Error(data.error || 'Resposta inválida ao carregar alunos');
        }
    } catch (error) {
        console.error('[carregarAlunos] Erro ao carregar alunos:', error);
        console.error('[carregarAlunos] Stack trace:', error.stack);
        if (typeof mostrarAlerta === 'function') {
            mostrarAlerta(`Erro ao carregar alunos: ${error.message}`, 'danger');
        } else {
            alert(`Erro ao carregar alunos: ${error.message}`);
        }
        preencherTabelaAlunos([]);
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
    
    // Configura listener para carregar alunos quando a aba de listagem for aberta
    const listaTab = document.getElementById('lista-tab');
    const listaPane = document.getElementById('lista');
    const myTab = document.getElementById('myTab');
    
    if (listaTab && listaPane) {
        console.log('[DOMContentLoaded] Configurando listeners para aba de listagem...');
        
        // Listener usando evento Bootstrap
        listaTab.addEventListener('shown.bs.tab', (e) => {
            console.log('[EVENT] Aba de listagem aberta (shown.bs.tab)');
            carregarAlunos();
        });
        
        // Listener usando evento do tab-pane
        listaPane.addEventListener('shown.bs.tab', (e) => {
            console.log('[EVENT] Tab-pane de listagem mostrado (shown.bs.tab)');
            carregarAlunos();
        });
        
        // Listener no container pai para capturar todos os eventos de tab
        if (myTab) {
            myTab.addEventListener('shown.bs.tab', (e) => {
                const targetId = e.target.getAttribute('data-bs-target');
                if (targetId === '#lista') {
                    console.log('[EVENT] Aba de listagem detectada via container pai');
                    carregarAlunos();
                }
            });
        }
        
        // Fallback: escuta o evento 'click' diretamente
        listaTab.addEventListener('click', () => {
            console.log('[EVENT] Clique na aba de listagem detectado');
            setTimeout(() => {
                if (listaPane.classList.contains('active') && listaPane.classList.contains('show')) {
                    console.log('[EVENT] Aba de listagem está ativa após clique (fallback)');
                    carregarAlunos();
                }
            }, 150);
        });
    } else {
        console.error('[DOMContentLoaded] ERRO: Elementos da aba de listagem não encontrados!');
        console.error('[DOMContentLoaded] listaTab:', !!listaTab, 'listaPane:', !!listaPane);
    }
    
    // Carrega alunos se a aba de listagem já estiver ativa ao carregar a página
    if (listaPane && listaPane.classList.contains('active') && listaPane.classList.contains('show')) {
        console.log('[DOMContentLoaded] Aba de listagem já está ativa ao carregar, carregando alunos...');
        setTimeout(() => carregarAlunos(), 500); // Pequeno delay para garantir que tudo está pronto
    }
    
    // Inicia carregamento dos dados
    carregarDadosIniciais();
});

// mostrarAlerta já está definida no topo do arquivo

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
// mostrarAlerta já está definida acima, não duplicar

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
                    limparCameraTimeout();
                    iniciarBtn.disabled = false;
                    iniciarBtn.innerHTML = '<i class="fas fa-play"></i> Iniciar Monitoramento';
                    return;
                }
                
                // Para cada vídeo, inicia um monitoramento
                for (let i = 0; i < testVideos.length; i++) {
                    socket.emit('start_monitoring', { 
                        camera_id: i, 
                        test_mode: true,
                        video_filename: testVideos[i].filename || testVideos[i].name
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
} // Fecha if (typeof window.CameraSystem === 'undefined')

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

    // Configura botão de atualizar lista de alunos
    const btnAtualizarAlunos = document.getElementById('btnAtualizarListaAlunos');
    if (btnAtualizarAlunos) {
        console.log('[DOMContentLoaded 2] Configurando listener para botão Atualizar Lista...');
        btnAtualizarAlunos.addEventListener('click', async (e) => {
            e.preventDefault();
            console.log('[EVENT] Botão Atualizar Lista clicado');
            btnAtualizarAlunos.disabled = true;
            btnAtualizarAlunos.innerHTML = '<span class="spinner-border spinner-border-sm" role="status"></span> Atualizando...';
            try {
                await carregarAlunos();
            } catch (error) {
                console.error('[EVENT] Erro ao atualizar lista:', error);
            } finally {
                btnAtualizarAlunos.disabled = false;
                btnAtualizarAlunos.innerHTML = '<i class="fas fa-sync"></i> Atualizar Lista';
            }
        });
    } else {
        console.error('[DOMContentLoaded 2] ERRO: Botão btnAtualizarListaAlunos não encontrado!');
    }
    
    // Configura event listener para salvar edição
    const btnSalvarEdit = document.getElementById('btnSalvarEdit');
    if (btnSalvarEdit) {
        btnSalvarEdit.addEventListener('click', async () => {
            await salvarEdicaoAluno();
        });
    }
    
    // Configura event listeners para câmera de edição
    const btnAbrirCameraEdit = document.getElementById('btnAbrirCameraEdit');
    const btnTirarFotoEdit = document.getElementById('btnTirarFotoEdit');
    const videoPreviewEdit = document.getElementById('videoPreviewEdit');
    const fotoPreviewEdit = document.getElementById('fotoPreviewEdit');
    
    let streamEdit = null;
    let fotoEditData = null;
    
    if (btnAbrirCameraEdit) {
        btnAbrirCameraEdit.addEventListener('click', async () => {
            try {
                streamEdit = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
                if (videoPreviewEdit) {
                    videoPreviewEdit.srcObject = streamEdit;
                    videoPreviewEdit.style.display = 'block';
                    videoPreviewEdit.play();
                }
                btnAbrirCameraEdit.style.display = 'none';
                btnTirarFotoEdit.style.display = 'block';
            } catch (error) {
                console.error('Erro ao abrir câmera:', error);
                mostrarAlerta('Erro ao acessar a câmera', 'danger');
            }
        });
    }
    
    if (btnTirarFotoEdit) {
        btnTirarFotoEdit.addEventListener('click', () => {
            if (videoPreviewEdit && videoPreviewEdit.readyState === videoPreviewEdit.HAVE_ENOUGH_DATA) {
                const canvas = document.createElement('canvas');
                canvas.width = videoPreviewEdit.videoWidth;
                canvas.height = videoPreviewEdit.videoHeight;
                canvas.getContext('2d').drawImage(videoPreviewEdit, 0, 0);
                fotoEditData = canvas.toDataURL('image/jpeg');
                
                if (fotoPreviewEdit) {
                    fotoPreviewEdit.src = fotoEditData;
                    fotoPreviewEdit.style.display = 'block';
                }
                if (videoPreviewEdit) videoPreviewEdit.style.display = 'none';
                
                if (streamEdit) {
                    streamEdit.getTracks().forEach(track => track.stop());
                    streamEdit = null;
                }
                
                btnTirarFotoEdit.style.display = 'none';
                btnAbrirCameraEdit.textContent = 'Refazer Foto';
                btnAbrirCameraEdit.style.display = 'block';
            }
        });
    }
    
    // Limpa stream ao fechar modal
    const modalEditar = document.getElementById('modalEditar');
    if (modalEditar) {
        modalEditar.addEventListener('hidden.bs.modal', () => {
            if (streamEdit) {
                streamEdit.getTracks().forEach(track => track.stop());
                streamEdit = null;
            }
            fotoEditData = null;
            if (videoPreviewEdit) videoPreviewEdit.style.display = 'none';
            if (fotoPreviewEdit) fotoPreviewEdit.style.display = 'none';
            btnAbrirCameraEdit.textContent = 'Abrir Câmera para Nova Foto';
        });
    }
}); // Fecha DOMContentLoaded

// Função para salvar edição do aluno
async function salvarEdicaoAluno() {
    const btnSalvar = document.getElementById('btnSalvarEdit');
    const alunoId = btnSalvar.getAttribute('data-aluno-id');
    
    if (!alunoId) {
        mostrarAlerta('Erro: ID do aluno não encontrado', 'danger');
        return;
    }
    
    const nome = document.getElementById('editNome').value.trim();
    if (!nome) {
        mostrarAlerta('O nome do aluno é obrigatório', 'warning');
        return;
    }
    
    const telefone = document.getElementById('editRespTelefone').value.trim() || null;
    const email = document.getElementById('editRespEmail').value.trim() || null;
    
    // Obtém foto se foi capturada
    const fotoPreviewEdit = document.getElementById('fotoPreviewEdit');
    let frameBase64 = null;
    if (fotoPreviewEdit && fotoPreviewEdit.style.display !== 'none' && fotoPreviewEdit.src) {
        frameBase64 = fotoPreviewEdit.src;
    }
    
    try {
        btnSalvar.disabled = true;
        btnSalvar.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Salvando...';
        
        const response = await fetch(`/api/alunos/${alunoId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                nome: nome,
                resp_telefone: telefone,
                resp_email: email,
                frame: frameBase64
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            mostrarAlerta('Aluno atualizado com sucesso!', 'success');
            const modal = bootstrap.Modal.getInstance(document.getElementById('modalEditar'));
            modal.hide();
            await carregarAlunos();
        } else {
            throw new Error(result.error || 'Erro ao atualizar aluno');
        }
    } catch (error) {
        console.error('Erro ao salvar edição:', error);
        mostrarAlerta(`Erro ao salvar edição: ${error.message}`, 'danger');
    } finally {
        btnSalvar.disabled = false;
        btnSalvar.innerHTML = 'Salvar Alterações';
    }
}

// Expose socket and functions globally
window.socket = socket;
window.carregarAlunos = carregarAlunos;
window.atualizarListaAlunos = atualizarListaAlunos;