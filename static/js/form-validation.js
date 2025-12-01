// Form Validation Module
const FormValidation = (() => {
    
    // Initialize form validation
    function init() {
        setupFormValidation();
        setupStudentForm();
        setupEmailValidation();
        setupPhoneFormatting();
        setupTestModeToggle();
        setupFileInputHandler();
        setupCameraButtons();
    }
    
    // Setup camera buttons to sync with CameraPreview
    function setupCameraButtons() {
        const btnAbrirCameraCadastro = document.getElementById('btnAbrirCameraCadastro');
        const btnTirarFotoCadastro = document.getElementById('btnTirarFotoCadastro');
        const btnCancelarCadastro = document.getElementById('btnCancelarCadastro');
        
        // Sincroniza btnAbrirCameraCadastro com btnAbrirCameraPreview
        if (btnAbrirCameraCadastro) {
            btnAbrirCameraCadastro.addEventListener('click', () => {
                const btnPreview = document.getElementById('btnAbrirCameraPreview');
                if (btnPreview) {
                    btnPreview.click();
                    // Atualiza visibilidade dos botões do formulário após um pequeno delay
                    setTimeout(() => {
                        const btnTirarPreview = document.getElementById('btnTirarFotoPreview');
                        const btnCancelarPreview = document.getElementById('btnCancelarCamera');
                        if (btnTirarPreview && btnTirarPreview.style.display !== 'none') {
                            btnAbrirCameraCadastro.style.display = 'none';
                            if (btnTirarFotoCadastro) btnTirarFotoCadastro.style.display = 'block';
                            if (btnCancelarCadastro) btnCancelarCadastro.style.display = 'block';
                        }
                    }, 100);
                }
            });
        }
        
        // Sincroniza btnTirarFotoCadastro com btnTirarFotoPreview
        if (btnTirarFotoCadastro) {
            btnTirarFotoCadastro.addEventListener('click', () => {
                const btnPreview = document.getElementById('btnTirarFotoPreview');
                if (btnPreview) {
                    btnPreview.click();
                }
            });
        }
        
        // Sincroniza btnCancelarCadastro com btnCancelarCamera
        if (btnCancelarCadastro) {
            btnCancelarCadastro.addEventListener('click', () => {
                const btnCancelarPreview = document.getElementById('btnCancelarCamera');
                if (btnCancelarPreview) {
                    btnCancelarPreview.click();
                }
                // Para o CameraPreview se estiver ativo
                if (typeof CameraPreview !== 'undefined' && CameraPreview.stopCamera) {
                    CameraPreview.stopCamera();
                } else if (typeof window.CameraPreview !== 'undefined' && window.CameraPreview.stopCamera) {
                    window.CameraPreview.stopCamera();
                }
                // Atualiza visibilidade dos botões do formulário
                if (btnAbrirCameraCadastro) btnAbrirCameraCadastro.style.display = 'block';
                if (btnTirarFotoCadastro) btnTirarFotoCadastro.style.display = 'none';
                btnCancelarCadastro.style.display = 'none';
                // Reseta a foto
                resetPhotoCapture();
            });
        }
    }
    
    // Setup file input handler for test mode
    function setupFileInputHandler() {
        const fileInput = document.getElementById('fileInputCadastro');
        if (!fileInput) return;
        
        fileInput.addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (file) {
                // Valida tipo de arquivo
                if (!file.type.startsWith('image/')) {
                    mostrarAlerta('Por favor, selecione um arquivo de imagem válido.', 'warning');
                    fileInput.value = '';
                    updateRegisterButtonState();
                    return;
                }
                
                // Valida tamanho (máximo 10MB)
                if (file.size > 10 * 1024 * 1024) {
                    mostrarAlerta('A imagem deve ter no máximo 10MB.', 'warning');
                    fileInput.value = '';
                    updateRegisterButtonState();
                    return;
                }
                
                // Mostra preview
                const reader = new FileReader();
                reader.onload = (event) => {
                    const photoPreview = document.getElementById('fotoPreview');
                    const placeholder = document.getElementById('cameraPlaceholder');
                    
                    if (photoPreview) {
                        photoPreview.src = event.target.result;
                        photoPreview.style.display = 'block';
                    }
                    if (placeholder) placeholder.style.display = 'none';
                    
                    updateRegisterButtonState();
                };
                reader.readAsDataURL(file);
            } else {
                updateRegisterButtonState();
            }
        });
    }
    
    // Setup Bootstrap form validation
    function setupFormValidation() {
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
    }
    
    // Setup student registration form
    function setupStudentForm() {
        const form = document.getElementById('formCadastro');
        if (!form) return;
        
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            if (!form.checkValidity()) {
                form.classList.add('was-validated');
                return;
            }
            
            await submitStudentForm();
        });
    }
    
    // Submit student form
    async function submitStudentForm() {
        const form = document.getElementById('formCadastro');
        const submitBtn = document.getElementById('btnRegistrar');
        
        try {
            // Disable submit button
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status"></span> Registrando...';
            
            // Get photo data (async)
            const frameData = await getPhotoData();
            
            // Get form data
            const formData = {
                id: parseInt(document.getElementById('idAluno').value),
                nome: document.getElementById('nomeAluno').value.trim(),
                resp_telefone: document.getElementById('respTelefone').value.trim() || null,
                resp_email: document.getElementById('respEmail').value.trim() || null,
                frame: frameData
            };
            
            // Validate required fields
            if (!formData.id || !formData.nome || !formData.frame) {
                throw new Error('Por favor, preencha todos os campos obrigatórios e ' + 
                    (document.getElementById('testModeCadastro')?.checked ? 'selecione uma imagem.' : 'capture uma foto.'));
            }
            
            // Submit to API
            const response = await fetch('/api/alunos', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });
            
            const result = await response.json();
            
            if (result.success) {
                mostrarAlerta('Aluno cadastrado com sucesso!', 'success');
                form.reset();
                form.classList.remove('was-validated');
                
                // Para qualquer stream de câmera ativo no cadastro
                const videoPreview = document.getElementById('videoPreviewCadastro');
                if (videoPreview && videoPreview.srcObject) {
                    const stream = videoPreview.srcObject;
                    stream.getTracks().forEach(track => track.stop());
                    videoPreview.srcObject = null;
                }
                
                // Para o CameraPreview se estiver ativo
                if (typeof CameraPreview !== 'undefined' && CameraPreview.stopCamera) {
                    CameraPreview.stopCamera();
                } else if (typeof window.CameraPreview !== 'undefined' && window.CameraPreview.stopCamera) {
                    window.CameraPreview.stopCamera();
                }
                
                // Reload students list e câmeras
                await carregarDadosIniciais();
                
                // Reset photo capture
                resetPhotoCapture();
            } else {
                throw new Error(result.error || 'Erro ao cadastrar aluno');
            }
            
        } catch (error) {
            console.error('Erro ao cadastrar aluno:', error);
            mostrarAlerta(`Erro ao cadastrar aluno: ${error.message}`, 'danger');
        } finally {
            // Re-enable submit button
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<i class="fas fa-save"></i> Registrar Aluno';
        }
    }
    
    // Get photo data from camera preview or file input
    function getPhotoData() {
        const testModeCadastro = document.getElementById('testModeCadastro');
        const isTestMode = testModeCadastro && testModeCadastro.checked;
        
        if (isTestMode) {
            // Modo teste: obtém do input de arquivo
            const fileInput = document.getElementById('fileInputCadastro');
            if (fileInput && fileInput.files && fileInput.files.length > 0) {
                const file = fileInput.files[0];
                return new Promise((resolve, reject) => {
                    const reader = new FileReader();
                    reader.onload = (e) => resolve(e.target.result);
                    reader.onerror = reject;
                    reader.readAsDataURL(file);
                });
            }
            return Promise.resolve(null);
        } else {
            // Modo normal: obtém da câmera
            const photoElement = document.getElementById('fotoPreview');
            if (photoElement && photoElement.src && photoElement.src.startsWith('data:')) {
                return Promise.resolve(photoElement.src);
            }
            return Promise.resolve(null);
        }
    }
    
    // Reset photo capture
    function resetPhotoCapture() {
        const photoElement = document.getElementById('fotoPreview');
        const videoElement = document.getElementById('videoPreviewCadastro');
        const placeholder = document.getElementById('cameraPlaceholder');
        const fileInput = document.getElementById('fileInputCadastro');
        
        // Para qualquer stream de câmera ativo
        if (videoElement && videoElement.srcObject) {
            const stream = videoElement.srcObject;
            stream.getTracks().forEach(track => track.stop());
            videoElement.srcObject = null;
        }
        
        if (photoElement) photoElement.style.display = 'none';
        if (videoElement) videoElement.style.display = 'none';
        if (placeholder) placeholder.style.display = 'flex';
        if (fileInput) fileInput.value = '';
        
        // Reset buttons
        const btnAbrir = document.getElementById('btnAbrirCameraCadastro');
        const btnTirar = document.getElementById('btnTirarFotoCadastro');
        const btnCancelar = document.getElementById('btnCancelarCadastro');
        const btnRegistrar = document.getElementById('btnRegistrar');
        
        if (btnAbrir) btnAbrir.style.display = 'block';
        if (btnTirar) btnTirar.style.display = 'none';
        if (btnCancelar) btnCancelar.style.display = 'none';
        if (btnRegistrar) btnRegistrar.disabled = true;
    }
    
    // Setup test mode toggle for registration
    function setupTestModeToggle() {
        const testModeToggle = document.getElementById('testModeCadastro');
        if (!testModeToggle) return;
        
        testModeToggle.addEventListener('change', (e) => {
            const isTestMode = e.target.checked;
            toggleRegistrationMode(isTestMode);
        });
    }
    
    // Toggle between camera and file input modes
    function toggleRegistrationMode(isTestMode) {
        const cameraSection = document.getElementById('cameraModeSection');
        const fileSection = document.getElementById('fileModeSection');
        const cameraButtons = document.getElementById('cameraModeButtons');
        const cameraSelect = document.getElementById('cameraSelectCadastro');
        const fileInput = document.getElementById('fileInputCadastro');
        const photoPreview = document.getElementById('fotoPreview');
        const videoPreview = document.getElementById('videoPreviewCadastro');
        const placeholder = document.getElementById('cameraPlaceholder');
        
        if (isTestMode) {
            // Mostra input de arquivo, esconde câmera
            if (cameraSection) cameraSection.style.display = 'none';
            if (fileSection) fileSection.style.display = 'block';
            if (cameraButtons) cameraButtons.style.display = 'none';
            if (cameraSelect) cameraSelect.removeAttribute('required');
            if (fileInput) fileInput.setAttribute('required', 'required');
            
            // Limpa preview de câmera
            if (videoPreview) {
                const stream = videoPreview.srcObject;
                if (stream) {
                    stream.getTracks().forEach(track => track.stop());
                    videoPreview.srcObject = null;
                }
                videoPreview.style.display = 'none';
            }
            
            // Mostra placeholder
            if (placeholder) placeholder.style.display = 'flex';
            if (photoPreview) photoPreview.style.display = 'none';
            
            // Reseta botões de câmera
            const btnAbrir = document.getElementById('btnAbrirCameraCadastro');
            const btnTirar = document.getElementById('btnTirarFotoCadastro');
            const btnCancelar = document.getElementById('btnCancelarCadastro');
            if (btnAbrir) btnAbrir.style.display = 'block';
            if (btnTirar) btnTirar.style.display = 'none';
            if (btnCancelar) btnCancelar.style.display = 'none';
        } else {
            // Mostra câmera, esconde input de arquivo
            if (cameraSection) cameraSection.style.display = 'block';
            if (fileSection) fileSection.style.display = 'none';
            if (cameraButtons) cameraButtons.style.display = 'block';
            if (cameraSelect) cameraSelect.setAttribute('required', 'required');
            if (fileInput) fileInput.removeAttribute('required');
            
            // Limpa preview de arquivo
            if (fileInput) fileInput.value = '';
            if (photoPreview) photoPreview.style.display = 'none';
        }
        
        // Atualiza estado do botão registrar
        updateRegisterButtonState();
    }
    
    // Update register button state based on current mode
    function updateRegisterButtonState() {
        const btnRegistrar = document.getElementById('btnRegistrar');
        const testModeCadastro = document.getElementById('testModeCadastro');
        const isTestMode = testModeCadastro && testModeCadastro.checked;
        
        if (!btnRegistrar) return;
        
        if (isTestMode) {
            const fileInput = document.getElementById('fileInputCadastro');
            btnRegistrar.disabled = !(fileInput && fileInput.files && fileInput.files.length > 0);
        } else {
            const photoElement = document.getElementById('fotoPreview');
            btnRegistrar.disabled = !(photoElement && photoElement.src && photoElement.src.startsWith('data:'));
        }
    }
    
    // Setup email validation
    function setupEmailValidation() {
        const emailInputs = document.querySelectorAll('input[type="email"]');
        emailInputs.forEach(input => {
            input.addEventListener('blur', validateEmail);
            input.addEventListener('input', clearEmailError);
        });
    }
    
    // Validate email format
    function validateEmail(event) {
        const input = event.target;
        const email = input.value.trim();
        
        if (email && !isValidEmail(email)) {
            input.setCustomValidity('Por favor, insira um email válido');
            input.classList.add('is-invalid');
        } else {
            input.setCustomValidity('');
            input.classList.remove('is-invalid');
        }
    }
    
    // Clear email error
    function clearEmailError(event) {
        const input = event.target;
        input.classList.remove('is-invalid');
        input.setCustomValidity('');
    }
    
    // Check if email is valid
    function isValidEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }
    
    // Setup phone number formatting
    function setupPhoneFormatting() {
        const phoneInputs = document.querySelectorAll('input[type="tel"]');
        phoneInputs.forEach(input => {
            input.addEventListener('input', formatPhone);
        });
    }
    
    // Format phone number
    function formatPhone(event) {
        const input = event.target;
        let value = input.value.replace(/\D/g, ''); // Remove non-digits
        
        // Format as (XX) XXXXX-XXXX
        if (value.length >= 11) {
            value = value.replace(/(\d{2})(\d{5})(\d{4})/, '($1) $2-$3');
        } else if (value.length >= 7) {
            value = value.replace(/(\d{2})(\d{4})(\d{0,4})/, '($1) $2-$3');
        } else if (value.length >= 3) {
            value = value.replace(/(\d{2})(\d{0,5})/, '($1) $2');
        }
        
        input.value = value;
    }
    
    // Validate student ID
    function validateStudentId(id) {
        const numId = parseInt(id);
        return numId > 0 && numId <= 999999;
    }
    
    // Setup student ID validation
    function setupStudentIdValidation() {
        const idInput = document.getElementById('idAluno');
        if (!idInput) return;
        
        idInput.addEventListener('blur', (event) => {
            const id = event.target.value;
            if (id && !validateStudentId(id)) {
                event.target.setCustomValidity('ID deve ser um número entre 1 e 999999');
                event.target.classList.add('is-invalid');
            } else {
                event.target.setCustomValidity('');
                event.target.classList.remove('is-invalid');
            }
        });
    }
    
    // Public API
    return {
        init,
        validateEmail: isValidEmail,
        validateStudentId,
        formatPhone,
        updateRegisterButtonState
    };
})();

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    FormValidation.init();
});

// Expose globally for other modules
window.FormValidation = FormValidation;
