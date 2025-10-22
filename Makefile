# Makefile para Sistema de Controle de Presença

.PHONY: help install test test-unit test-integration test-js test-all coverage clean lint security setup-dev run

# Configurações
PYTHON = python
PIP = pip
NPM = npm

help: ## Mostra esta ajuda
	@echo "Sistema de Controle de Presença - Comandos Disponíveis:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Instala dependências Python
	$(PIP) install -r requirements.txt
	$(PIP) install -r requirements-test.txt

install-js: ## Instala dependências JavaScript
	$(NPM) install

setup-dev: install install-js ## Configura ambiente de desenvolvimento
	@echo "Ambiente de desenvolvimento configurado!"

test: ## Executa todos os testes
	$(PYTHON) run_tests.py

test-unit: ## Executa apenas testes unitários
	$(PYTHON) run_tests.py --type unit

test-integration: ## Executa apenas testes de integração
	$(PYTHON) run_tests.py --type integration

test-fast: ## Executa apenas testes rápidos
	$(PYTHON) run_tests.py --type fast

test-js: ## Executa apenas testes JavaScript
	$(PYTHON) run_tests.py --js-only

test-python: ## Executa apenas testes Python
	$(PYTHON) run_tests.py --python-only

coverage: ## Gera relatório de cobertura
	$(PYTHON) run_tests.py --coverage
	@echo "Relatórios de cobertura:"
	@echo "- Python: htmlcov/index.html"
	@echo "- JavaScript: coverage/index.html"

lint: ## Executa verificações de código
	$(PYTHON) -m flake8 . --exclude=venv,htmlcov,node_modules
	$(PYTHON) -m bandit -r . -x tests,venv

security: ## Executa verificações de segurança
	$(PYTHON) -m bandit -r . -x tests,venv
	$(PYTHON) -m safety check

quality: lint security ## Executa todas as verificações de qualidade

clean: ## Remove arquivos temporários
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	rm -rf htmlcov/
	rm -rf coverage/
	rm -rf .coverage
	rm -rf .pytest_cache/
	rm -rf node_modules/
	rm -rf test_report.html

run: ## Executa a aplicação
	$(PYTHON) app.py

run-dev: ## Executa a aplicação em modo desenvolvimento
	FLASK_ENV=development $(PYTHON) app.py

docker-build: ## Constrói imagem Docker
	docker build -t sistema-presenca .

docker-run: ## Executa aplicação no Docker
	docker run -p 5000:5000 sistema-presenca

ci: clean install test quality ## Pipeline completo de CI
	@echo "Pipeline de CI executado com sucesso!"

report: ## Gera relatório completo de testes
	$(PYTHON) run_tests.py --report
	@echo "Relatório gerado: test_report.html"
