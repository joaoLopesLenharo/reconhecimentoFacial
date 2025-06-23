// Inicialização do Socket.IO
const socket = io();

// Variáveis globais
let fotoPreview = null;
let alunoEditando = null;
let alertasAtivos = new Set();

// Elementos da interface
const cameraFeed = document.getElementById('cameraFeed');
const logsContainer = document.getElementById('logs');
const fotoPreviewImg = document.getElementById('fotoPreview');
const fotoPreviewEdit = document.getElementById('fotoPreviewEdit');

// Funções auxiliares
function mostrarAlerta(mensagem, tipo = 'success', persistente = false) {
    const alerta = document.createElement('div');
    alerta.className = `alert alert-${tipo} alert-dismissible fade show`;
    if (persistente) {
        alerta.classList.add('alerta-persistente');
    }
    alerta.innerHTML = `
        ${mensagem}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    document.querySelector('.container').insertBefore(alerta, document.querySelector('.tab-content'));
    
    if (!persistente) {
        setTimeout(() => alerta.remove(), 5000);
    }
    
    return alerta;
}

function mostrarAlertaPersistente(mensagem, tipo = 'warning') {
    const alerta = mostrarAlerta(mensagem, tipo, true);
    alertasAtivos.add(alerta);
    return alerta;
}

function removerAlertaPersistente(alerta) {
    if (alertasAtivos.has(alerta)) {
        alerta.remove();
        alertasAtivos.delete(alerta);
    }
}

function atualizarListaCameras() {
    fetch('/api/cameras')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const select = document.getElementById('cameraSelect');
                select.innerHTML = data.cameras.map((cam, index) => 
                    `<option value="${index}">Câmera ${index}</option>`
                ).join('');
            } else {
                mostrarAlerta('Erro ao carregar câmeras: ' + data.error, 'danger');
            }
        })
        .catch(error => {
            mostrarAlerta('Erro ao carregar câmeras: ' + error, 'danger');
        });
}

function atualizarListaAlunos() {
    fetch('/api/alunos')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const tbody = document.querySelector('#tabelaAlunos tbody');
                if (data.alunos.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="3" class="text-center">Nenhum aluno cadastrado</td></tr>';
                } else {
                    tbody.innerHTML = data.alunos.map(aluno => `
                        <tr>
                            <td>${aluno._id}</td>
                            <td>${aluno.nome}</td>
                            <td>
                                <button class="btn btn-sm btn-primary" onclick="editarAluno('${aluno._id}', '${aluno.nome}')">
                                    <i class="fas fa-edit"></i> Editar
                                </button>
                                <button class="btn btn-sm btn-danger" onclick="excluirAluno('${aluno._id}')">
                                    <i class="fas fa-trash"></i> Excluir
                                </button>
                            </td>
                        </tr>
                    `).join('');
                }
            } else {
                mostrarAlerta('Erro ao carregar alunos: ' + data.error, 'danger');
            }
        })
        .catch(error => {
            mostrarAlerta('Erro ao carregar alunos: ' + error, 'danger');
        });
}

// Monitoramento
document.getElementById('iniciarMonitoramento').addEventListener('click', async () => {
    const cameraId = document.getElementById('cameraSelect').value;
    if (!cameraId) {
        mostrarAlerta('Selecione uma câmera', 'warning');
        return;
    }

    try {
        const response = await fetch('/api/monitoramento/start', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ camera_id: parseInt(cameraId) })
        });
        
        const data = await response.json();
        if (data.success) {
            mostrarAlerta('Monitoramento iniciado com sucesso!');
            document.getElementById('iniciarMonitoramento').disabled = true;
            document.getElementById('pararMonitoramento').disabled = false;
        } else {
            mostrarAlerta('Erro ao iniciar monitoramento: ' + data.error, 'danger');
        }
    } catch (error) {
        mostrarAlerta('Erro ao iniciar monitoramento: ' + error, 'danger');
    }
});

document.getElementById('pararMonitoramento').addEventListener('click', async () => {
    try {
        const response = await fetch('/api/monitoramento/stop', {
            method: 'POST'
        });
        
        const data = await response.json();
        if (data.success) {
            mostrarAlerta('Monitoramento parado com sucesso!');
            document.getElementById('iniciarMonitoramento').disabled = false;
            document.getElementById('pararMonitoramento').disabled = true;
            cameraFeed.src = '';
            cameraFeed.alt = 'Inicie o monitoramento para ver o feed da câmera';
        } else {
            mostrarAlerta('Erro ao parar monitoramento: ' + data.error, 'danger');
        }
    } catch (error) {
        mostrarAlerta('Erro ao parar monitoramento: ' + error, 'danger');
    }
});

// Cadastro
document.getElementById('capturarFoto').addEventListener('click', async () => {
    const cameraId = document.getElementById('cameraSelectCadastro').value;
    if (!cameraId) {
        mostrarAlerta('Selecione uma câmera', 'warning');
        return;
    }

    try {
        const response = await fetch('/api/camera/capture', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ camera_id: parseInt(cameraId) })
        });
        
        const data = await response.json();
        if (data.success) {
            fotoPreview = data.frame;
            fotoPreviewImg.src = data.frame;
            document.getElementById('btnRegistrar').disabled = false;
            document.getElementById('btnCancelarFoto').disabled = false;
        } else {
            mostrarAlerta('Erro ao capturar foto: ' + data.error, 'danger');
        }
    } catch (error) {
        mostrarAlerta('Erro ao capturar foto: ' + error, 'danger');
    }
});

document.getElementById('formCadastro').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    if (!fotoPreview) {
        mostrarAlerta('Capture uma foto antes de registrar!', 'warning');
        return;
    }
    
    const id = document.getElementById('idAluno').value;
    const nome = document.getElementById('nomeAluno').value;
    
    try {
        const response = await fetch('/api/alunos', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                id: id,
                nome: nome,
                frame: fotoPreview
            })
        });
        
        const data = await response.json();
        if (data.success) {
            mostrarAlerta('Aluno cadastrado com sucesso!');
            document.getElementById('formCadastro').reset();
            fotoPreview = null;
            fotoPreviewImg.src = '';
            document.getElementById('btnRegistrar').disabled = true;
            document.getElementById('btnCancelarFoto').disabled = true;
            atualizarListaAlunos();
        } else {
            mostrarAlerta('Erro ao cadastrar aluno: ' + data.error, 'danger');
        }
    } catch (error) {
        mostrarAlerta('Erro ao cadastrar aluno: ' + error, 'danger');
    }
});

// Edição
function editarAluno(id, nome) {
    alunoEditando = id;
    document.getElementById('editNome').value = nome;
    document.getElementById('editCameraSelect').value = '0';
    fotoPreviewEdit.src = '';
    new bootstrap.Modal(document.getElementById('modalEditar')).show();
}

document.getElementById('capturarFotoEdit').addEventListener('click', async () => {
    const cameraId = document.getElementById('editCameraSelect').value;
    if (!cameraId) {
        mostrarAlerta('Selecione uma câmera', 'warning');
        return;
    }

    try {
        const response = await fetch('/api/camera/capture', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ camera_id: parseInt(cameraId) })
        });
        
        const data = await response.json();
        if (data.success) {
            fotoPreview = data.frame;
            fotoPreviewEdit.src = data.frame;
            document.getElementById('btnSalvarEdit').disabled = false;
        } else {
            mostrarAlerta('Erro ao capturar foto: ' + data.error, 'danger');
        }
    } catch (error) {
        mostrarAlerta('Erro ao capturar foto: ' + error, 'danger');
    }
});

document.getElementById('formEditar').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const nome = document.getElementById('editNome').value;
    
    try {
        const response = await fetch(`/api/alunos/${alunoEditando}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                nome: nome,
                frame: fotoPreview
            })
        });
        
        const data = await response.json();
        if (data.success) {
            mostrarAlerta('Aluno atualizado com sucesso!');
            bootstrap.Modal.getInstance(document.getElementById('modalEditar')).hide();
            atualizarListaAlunos();
        } else {
            mostrarAlerta('Erro ao atualizar aluno: ' + data.error, 'danger');
        }
    } catch (error) {
        mostrarAlerta('Erro ao atualizar aluno: ' + error, 'danger');
    }
});

// Exclusão
async function excluirAluno(id) {
    if (!confirm('Tem certeza que deseja excluir este aluno?')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/alunos/${id}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        if (data.success) {
            mostrarAlerta('Aluno excluído com sucesso!');
            atualizarListaAlunos();
        } else {
            mostrarAlerta('Erro ao excluir aluno: ' + data.error, 'danger');
        }
    } catch (error) {
        mostrarAlerta('Erro ao excluir aluno: ' + error, 'danger');
    }
}

// Socket.IO events
socket.on('frame', (data) => {
    cameraFeed.src = data.frame;
});

socket.on('log', (data) => {
    const log = document.createElement('div');
    log.className = 'log-item';
    log.textContent = data.mensagem;
    
    logsContainer.insertBefore(log, logsContainer.firstChild);
    
    // Manter apenas os últimos 20 logs
    while (logsContainer.children.length > 20) {
        logsContainer.removeChild(logsContainer.lastChild);
    }
});

// Inicialização
document.addEventListener('DOMContentLoaded', () => {
    atualizarListaCameras();
    atualizarListaAlunos();
});

// Atualizar lista de alunos ao trocar para a aba de listagem
const listaTab = document.getElementById('lista-tab');
if (listaTab) {
    listaTab.addEventListener('shown.bs.tab', () => {
        atualizarListaAlunos();
    });
}

// Atualizar estado dos botões ao trocar para a aba de monitoramento
const monitoramentoTab = document.getElementById('monitoramento-tab');
if (monitoramentoTab) {
    monitoramentoTab.addEventListener('shown.bs.tab', () => {
        document.getElementById('iniciarMonitoramento').disabled = false;
        document.getElementById('pararMonitoramento').disabled = true;
    });
} 