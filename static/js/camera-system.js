// Camera System Module - Complete camera functionality
const CameraSystem = (() => {
    
    // State management
    let availableCameras = [];
    let currentStream = null;
    let isMonitoring = false;
    let selectedCameraId = null;
    
    // DOM elements
    let cameraSelect, cameraContainer, iniciarBtn, pararBtn;
    let testModeToggle, multiCameraView;
    
    // Initialize the camera system
    function init() {
        initializeElements();
        setupEventListeners();
        loadAvailableCameras();
    }
    
    // Initialize DOM elements
    function initializeElements() {
        cameraSelect = document.getElementById('cameraSelect');
        cameraContainer = document.getElementById('cameraContainer');
        iniciarBtn = document.getElementById('iniciarMonitoramento');
        pararBtn = document.getElementById('pararMonitoramento');
        testModeToggle = document.getElementById('testModeToggle');
        multiCameraView = document.getElementById('multiCameraView');
    }
    
    // Setup event listeners
    function setupEventListeners() {
        if (iniciarBtn) {
            iniciarBtn.addEventListener('click', startMonitoring);
        }
        
        if (pararBtn) {
            pararBtn.addEventListener('click', stopMonitoring);
        }
        
        if (cameraSelect) {
            cameraSelect.addEventListener('change', onCameraSelectionChange);
        }
        
        if (testModeToggle) {
            testModeToggle.addEventListener('change', onTestModeToggle);
        }
        
        if (multiCameraView) {
            multiCameraView.addEventListener('change', onMultiCameraToggle);
        }
    }
    
    // Load available cameras from backend and browser
    async function loadAvailableCameras() {
        try {
            showCameraStatus('Carregando câmeras disponíveis...', 'loading');
            
            // First try to get browser cameras
            let browserCameras = [];
            try {
                // Request permission first
                const tempStream = await navigator.mediaDevices.getUserMedia({ video: true });
                tempStream.getTracks().forEach(track => track.stop());
                
                // Now enumerate devices
                const devices = await navigator.mediaDevices.enumerateDevices();
                browserCameras = devices
                    .filter(device => device.kind === 'videoinput')
                    .map((device, index) => ({
                        id: device.deviceId || index.toString(),
                        name: device.label || `Câmera ${index + 1}`,
                        deviceId: device.deviceId
                    }));
                
                console.log('Câmeras do navegador:', browserCameras);
            } catch (permissionError) {
                console.warn('Não foi possível obter permissão para câmeras:', permissionError);
                // Fallback to backend cameras
            }
            
            // Load cameras from backend API
            let backendCameras = [];
            try {
                const response = await fetch('/api/cameras');
                if (!response.ok) {
                    if (response.status === 404) {
                        throw new Error('Endpoint /api/cameras não encontrado');
                    }
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                
                const data = await response.json();
                if (data.cameras && data.cameras.length > 0) {
                    backendCameras = data.cameras.map(cam => ({
                        id: cam.id || cam.toString(),
                        name: cam.name || `Câmera ${cam.id || cam}`
                    }));
                }
            } catch (backendError) {
                console.warn('Erro ao carregar câmeras do backend:', backendError);
            }
            
            // Combine both sources, prioritizing browser cameras
            availableCameras = browserCameras.length > 0 ? browserCameras : backendCameras;
            
            populateCameraSelect(availableCameras);
            
            if (availableCameras.length === 0) {
                showCameraStatus('Nenhuma câmera encontrada. Verifique se uma câmera está conectada e permita o acesso quando solicitado.', 'warning');
            } else {
                showCameraStatus(`${availableCameras.length} câmera(s) encontrada(s)`, 'success');
            }
            
        } catch (error) {
            console.error('Erro ao carregar câmeras:', error);
            showCameraStatus('Erro ao carregar câmeras: ' + error.message, 'error');
            availableCameras = [];
        }
    }
    
    // Populate camera selection dropdown
    function populateCameraSelect(cameras) {
        if (!cameraSelect) return;
        
        // Clear existing options
        cameraSelect.innerHTML = '';
        
        // Add default option
        const defaultOption = document.createElement('option');
        defaultOption.value = '';
        defaultOption.textContent = 'Selecione uma câmera';
        defaultOption.disabled = true;
        defaultOption.selected = true;
        cameraSelect.appendChild(defaultOption);
        
        // Add camera options
        cameras.forEach(camera => {
            const option = document.createElement('option');
            option.value = camera.id;
            option.textContent = camera.name;
            cameraSelect.appendChild(option);
        });
        
        // Enable/disable based on availability
        cameraSelect.disabled = cameras.length === 0;
    }
    
    // Handle camera selection change
    function onCameraSelectionChange(event) {
        selectedCameraId = event.target.value;
        
        if (selectedCameraId && iniciarBtn) {
            iniciarBtn.disabled = false;
        } else if (iniciarBtn) {
            iniciarBtn.disabled = true;
        }
    }
    
    // Start camera monitoring (backend-driven, no getUserMedia required)
    async function startMonitoring() {
        if (!selectedCameraId) {
            showAlert('Por favor, selecione uma câmera primeiro', 'warning');
            return;
        }
        
        try {
            // Update UI state
            setMonitoringState(true);
            showCameraStatus('Iniciando monitoramento...', 'loading');

            // Always render display IMG and connect to backend (OpenCV will read camera)
            createCameraDisplay();
            await connectToBackendMonitoring();

            isMonitoring = true;
            showCameraStatus('Monitoramento ativo', 'success');
        } catch (error) {
            console.error('Erro ao iniciar monitoramento:', error);
            showCameraStatus('Erro ao iniciar monitoramento: ' + error.message, 'error');
            setMonitoringState(false);
        }
    }
    
    // Start real camera monitoring
    async function startRealCameraMonitoring() {
        try {
            // First, enumerate available devices
            const devices = await navigator.mediaDevices.enumerateDevices();
            const videoDevices = devices.filter(device => device.kind === 'videoinput');
            
            console.log('Dispositivos de vídeo encontrados:', videoDevices);
            
            if (videoDevices.length === 0) {
                throw new Error('Nenhuma câmera encontrada no sistema');
            }
            
            // Find the selected device or use default
            let deviceId = undefined;
            if (selectedCameraId && selectedCameraId !== '') {
                // First try to find by deviceId
                let selectedDevice = videoDevices.find(device => device.deviceId === selectedCameraId);
                
                // If not found, try to find by index
                if (!selectedDevice) {
                    const index = parseInt(selectedCameraId);
                    if (!isNaN(index) && index < videoDevices.length) {
                        selectedDevice = videoDevices[index];
                    }
                }
                
                // If still not found, try to find by our stored deviceId
                if (!selectedDevice) {
                    const storedCamera = availableCameras.find(cam => cam.id === selectedCameraId);
                    if (storedCamera && storedCamera.deviceId) {
                        selectedDevice = videoDevices.find(device => device.deviceId === storedCamera.deviceId);
                    }
                }
                
                if (selectedDevice) {
                    deviceId = selectedDevice.deviceId;
                    console.log('Usando câmera:', selectedDevice.label || selectedDevice.deviceId);
                } else {
                    console.warn('Câmera selecionada não encontrada, usando primeira disponível');
                    if (videoDevices.length > 0) {
                        deviceId = videoDevices[0].deviceId;
                    }
                }
            } else {
                // Use first available camera
                if (videoDevices.length > 0) {
                    deviceId = videoDevices[0].deviceId;
                    console.log('Usando primeira câmera disponível:', videoDevices[0].label || videoDevices[0].deviceId);
                }
            }
            
            // Request camera access with fallback constraints
            let constraints = {
                video: {
                    deviceId: deviceId ? { exact: deviceId } : undefined,
                    width: { ideal: 1280, min: 640 },
                    height: { ideal: 720, min: 480 }
                },
                audio: false
            };
            
            try {
                currentStream = await navigator.mediaDevices.getUserMedia(constraints);
            } catch (exactError) {
                console.warn('Falha com deviceId específico, tentando sem restrições:', exactError);
                // Fallback: try without specific device ID
                constraints = {
                    video: {
                        width: { ideal: 1280, min: 640 },
                        height: { ideal: 720, min: 480 }
                    },
                    audio: false
                };
                currentStream = await navigator.mediaDevices.getUserMedia(constraints);
            }
            
            // Create video element for display
            createCameraDisplay();
            
            // Connect to backend monitoring
            await connectToBackendMonitoring();
            
            isMonitoring = true;
            showCameraStatus('Monitoramento ativo', 'success');
            
        } catch (error) {
            console.error('Erro detalhado na câmera:', error);
            
            if (error.name === 'NotAllowedError') {
                throw new Error('Permissão de câmera negada. Clique no ícone da câmera na barra de endereços e permita o acesso.');
            } else if (error.name === 'NotFoundError') {
                throw new Error('Nenhuma câmera encontrada. Verifique se uma câmera está conectada ao computador.');
            } else if (error.name === 'NotReadableError') {
                throw new Error('Câmera está sendo usada por outro aplicativo. Feche outros programas que possam estar usando a câmera.');
            } else if (error.name === 'OverconstrainedError') {
                throw new Error('Configurações de câmera não suportadas. Tentando com configurações básicas...');
            } else {
                throw new Error('Erro ao acessar câmera: ' + (error.message || 'Erro desconhecido'));
            }
        }
    }
    
    // Start test mode with simulated camera
    function startTestMode() {
        createTestCameraDisplay();
        isMonitoring = true;
        showCameraStatus('Modo de teste ativo', 'info');
    }
    
    // Create camera display element (single IMG fed by backend frames)
    function createCameraDisplay() {
        if (!cameraContainer) return;
        cameraContainer.innerHTML = '';
        const img = document.createElement('img');
        img.id = 'cameraFeed';
        img.className = 'w-100 h-auto';
        img.alt = 'Feed da câmera (frames processados)';
        img.style.maxHeight = '400px';
        img.style.objectFit = 'contain';
        img.style.backgroundColor = '#000';

        img.onerror = (error) => {
            console.error('Erro na imagem do feed:', error);
            showCameraStatus('Erro na exibição do frame recebido', 'error');
        };

        img.onload = () => {
            // Frame carregado com sucesso
        };

        cameraContainer.appendChild(img);
    }
    
    // Create test camera display
    function createTestCameraDisplay() {
        if (!cameraContainer) return;
        
        cameraContainer.innerHTML = `
            <div class="test-camera-display bg-secondary rounded p-4 text-center">
                <i class="fas fa-video fa-3x text-primary mb-3"></i>
                <h5>Modo de Teste</h5>
                <p class="mb-0">Simulando câmera ${selectedCameraId}</p>
                <div class="mt-3">
                    <div class="spinner-border spinner-border-sm text-primary me-2"></div>
                    <small>Processando frames simulados...</small>
                </div>
            </div>
        `;
    }
    
    // Connect to backend monitoring system
    async function connectToBackendMonitoring() {
        try {
            const response = await fetch('/api/monitoring/start', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    camera_id: selectedCameraId,
                    test_mode: testModeToggle && testModeToggle.checked
                })
            });
            
            const data = await response.json();
            
            if (!data.success) {
                throw new Error(data.error || 'Erro ao conectar com o backend');
            }
            
            // Setup socket listeners for real-time updates
            setupSocketListeners();
            
        } catch (error) {
            console.error('Erro ao conectar com backend:', error);
            throw error;
        }
    }
    
    // Setup Socket.IO listeners with robust initialization
    function setupSocketListeners() {
        let s = window.socket;
        if (!s && typeof window.io === 'function') {
            try {
                window.socket = window.io();
                s = window.socket;
                console.log('[CameraSystem] Socket.IO inicializado pelo camera-system.js');
            } catch (e) {
                console.warn('Falha ao inicializar Socket.IO:', e);
            }
        }
        if (!s) {
            console.warn('Socket.IO não disponível, tentando novamente em 500ms');
            setTimeout(setupSocketListeners, 500);
            return;
        }
        const socket = s;
        
        // Listen for camera frames
        socket.on('camera_frame', (data) => {
            updateCameraFrame(data);
        });
        
        // Listen for recognition events
        socket.on('student_detected', (data) => {
            handleStudentDetection(data);
        });
        
        // Listen for unknown face detection
        socket.on('unknown_face_detected', (data) => {
            handleUnknownFaceDetection(data);
        });
        
        // Listen for student absence notifications
        socket.on('student_absent', (data) => {
            handleStudentAbsence(data);
        });
        
        // Listen for email notifications
        socket.on('email_sent', (data) => {
            handleEmailNotification(data);
        });
        
        // Listen for monitoring status
        socket.on('monitoring_status', (data) => {
            handleMonitoringStatus(data);
        });
    }
    
    // Update camera frame display
    let lastFrameAt = 0;
    let previousObjectUrl = null;
    let firstFrameLogged = false;
    function updateCameraFrame(data) {
        const imgElement = document.getElementById('cameraFeed');
        if (!imgElement || !data || !data.frame) return;
        
        try {
            // Throttle UI updates to avoid flicker and decode pressure (max ~15 FPS)
            const now = Date.now();
            if (now - lastFrameAt < 66) return;
            lastFrameAt = now;

            let frameData = data.frame;
            // Strip any data URL prefix if present
            if (frameData.startsWith('data:image/')) {
                const idx = frameData.indexOf(',');
                frameData = frameData.slice(idx + 1);
            }
            // Remove whitespace/newlines
            frameData = frameData.replace(/\s/g, '');
            // Normalize Base64 padding to multiple of 4
            const pad = frameData.length % 4;
            if (pad === 2) frameData += '==';
            else if (pad === 3) frameData += '=';
            else if (pad === 1) {
                // Invalid base64 length, skip this frame
                console.warn('Frame base64 inválido (padding incorreto)');
                return;
            }
            if (!frameData) return;

            // Convert base64 to Blob and use ObjectURL (more robust than data URLs for rapid updates)
            const byteChars = atob(frameData);
            const byteNumbers = new Uint8Array(byteChars.length);
            for (let i = 0; i < byteChars.length; i++) byteNumbers[i] = byteChars.charCodeAt(i);
            const blob = new Blob([byteNumbers], { type: 'image/jpeg' });
            const objectUrl = URL.createObjectURL(blob);

            // Revoke previous URL only after new image has loaded to avoid flicker/black frames
            const oldUrl = previousObjectUrl;
            previousObjectUrl = objectUrl;
            imgElement.onload = () => {
                if (!firstFrameLogged) {
                    console.log('[CameraSystem] Primeiro frame recebido e exibido');
                    firstFrameLogged = true;
                }
                if (oldUrl) URL.revokeObjectURL(oldUrl);
            };
            imgElement.onerror = (e) => {
                console.error('Falha ao carregar frame', e);
            };
            imgElement.src = objectUrl;
        } catch (error) {
            console.error('Error updating camera frame:', error);
        }
    }
    
    // Handle unknown face detection
    function handleUnknownFaceDetection(data) {
        console.log('Rosto desconhecido detectado:', data);
        
        // Show notification
        if (typeof mostrarAlerta === 'function') {
            mostrarAlerta('Rosto não reconhecido detectado', 'warning');
        }
        
        // Update logs
        addToLogs(
            'Rosto não reconhecido detectado',
            'face_unknown',
            `Câmera: ${data.camera_id || 'N/A'} | Confiança: ${data.confidence ? Math.round(data.confidence * 100) + '%' : 'N/A'}`
        );
    }
    
    // Handle student absence
    function handleStudentAbsence(data) {
        console.log('Aluno ausente:', data);
        
        const studentName = data.student_name || `ID: ${data.student_id}`;
        
        // Show notification
        if (typeof mostrarAlerta === 'function') {
            mostrarAlerta(`Aluno ausente detectado: ${studentName}`, 'warning');
        }
        
        // Update logs
        addToLogs(
            `Ausência detectada: ${studentName}`,
            'warning',
            `Ausente por ${data.absence_count || 'N/A'} verificações consecutivas`
        );
    }
    
    // Handle email notifications
    function handleEmailNotification(data) {
        console.log('Notificação de email:', data);
        
        const status = data.success ? 'enviado' : 'falhou';
        const type = data.success ? 'email_sent' : 'email_failed';
        const alertType = data.success ? 'success' : 'danger';
        
        // Show notification
        if (typeof mostrarAlerta === 'function') {
            mostrarAlerta(`Email ${status} para ${data.recipient || 'destinatário'}`, alertType);
        }
        
        // Update logs
        addToLogs(
            `Email ${status}: ${data.subject || 'Notificação de ausência'}`,
            type,
            `Para: ${data.recipient || 'N/A'} | ${data.success ? 'Enviado com sucesso' : 'Erro: ' + (data.error || 'Erro desconhecido')}`
        );
    }
    
    // Handle student detection
    function handleStudentDetection(data) {
        console.log('Aluno detectado:', data);
        
        const studentName = data.student_name || `ID: ${data.student_id}`;
        const confidence = data.confidence ? ` (${Math.round(data.confidence * 100)}%)` : '';
        
        // Show notification
        if (typeof mostrarAlerta === 'function') {
            mostrarAlerta(`Rosto reconhecido: ${studentName}`, 'success');
        }
        
        // Update logs with detailed information
        addToLogs(
            `Rosto reconhecido: ${studentName}${confidence}`,
            'face_recognized',
            `Câmera: ${data.camera_id || 'N/A'} | Horário: ${new Date().toLocaleString()}`
        );
    }
    
    // Handle monitoring status updates
    function handleMonitoringStatus(data) {
        console.log('Status do monitoramento:', data);
        
        if (data.status === 'error') {
            showCameraStatus('Erro no monitoramento: ' + data.message, 'error');
        } else if (data.status === 'active') {
            showCameraStatus('Monitoramento ativo', 'success');
        }
    }
    
    // Stop monitoring
    async function stopMonitoring() {
        try {
            setMonitoringState(false);
            showCameraStatus('Parando monitoramento...', 'loading');
            
            // Stop camera stream
            if (currentStream) {
                currentStream.getTracks().forEach(track => track.stop());
                currentStream = null;
            }
            
            // Stop backend monitoring
            await fetch('/api/monitoring/stop', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            // Clear display
            if (cameraContainer) {
                cameraContainer.innerHTML = `
                    <div class="text-center py-5 text-muted">
                        <i class="fas fa-video-slash fa-3x mb-3"></i>
                        <p>Monitoramento parado</p>
                    </div>
                `;
            }
            
            isMonitoring = false;
            showCameraStatus('Monitoramento parado', 'info');
            
        } catch (error) {
            console.error('Erro ao parar monitoramento:', error);
            showCameraStatus('Erro ao parar monitoramento', 'error');
        }
    }
    
    // Set monitoring UI state
    function setMonitoringState(monitoring) {
        if (iniciarBtn) {
            iniciarBtn.disabled = monitoring;
            iniciarBtn.innerHTML = monitoring ? 
                '<span class="spinner-border spinner-border-sm me-2"></span>Iniciando...' :
                '<i class="fas fa-play"></i> Iniciar Monitoramento';
        }
        
        if (pararBtn) {
            pararBtn.disabled = !monitoring;
        }
        
        if (cameraSelect) {
            cameraSelect.disabled = monitoring;
        }
    }
    
    // Show camera status message
    function showCameraStatus(message, type = 'info') {
        const statusClass = {
            'loading': 'text-primary',
            'success': 'text-success',
            'warning': 'text-warning',
            'error': 'text-danger',
            'info': 'text-info'
        }[type] || 'text-info';
        
        const icon = {
            'loading': 'fas fa-spinner fa-spin',
            'success': 'fas fa-check-circle',
            'warning': 'fas fa-exclamation-triangle',
            'error': 'fas fa-times-circle',
            'info': 'fas fa-info-circle'
        }[type] || 'fas fa-info-circle';
        
        console.log(`[Camera System] ${message}`);
        
        // Update status in logs
        addToLogs(message, type);
    }
    
    // Add message to logs with enhanced formatting
    function addToLogs(message, type = 'info', details = null) {
        const logsContainer = document.getElementById('logs');
        if (!logsContainer) return;
        
        const logEntry = document.createElement('div');
        logEntry.className = `log-entry ${type}`;
        
        const timestamp = new Date().toLocaleTimeString();
        const icon = getLogIcon(type);
        
        let logContent = `
            <div class="d-flex align-items-start">
                <span class="timestamp me-2">${timestamp}</span>
                <i class="${icon} me-2 mt-1"></i>
                <div class="flex-grow-1">
                    <span class="message">${message}</span>
                    ${details ? `<div class="details mt-1"><small>${details}</small></div>` : ''}
                </div>
            </div>
        `;
        
        logEntry.innerHTML = logContent;
        logsContainer.appendChild(logEntry);
        logsContainer.scrollTop = logsContainer.scrollHeight;
        
        // Keep only last 100 entries
        while (logsContainer.children.length > 100) {
            logsContainer.removeChild(logsContainer.firstChild);
        }
    }
    
    // Get icon for log type
    function getLogIcon(type) {
        const icons = {
            'success': 'fas fa-check-circle text-success',
            'error': 'fas fa-times-circle text-danger',
            'warning': 'fas fa-exclamation-triangle text-warning',
            'info': 'fas fa-info-circle text-info',
            'face_recognized': 'fas fa-user-check text-success',
            'face_unknown': 'fas fa-user-question text-warning',
            'email_sent': 'fas fa-envelope text-success',
            'email_failed': 'fas fa-envelope-open-text text-danger',
            'monitoring': 'fas fa-video text-primary'
        };
        return icons[type] || icons['info'];
    }
    
    // Show alert using existing function
    function showAlert(message, type = 'info') {
        if (typeof mostrarAlerta === 'function') {
            mostrarAlerta(message, type);
        } else {
            console.log(`[${type.toUpperCase()}] ${message}`);
        }
    }
    
    // Handle test mode toggle
    function onTestModeToggle(event) {
        const isTestMode = event.target.checked;
        console.log('Modo de teste:', isTestMode ? 'ativado' : 'desativado');
        
        if (isMonitoring) {
            showAlert('Pare o monitoramento antes de alterar o modo', 'warning');
            event.target.checked = !isTestMode; // Revert change
        }
    }
    
    // Handle multi-camera view toggle
    function onMultiCameraToggle(event) {
        const isMultiView = event.target.checked;
        console.log('Visualização múltipla:', isMultiView ? 'ativada' : 'desativada');
        
        if (isMonitoring) {
            showAlert('Pare o monitoramento antes de alterar a visualização', 'warning');
            event.target.checked = !isMultiView; // Revert change
        }
    }
    
    // Get current monitoring status
    function getStatus() {
        return {
            isMonitoring,
            selectedCameraId,
            availableCameras: availableCameras.length,
            hasStream: !!currentStream
        };
    }
    
    // Public API
    return {
        init,
        startMonitoring,
        stopMonitoring,
        loadAvailableCameras,
        getStatus
    };
})();

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    CameraSystem.init();
});

// Make available globally
window.CameraSystem = CameraSystem;
