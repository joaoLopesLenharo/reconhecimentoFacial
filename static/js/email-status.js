// Verificar status do serviço de e-mail
document.addEventListener('DOMContentLoaded', function() {
    const emailStatus = document.getElementById('emailStatus');
    const emailConfigInfo = document.getElementById('emailConfigInfo');

    function updateEmailStatus() {
        fetch('/debug/email/status')
            .then(response => response.json())
            .then(status => {
                const isConfigured = status.smtp_configured === true || 
                                  status.status === 'configured';
                
                // Atualiza o badge de status
                const statusBadge = emailStatus;
                if (isConfigured) {
                    statusBadge.className = 'badge bg-success';
                    statusBadge.textContent = 'Configurado';
                    
                    // Mostra as informações de configuração
                    fetch('/api/email/config')
                        .then(response => response.json())
                        .then(config => {
                            if (config.success) {
                                emailConfigInfo.innerHTML = `
                                    <div class="table-responsive">
                                        <table class="table table-dark table-hover">
                                            <tbody>
                                                <tr>
                                                    <th>Servidor SMTP:</th>
                                                    <td>${config.smtp_server}:${config.smtp_port}</td>
                                                </tr>
                                                <tr>
                                                    <th>Usuário:</th>
                                                    <td>${config.smtp_username}</td>
                                                </tr>
                                                <tr>
                                                    <th>E-mail do Remetente:</th>
                                                    <td>${config.sender_email || config.smtp_username}</td>
                                                </tr>
                                            </tbody>
                                        </table>
                                    </div>
                                    <div class="alert alert-success mt-3">
                                        <i class="bi bi-check-circle me-2"></i>
                                        O serviço de e-mail está configurado corretamente.
                                    </div>
                                `;
                            }
                        });
                } else {
                    statusBadge.className = 'badge bg-warning';
                    statusBadge.textContent = 'Não configurado';
                    emailConfigInfo.innerHTML = `
                        <div class="alert alert-warning">
                            <i class="bi bi-exclamation-triangle me-2"></i>
                            O serviço de e-mail não está configurado. Crie ou edite o arquivo <code>email_config.json</code> no servidor.
                        </div>
                        <div class="alert alert-info">
                            <h6>Exemplo de configuração:</h6>
                            <pre class="bg-dark text-light p-3 rounded">{
  "SMTP_SERVER": "smtp.gmail.com",
  "SMTP_PORT": 587,
  "SMTP_USERNAME": "seu-email@gmail.com",
  "SMTP_PASSWORD": "sua-senha-app",
  "SMTP_SENDER_EMAIL": "seu-email@gmail.com",
  "SMTP_SENDER_NAME": "Sistema de Monitoramento"
}</pre>
                        </div>
                    `;
                }
            })
            .catch(error => {
                console.error('Erro ao verificar status do e-mail:', error);
                emailStatus.className = 'badge bg-danger';
                emailStatus.textContent = 'Erro';
                emailConfigInfo.innerHTML = `
                    <div class="alert alert-danger">
                        <i class="bi bi-x-circle me-2"></i>
                        Erro ao verificar o status do serviço de e-mail. Verifique o console para mais detalhes.
                    </div>
                `;
            });
    }

    // Verifica o status a cada 5 segundos
    updateEmailStatus();
    setInterval(updateEmailStatus, 5000);
});
