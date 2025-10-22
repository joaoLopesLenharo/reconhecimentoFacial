// Error Handler Module
const ErrorHandler = (() => {
    
    // Error types
    const ERROR_TYPES = {
        NETWORK: 'network',
        VALIDATION: 'validation',
        CAMERA: 'camera',
        SOCKET: 'socket',
        API: 'api',
        UNKNOWN: 'unknown'
    };
    
    // Error messages
    const ERROR_MESSAGES = {
        [ERROR_TYPES.NETWORK]: 'Erro de conexão. Verifique sua internet.',
        [ERROR_TYPES.VALIDATION]: 'Dados inválidos. Verifique os campos.',
        [ERROR_TYPES.CAMERA]: 'Erro na câmera. Verifique as permissões.',
        [ERROR_TYPES.SOCKET]: 'Conexão perdida. Tentando reconectar...',
        [ERROR_TYPES.API]: 'Erro no servidor. Tente novamente.',
        [ERROR_TYPES.UNKNOWN]: 'Erro desconhecido. Tente novamente.'
    };
    
    // Initialize error handling
    function init() {
        setupGlobalErrorHandlers();
        setupNetworkErrorHandling();
        setupSocketErrorHandling();
    }
    
    // Setup global error handlers
    function setupGlobalErrorHandlers() {
        // Handle unhandled promise rejections
        window.addEventListener('unhandledrejection', (event) => {
            console.error('Unhandled promise rejection:', event.reason);
            handleError(event.reason, ERROR_TYPES.UNKNOWN);
            event.preventDefault();
        });
        
        // Handle JavaScript errors
        window.addEventListener('error', (event) => {
            console.error('JavaScript error:', event.error);
            handleError(event.error, ERROR_TYPES.UNKNOWN);
        });
    }
    
    // Setup network error handling
    function setupNetworkErrorHandling() {
        // Monitor online/offline status
        window.addEventListener('online', () => {
            showAlert('Conexão restaurada!', 'success');
            hideNetworkError();
        });
        
        window.addEventListener('offline', () => {
            showAlert('Conexão perdida. Algumas funcionalidades podem não funcionar.', 'warning');
            showNetworkError();
        });
    }
    
    // Setup socket error handling
    function setupSocketErrorHandling() {
        if (typeof socket !== 'undefined') {
            socket.on('connect_error', (error) => {
                handleError(error, ERROR_TYPES.SOCKET);
            });
            
            socket.on('disconnect', (reason) => {
                if (reason === 'io server disconnect') {
                    showAlert('Servidor desconectado. Tentando reconectar...', 'warning');
                }
            });
            
            socket.on('reconnect', () => {
                showAlert('Reconectado ao servidor!', 'success');
            });
        }
    }
    
    // Main error handler
    function handleError(error, type = ERROR_TYPES.UNKNOWN, context = '') {
        console.error(`[${type.toUpperCase()}] ${context}:`, error);
        
        const errorInfo = {
            type,
            message: error.message || error,
            context,
            timestamp: new Date().toISOString(),
            userAgent: navigator.userAgent,
            url: window.location.href
        };
        
        // Log error for debugging
        logError(errorInfo);
        
        // Show user-friendly message
        const userMessage = getUserFriendlyMessage(error, type);
        showAlert(userMessage, getAlertType(type));
        
        // Handle specific error types
        switch (type) {
            case ERROR_TYPES.CAMERA:
                handleCameraError(error);
                break;
            case ERROR_TYPES.NETWORK:
                handleNetworkError(error);
                break;
            case ERROR_TYPES.API:
                handleApiError(error);
                break;
        }
    }
    
    // Get user-friendly error message
    function getUserFriendlyMessage(error, type) {
        // Check for specific error messages
        if (error.message) {
            if (error.message.includes('Permission denied')) {
                return 'Permissão negada. Verifique as configurações do navegador.';
            }
            if (error.message.includes('NotFoundError')) {
                return 'Câmera não encontrada. Verifique se está conectada.';
            }
            if (error.message.includes('NetworkError')) {
                return 'Erro de rede. Verifique sua conexão.';
            }
        }
        
        return ERROR_MESSAGES[type] || ERROR_MESSAGES[ERROR_TYPES.UNKNOWN];
    }
    
    // Get alert type for Bootstrap
    function getAlertType(errorType) {
        switch (errorType) {
            case ERROR_TYPES.NETWORK:
            case ERROR_TYPES.SOCKET:
                return 'warning';
            case ERROR_TYPES.VALIDATION:
                return 'info';
            default:
                return 'danger';
        }
    }
    
    // Handle camera-specific errors
    function handleCameraError(error) {
        const cameraContainer = document.getElementById('cameraContainer');
        if (cameraContainer) {
            showCameraError(error.message || 'Erro na câmera');
        }
        
        // Reset camera buttons
        resetCameraButtons();
    }
    
    // Handle network errors
    function handleNetworkError(error) {
        showNetworkError();
        
        // Disable network-dependent features
        disableNetworkFeatures();
    }
    
    // Handle API errors
    function handleApiError(error) {
        // Check if it's a server error (5xx) or client error (4xx)
        if (error.status >= 500) {
            showAlert('Erro no servidor. Nossa equipe foi notificada.', 'danger');
        } else if (error.status >= 400) {
            showAlert('Erro na solicitação. Verifique os dados enviados.', 'warning');
        }
    }
    
    // Show camera error
    function showCameraError(message) {
        const container = document.getElementById('cameraContainer');
        if (container) {
            container.innerHTML = `
                <div class="camera-error text-center p-4">
                    <i class="fas fa-exclamation-triangle fa-3x text-danger mb-3"></i>
                    <p class="text-danger">${message}</p>
                    <button class="btn btn-outline-light btn-sm" onclick="location.reload()">
                        <i class="fas fa-sync-alt me-1"></i> Tentar novamente
                    </button>
                </div>
            `;
        }
    }
    
    // Show network error indicator
    function showNetworkError() {
        let indicator = document.getElementById('network-error-indicator');
        if (!indicator) {
            indicator = document.createElement('div');
            indicator.id = 'network-error-indicator';
            indicator.className = 'alert alert-warning position-fixed top-0 start-50 translate-middle-x mt-2';
            indicator.style.zIndex = '9999';
            indicator.innerHTML = `
                <i class="fas fa-wifi"></i> Sem conexão com a internet
            `;
            document.body.appendChild(indicator);
        }
        indicator.style.display = 'block';
    }
    
    // Hide network error indicator
    function hideNetworkError() {
        const indicator = document.getElementById('network-error-indicator');
        if (indicator) {
            indicator.style.display = 'none';
        }
    }
    
    // Reset camera buttons to initial state
    function resetCameraButtons() {
        const btnIniciar = document.getElementById('iniciarMonitoramento');
        const btnParar = document.getElementById('pararMonitoramento');
        
        if (btnIniciar) {
            btnIniciar.disabled = false;
            btnIniciar.innerHTML = '<i class="fas fa-play"></i> Iniciar Monitoramento';
        }
        
        if (btnParar) {
            btnParar.disabled = true;
        }
    }
    
    // Disable network-dependent features
    function disableNetworkFeatures() {
        const networkButtons = document.querySelectorAll('[data-requires-network]');
        networkButtons.forEach(btn => {
            btn.disabled = true;
            btn.title = 'Requer conexão com a internet';
        });
    }
    
    // Enable network-dependent features
    function enableNetworkFeatures() {
        const networkButtons = document.querySelectorAll('[data-requires-network]');
        networkButtons.forEach(btn => {
            btn.disabled = false;
            btn.title = '';
        });
    }
    
    // Log error for debugging
    function logError(errorInfo) {
        // Store in localStorage for debugging
        try {
            const errors = JSON.parse(localStorage.getItem('app_errors') || '[]');
            errors.push(errorInfo);
            
            // Keep only last 50 errors
            if (errors.length > 50) {
                errors.splice(0, errors.length - 50);
            }
            
            localStorage.setItem('app_errors', JSON.stringify(errors));
        } catch (e) {
            console.warn('Could not store error in localStorage:', e);
        }
    }
    
    // Show alert using existing function
    function showAlert(message, type = 'danger') {
        if (typeof mostrarAlerta === 'function') {
            mostrarAlerta(message, type);
        } else {
            // Fallback alert
            console.warn('mostrarAlerta function not available, using console');
            console.log(`[${type.toUpperCase()}] ${message}`);
        }
    }
    
    // Retry mechanism for failed operations
    function retry(operation, maxAttempts = 3, delay = 1000) {
        return new Promise((resolve, reject) => {
            let attempts = 0;
            
            function attempt() {
                attempts++;
                operation()
                    .then(resolve)
                    .catch(error => {
                        if (attempts >= maxAttempts) {
                            reject(error);
                        } else {
                            console.log(`Attempt ${attempts} failed, retrying in ${delay}ms...`);
                            setTimeout(attempt, delay);
                        }
                    });
            }
            
            attempt();
        });
    }
    
    // Get stored errors for debugging
    function getStoredErrors() {
        try {
            return JSON.parse(localStorage.getItem('app_errors') || '[]');
        } catch (e) {
            return [];
        }
    }
    
    // Clear stored errors
    function clearStoredErrors() {
        localStorage.removeItem('app_errors');
    }
    
    // Public API
    return {
        init,
        handleError,
        retry,
        getStoredErrors,
        clearStoredErrors,
        ERROR_TYPES
    };
})();

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    ErrorHandler.init();
});

// Make available globally
window.ErrorHandler = ErrorHandler;
