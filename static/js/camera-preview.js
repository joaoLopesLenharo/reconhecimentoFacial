// Camera Preview Module
const CameraPreview = (() => {
    // Elements - Initialize after DOM is loaded
    let videoElement, canvasElement, photoElement, cameraPlaceholder, cameraLoading;
    let btnAbrirCamera, btnTirarFoto, btnCancelar, btnConfirmar;
    
    // Initialize elements
    function initializeElements() {
        videoElement = document.getElementById('videoPreviewCadastro');
        canvasElement = document.getElementById('canvasPreview');
        photoElement = document.getElementById('fotoPreview');
        cameraPlaceholder = document.getElementById('cameraPlaceholder');
        cameraLoading = document.getElementById('cameraLoading');
        
        // Buttons
        btnAbrirCamera = document.getElementById('btnAbrirCameraPreview');
        btnTirarFoto = document.getElementById('btnTirarFotoPreview');
        btnCancelar = document.getElementById('btnCancelarCamera');
        btnConfirmar = document.getElementById('btnConfirmarFoto');
    }
    
    // State
    let stream = null;
    let isCameraActive = false;
    let photoData = null;
    
    // Initialize the module
    function init() {
        initializeElements();
        if (!videoElement || !btnAbrirCamera) return;
        
        // Event Listeners
        btnAbrirCamera.addEventListener('click', startCamera);
        btnTirarFoto.addEventListener('click', takePhoto);
        if (btnCancelar) btnCancelar.addEventListener('click', stopCamera);
        if (btnConfirmar) btnConfirmar.addEventListener('click', confirmPhoto);
        
        // Clean up on page unload
        window.addEventListener('beforeunload', stopCamera);
    }
    
    // Start the camera
    async function startCamera() {
        try {
            // Show loading state
            showLoading(true);
            if (cameraPlaceholder) cameraPlaceholder.style.display = 'none';
            
            // Get user media
            stream = await navigator.mediaDevices.getUserMedia({
                video: { 
                    width: { ideal: 1280 },
                    height: { ideal: 720 },
                    facingMode: 'user' 
                },
                audio: false
            });
            
            // Set video source
            if (videoElement) {
                videoElement.srcObject = stream;
                videoElement.style.display = 'block';
                videoElement.play();
            }
            
            // Update UI
            isCameraActive = true;
            btnAbrirCamera.style.display = 'none';
            btnTirarFoto.style.display = 'block';
            if (btnCancelar) btnCancelar.style.display = 'block';
            
            // Hide loading
            showLoading(false);
            
        } catch (error) {
            console.error('Error accessing camera:', error);
            showLoading(false);
            if (cameraPlaceholder) {
                cameraPlaceholder.style.display = 'flex';
                cameraPlaceholder.innerHTML = `
                    <div class="text-danger">
                        <i class="fas fa-exclamation-triangle fa-2x mb-2"></i>
                        <p>Não foi possível acessar a câmera.</p>
                        <button class="btn btn-sm btn-outline-light" onclick="location.reload()">
                            <i class="fas fa-sync-alt me-1"></i> Tentar novamente
                        </button>
                    </div>
                `;
            }
        }
    }
    
    // Take a photo
    function takePhoto() {
        if (!isCameraActive) return;
        
        // Create capture effect
        const flash = document.createElement('div');
        flash.className = 'capture-effect';
        document.querySelector('.camera-preview-container').appendChild(flash);
        
        // Remove flash after animation
        setTimeout(() => flash.remove(), 500);
        
        // Set canvas dimensions
        const width = videoElement.videoWidth;
        const height = videoElement.videoHeight;
        canvasElement.width = width;
        canvasElement.height = height;
        
        // Draw video frame to canvas
        const context = canvasElement.getContext('2d');
        context.drawImage(videoElement, 0, 0, width, height);
        
        // Show the captured photo
        photoData = canvasElement.toDataURL('image/jpeg');
        if (photoElement) {
            photoElement.src = photoData;
            photoElement.style.display = 'block';
        }
        if (videoElement) videoElement.style.display = 'none';
        
        // Update UI
        btnTirarFoto.style.display = 'none';
        if (btnConfirmar) btnConfirmar.style.display = 'block';
    }
    
    // Confirm the photo
    function confirmPhoto() {
        if (!photoData) return;
        
        // Here you can handle the confirmed photo
        // For example, save it to a hidden input field:
        // document.getElementById('fotoAluno').value = photoData;
        
        // Update UI
        btnConfirmar.style.display = 'none';
        btnCancelar.textContent = 'Refazer Foto';
    }
    
    // Stop the camera
    function stopCamera() {
        if (stream) {
            stream.getTracks().forEach(track => track.stop());
            stream = null;
        }
        
        // Reset UI
        isCameraActive = false;
        if (videoElement) videoElement.style.display = 'none';
        if (photoElement) photoElement.style.display = 'none';
        if (cameraPlaceholder) cameraPlaceholder.style.display = 'flex';
        if (btnAbrirCamera) btnAbrirCamera.style.display = 'block';
        if (btnTirarFoto) btnTirarFoto.style.display = 'none';
        if (btnCancelar) btnCancelar.style.display = 'none';
        if (btnConfirmar) btnConfirmar.style.display = 'none';
        
        // Reset photo data
        photoData = null;
    }
    
    // Show/hide loading state
    function showLoading(show) {
        if (cameraLoading) {
            cameraLoading.style.display = show ? 'flex' : 'none';
        }
    }
    
    // Public API
    return {
        init,
        startCamera,
        stopCamera,
        takePhoto,
        confirmPhoto,
        getPhotoData: () => photoData
    };
})();

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    CameraPreview.init();
});
