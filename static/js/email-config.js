// Configuração do serviço de e-mail SMTP
document.addEventListener('DOMContentLoaded', function() {
    const emailConfigForm = document.getElementById('emailConfigForm');
    const emailStatus = document.getElementById('emailStatus');
    const btnTestEmail = document.getElementById('btnTestEmail');

    // Verificar status do serviço de e-mail
    function checkEmailStatus() {
        fetch('/debug/email/status')
            .then(response => response.json())
            .then(status => {
                const isConfigured = status.smtp_configured === true || 
                                  status.smtp_username === 'configured';
                updateEmailStatus(isConfigured, isConfigured ? 'Configurado' : 'Não configurado');
                
                // Se configurado, carrega as configurações
                if (isConfigured) {
                    loadEmailConfig();
                }
            })
            .catch(error => {
                console.error('Erro ao verificar status do e-mail:', error);
                updateEmailStatus(false, 'Erro ao verificar status');
            });
    }

    // Carregar configurações salvas
    function loadEmailConfig() {
        fetch('/api/email/config')
            .then(response => response.json())
            .then(config => {
                if (config.success && config.config) {
                    document.getElementById('smtpServer').value = config.config.SMTP_SERVER || '';
                    document.getElementById('smtpPort').value = config.config.SMTP_PORT || '587';
                    document.getElementById('smtpEmail').value = config.config.SMTP_USERNAME || '';
                    // Não carregamos a senha por segurança
                }
            })
            .catch(error => {
                console.error('Erro ao carregar configurações de e-mail:', error);
            });
    }

    // Atualizar status do e-mail na UI
    function updateEmailStatus(isConfigured, message = '') {
        const statusBadge = emailStatus.querySelector('.badge');
        if (isConfigured) {
            statusBadge.className = 'badge bg-success';
            statusBadge.textContent = 'Configurado';
            statusBadge.title = message || 'O serviço de e-mail está configurado corretamente';
        } else {
            statusBadge.className = 'badge bg-warning';
            statusBadge.textContent = message || 'Não configurado';
            statusBadge.title = 'Clique para configurar o serviço de e-mail';
        }
        
        // Atualiza o estado dos botões
        const testButton = document.getElementById('btnTestEmail');
        if (testButton) {
            testButton.disabled = !isConfigured;
        }
    }

    // Salvar configurações
    emailConfigForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const config = {
            SMTP_SERVER: document.getElementById('smtpServer').value,
            SMTP_PORT: parseInt(document.getElementById('smtpPort').value),
            SMTP_USERNAME: document.getElementById('smtpEmail').value,
            SMTP_PASSWORD: document.getElementById('smtpPassword').value
        };

        fetch('/api/email/config', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(config)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                updateEmailStatus(true, 'Configuração salva com sucesso!');
                // Limpar campo de senha após salvar
                document.getElementById('smtpPassword').value = '';
                mostrarAlerta('Configurações de e-mail salvas com sucesso!', 'success');
            } else {
                throw new Error(data.error || 'Erro ao salvar configurações');
            }
        })
        .catch(error => {
            console.error('Erro ao salvar configurações:', error);
            mostrarAlerta(`Erro ao salvar configurações: ${error.message}`, 'danger');
        });
    });

    // Testar envio de e-mail
    btnTestEmail.addEventListener('click', function() {
        const email = prompt('Digite o e-mail para teste:');
        if (!email) return;

        mostrarAlerta('Enviando e-mail de teste...', 'info');
        
        fetch('/debug/email/test', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ to: email })
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                mostrarAlerta('E-mail de teste enviado com sucesso!', 'success');
            } else {
                throw new Error(data.message || 'Falha ao enviar e-mail de teste');
            }
        })
        .catch(error => {
            console.error('Erro ao enviar e-mail de teste:', error);
            mostrarAlerta(`Erro: ${error.message}. Verifique o console para mais detalhes.`, 'danger');
        });
    });

    // Verificar status ao iniciar
    checkEmailStatus();
    
    // Atualizar a cada 5 segundos (opcional)
    setInterval(checkEmailStatus, 5000);
});
