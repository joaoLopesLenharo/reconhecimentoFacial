// Form Validation Module
const FormValidation = (() => {
    
    // Initialize form validation
    function init() {
        setupFormValidation();
        setupStudentForm();
        setupEmailValidation();
        setupPhoneFormatting();
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
            
            // Get form data
            const formData = {
                id: parseInt(document.getElementById('idAluno').value),
                nome: document.getElementById('nomeAluno').value.trim(),
                resp_telefone: document.getElementById('respTelefone').value.trim() || null,
                resp_email: document.getElementById('respEmail').value.trim() || null,
                frame: getPhotoData()
            };
            
            // Validate required fields
            if (!formData.id || !formData.nome || !formData.frame) {
                throw new Error('Por favor, preencha todos os campos obrigatórios e capture uma foto.');
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
                
                // Reload students list
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
    
    // Get photo data from camera preview
    function getPhotoData() {
        // This should integrate with the camera preview module
        const photoElement = document.getElementById('fotoPreview');
        if (photoElement && photoElement.src && photoElement.src.startsWith('data:')) {
            return photoElement.src;
        }
        return null;
    }
    
    // Reset photo capture
    function resetPhotoCapture() {
        const photoElement = document.getElementById('fotoPreview');
        const videoElement = document.getElementById('videoPreviewCadastro');
        const placeholder = document.getElementById('cameraPlaceholder');
        
        if (photoElement) photoElement.style.display = 'none';
        if (videoElement) videoElement.style.display = 'none';
        if (placeholder) placeholder.style.display = 'flex';
        
        // Reset buttons
        const btnAbrir = document.getElementById('btnAbrirCameraCadastro');
        const btnTirar = document.getElementById('btnTirarFotoCadastro');
        const btnRegistrar = document.getElementById('btnRegistrar');
        
        if (btnAbrir) btnAbrir.style.display = 'block';
        if (btnTirar) btnTirar.style.display = 'none';
        if (btnRegistrar) btnRegistrar.disabled = true;
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
        formatPhone
    };
})();

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    FormValidation.init();
});
