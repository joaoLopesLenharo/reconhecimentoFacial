// static/js/app.js

// --- INICIALIZAÇÃO E VARIÁVEIS GLOBAIS ---
const socket = io();
let fotoCapturada = null;
let streamAtivo = null;

// --- ELEMENTOS DA UI ---
const cameraFeed = document.getElementById('cameraFeed');
const logsContainer = document.getElementById('logs');
const iniciarMonitoramentoBtn = document.getElementById('iniciarMonitoramento');
const pararMonitoramentoBtn = document.getElementById('pararMonitoramento');

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

async function popularSeletoresDeCameraCliente() {
    console.log("JS: Iniciando busca por câmeras no navegador...");
    if (!navigator.mediaDevices?.enumerateDevices) {
        console.error("JS: enumerateDevices() não é suportado por este navegador.");
        mostrarAlerta("Seu navegador não suporta a seleção de câmeras.", "warning");
        return;
    }

    try {
        console.log("JS: Solicitando permissão de câmera para listar dispositivos...");
        const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
        pararStreamDeVideo(stream);

        const devices = await navigator.mediaDevices.enumerateDevices();
        console.log("JS: Dispositivos encontrados:", devices);

        const videoDevices = devices.filter(device => device.kind === 'videoinput');
        console.log("JS: Dispositivos de vídeo filtrados:", videoDevices);

        const selectors = document.querySelectorAll('#cameraSelectCadastro, #cameraSelectEdit');

        if (videoDevices.length === 0) {
            console.warn("JS: Nenhuma câmera (videoinput) foi encontrada.");
            mostrarAlerta("Nenhuma câmera foi encontrada pelo navegador.", "warning");
            selectors.forEach(selector => selector.innerHTML = '<option value="">Nenhuma câmera encontrada</option>');
            return;
        }

        selectors.forEach(selector => {
            selector.innerHTML = '';
            videoDevices.forEach((device, index) => {
                const option = document.createElement('option');
                option.value = device.deviceId;
                option.text = device.label || `Câmera ${index + 1}`;
                selector.appendChild(option);
            });
        });
        console.log("JS: Seletores de câmera para cadastro/edição populados com sucesso.");

    } catch (err) {
        console.error("JS: Erro ao enumerar ou obter permissão para dispositivos:", err);
        if (err.name === "NotAllowedError" || err.name === "PermissionDeniedError") {
            mostrarAlerta("Permissão de câmera negada. Habilite nas configurações do seu navegador.", "danger");
        } else {
            mostrarAlerta("Erro ao listar as câmeras. Veja o console (F12) para detalhes.", "danger");
        }
    }
}

// --- LÓGICA DE CAPTURA DE FOTO (CLIENT-SIDE) ---
function configurarControlesDeCamera(tipo) {
    const btnAbrir = document.getElementById(`btnAbrirCamera${tipo}`);
    const btnTirar = document.getElementById(`btnTirarFoto${tipo}`);
    const videoPreview = document.getElementById(`videoPreview${tipo}`);
    const fotoPreview = document.getElementById(tipo === 'Cadastro' ? 'fotoPreview' : 'fotoPreviewEdit');
    const cameraSelector = document.getElementById(`cameraSelect${tipo}`);
    const btnRegistrar = document.getElementById('btnRegistrar');
    const btnCancelar = document.getElementById('btnCancelarCadastro');

    btnAbrir.addEventListener('click', async () => {
        pararStreamDeVideo();
        if (!cameraSelector || !cameraSelector.value) {
            mostrarAlerta("Nenhuma câmera selecionada ou encontrada.", "warning");
            return;
        }
        
        const constraints = { video: { deviceId: { exact: cameraSelector.value } } };

        try {
            streamAtivo = await navigator.mediaDevices.getUserMedia(constraints);
            videoPreview.srcObject = streamAtivo;
            videoPreview.style.display = 'block';
            fotoPreview.style.display = 'none';
            videoPreview.play();
            btnAbrir.style.display = 'none';
            btnTirar.style.display = 'inline-block';
            if(btnCancelar) btnCancelar.style.display = 'inline-block';
        } catch (err) {
            mostrarAlerta(`Não foi possível acessar a câmera: ${err.name}`, "danger");
        }
    });

    btnTirar.addEventListener('click', () => {
        const canvas = document.createElement('canvas');
        canvas.width = videoPreview.videoWidth;
        canvas.height = videoPreview.videoHeight;
        canvas.getContext('2d').drawImage(videoPreview, 0, 0);
        fotoCapturada = canvas.toDataURL('image/jpeg');
        fotoPreview.src = fotoCapturada;
        fotoPreview.style.display = 'block';
        pararStreamDeVideo();
        videoPreview.style.display = 'none';
        btnTirar.style.display = 'none';
        btnAbrir.style.display = 'inline-block';
        if(btnRegistrar) btnRegistrar.disabled = false;
    });
}

configurarControlesDeCamera('Cadastro');
configurarControlesDeCamera('Edit');

document.getElementById('btnCancelarCadastro').addEventListener('click', () => {
    pararStreamDeVideo();
    document.getElementById('videoPreviewCadastro').style.display = 'none';
    const fotoImg = document.getElementById('fotoPreview');
    fotoImg.src = '';
    fotoImg.alt = 'Abra a câmera para iniciar';
    fotoImg.style.display = 'block';
    document.getElementById('btnAbrirCameraCadastro').style.display = 'inline-block';
    document.getElementById('btnTirarFotoCadastro').style.display = 'none';
    document.getElementById('btnCancelarCadastro').style.display = 'none';
    document.getElementById('btnRegistrar').disabled = true;
    fotoCapturada = null;
});

// --- LÓGICA DE MONITORAMENTO ---
iniciarMonitoramentoBtn.addEventListener('click', async () => {
    try {
        const cameraId = document.getElementById('cameraSelect').value;
        if (cameraId === "") {
            mostrarAlerta("Nenhuma câmera disponível para monitoramento.", "warning");
            return;
        }
        const response = await fetch('/api/monitoramento/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ camera_id: parseInt(cameraId) })
        });
        const data = await response.json();
        if (data.success) {
            mostrarAlerta('Monitoramento iniciado.');
            iniciarMonitoramentoBtn.disabled = true;
            pararMonitoramentoBtn.disabled = false;
        } else {
            mostrarAlerta('Erro ao iniciar monitoramento: ' + data.error, 'danger');
        }
    } catch (e) {
        mostrarAlerta('Erro de conexão ao iniciar monitoramento.', 'danger');
    }
});

pararMonitoramentoBtn.addEventListener('click', async () => {
    try {
        const response = await fetch('/api/monitoramento/stop', { method: 'POST' });
        const data = await response.json();
        if (data.success) {
            mostrarAlerta('Monitoramento parado.');
            iniciarMonitoramentoBtn.disabled = false;
            pararMonitoramentoBtn.disabled = true;
            cameraFeed.src = '';
            cameraFeed.alt = 'Inicie o monitoramento para ver o feed da câmera';
        }
    } catch (e) {
        mostrarAlerta('Erro de conexão ao parar monitoramento.', 'danger');
    }
});

// --- LÓGICA DE ALUNOS (CRUD) ---
function atualizarListaAlunos() {
    fetch('/api/alunos')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const tbody = document.querySelector('#tabelaAlunos tbody');
                tbody.innerHTML = data.alunos.length > 0 ? data.alunos.map(aluno => `
                    <tr>
                        <td>${aluno._id}</td>
                        <td>${aluno.nome}</td>
                        <td>
                            <button class="btn btn-sm btn-primary" onclick="abrirModalEditar('${aluno._id}', '${aluno.nome}')"><i class="fas fa-edit"></i> Editar</button>
                            <button class="btn btn-sm btn-danger" onclick="excluirAluno('${aluno._id}')"><i class="fas fa-trash"></i> Excluir</button>
                        </td>
                    </tr>
                `).join('') : '<tr><td colspan="3" class="text-center">Nenhum aluno cadastrado</td></tr>';
            }
        });
}

document.getElementById('formCadastro').addEventListener('submit', async (e) => {
    e.preventDefault();
    if (!fotoCapturada) {
        mostrarAlerta('Tire uma foto antes de registrar!', 'warning');
        return;
    }
    const id = document.getElementById('idAluno').value;
    const nome = document.getElementById('nomeAluno').value;
    const response = await fetch('/api/alunos', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id, nome, frame: fotoCapturada })
    });
    const data = await response.json();
    if (data.success) {
        mostrarAlerta('Aluno cadastrado com sucesso!');
        document.getElementById('formCadastro').reset();
        document.getElementById('btnCancelarCadastro').click();
        atualizarListaAlunos();
    } else {
        mostrarAlerta('Erro ao cadastrar aluno: ' + data.error, 'danger');
    }
});

let alunoEditando = null;
const modalEditar = new bootstrap.Modal(document.getElementById('modalEditar'));

function abrirModalEditar(id, nome) {
    alunoEditando = id;
    document.getElementById('editNome').value = nome;
    document.getElementById('fotoPreviewEdit').src = '';
    document.getElementById('fotoPreviewEdit').alt = 'Abra a câmera se desejar uma nova foto';
    document.getElementById('videoPreviewEdit').style.display = 'none';
    document.getElementById('btnAbrirCameraEdit').style.display = 'inline-block';
    document.getElementById('btnTirarFotoEdit').style.display = 'none';
    fotoCapturada = null;
    modalEditar.show();
}

document.getElementById('btnSalvarEdit').addEventListener('click', async () => {
    const nome = document.getElementById('editNome').value;
    const response = await fetch(`/api/alunos/${alunoEditando}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ nome, frame: fotoCapturada })
    });
    const data = await response.json();
    if (data.success) {
        mostrarAlerta('Aluno atualizado com sucesso!');
        modalEditar.hide();
        atualizarListaAlunos();
    } else {
        mostrarAlerta('Erro ao atualizar aluno: ' + data.error, 'danger');
    }
});

document.getElementById('modalEditar').addEventListener('hidden.bs.modal', pararStreamDeVideo);

async function excluirAluno(id) {
    if (!confirm('Tem certeza que deseja excluir este aluno?')) return;
    const response = await fetch(`/api/alunos/${id}`, { method: 'DELETE' });
    const data = await response.json();
    if (data.success) {
        mostrarAlerta('Aluno excluído com sucesso!');
        atualizarListaAlunos();
    } else {
        mostrarAlerta('Erro ao excluir aluno: ' + data.error, 'danger');
    }
}

// --- SOCKET.IO E EVENTOS GERAIS ---
socket.on('frame', (data) => {
    cameraFeed.src = data.frame;
});
socket.on('log', (data) => {
    const log = document.createElement('div');
    log.className = 'log-item';
    log.textContent = data.mensagem;
    logsContainer.insertBefore(log, logsContainer.firstChild);
    if (logsContainer.children.length > 50) {
        logsContainer.removeChild(logsContainer.lastChild);
    }
});

document.addEventListener('DOMContentLoaded', () => {
    fetch('/api/cameras')
      .then(res => res.json())
      .then(data => {
        const select = document.getElementById('cameraSelect');
        if(data.success && data.cameras.length > 0){
            select.innerHTML = data.cameras.map(cam => `<option value="${cam}">Câmera ${cam}</option>`).join('');
        } else {
            select.innerHTML = '<option value="">Nenhuma câmera encontrada</option>';
        }
      });
    
    popularSeletoresDeCameraCliente();
    
    atualizarListaAlunos();
    document.getElementById('lista-tab').addEventListener('shown.bs.tab', atualizarListaAlunos);
});