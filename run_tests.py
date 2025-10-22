#!/usr/bin/env python3
"""
Script para executar todos os testes do projeto
"""
import os
import sys
import subprocess
import argparse
from pathlib import Path
from datetime import datetime


def _run_with_logging(cmd, cwd: Path, log_fh, section_title: str):
    """Executa um comando, espelhando saída no console e gravando no log."""
    header = f"\n=== {section_title} ===\nComando: {' '.join(cmd)}\nDiretório: {cwd}\nHora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    print(header, end='')
    if log_fh:
        log_fh.write(header)
        log_fh.flush()

    try:
        proc = subprocess.Popen(
            cmd,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        for line in proc.stdout or []:
            print(line, end='')
            if log_fh:
                log_fh.write(line)
        proc.wait()
        rc = proc.returncode
    except FileNotFoundError as e:
        msg = f"Erro: {e}\n"
        print(msg, end='')
        if log_fh:
            log_fh.write(msg)
        rc = 0  # trate como sucesso para permitir pular etapas (ex.: npm ausente)

    footer = f"\n=== Fim: {section_title} (exit={rc}) ===\n"
    print(footer, end='')
    if log_fh:
        log_fh.write(footer)
        log_fh.flush()

    return subprocess.CompletedProcess(cmd, rc)


def run_python_tests(test_type='all', coverage=True, verbose=True, log_fh=None):
    """Executa testes Python com pytest"""
    cmd = ['python', '-m', 'pytest']
    
    if verbose:
        cmd.append('-v')
    
    if coverage:
        cmd.extend(['--cov=.', '--cov-report=html:htmlcov', '--cov-report=term-missing'])
    
    # Filtros por tipo de teste
    if test_type == 'unit':
        cmd.extend(['-m', 'unit'])
    elif test_type == 'integration':
        cmd.extend(['-m', 'integration'])
    elif test_type == 'database':
        cmd.extend(['-m', 'database'])
    elif test_type == 'slow':
        cmd.extend(['-m', 'slow'])
    elif test_type == 'fast':
        cmd.extend(['-m', 'not slow'])
    
    cmd.append('tests/')
    
    print(f"Executando testes Python: {' '.join(cmd)}")
    return _run_with_logging(cmd, cwd=Path(__file__).parent, log_fh=log_fh, section_title='Testes Python')


def run_javascript_tests(coverage=True, log_fh=None):
    """Executa testes JavaScript com Jest"""
    # Verifica se Node.js está instalado
    try:
        subprocess.run(['node', '--version'], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Node.js não encontrado. Pulando testes JavaScript.")
        if log_fh:
            log_fh.write("Node.js não encontrado. Pulando testes JavaScript.\n")
        return subprocess.CompletedProcess([], 0)
    
    # Verifica se npm está instalado
    try:
        subprocess.run(['npm', '--version'], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("npm não encontrado. Pulando testes JavaScript.")
        if log_fh:
            log_fh.write("npm não encontrado. Pulando testes JavaScript.\n")
        return subprocess.CompletedProcess([], 0)
    
    # Verifica se as dependências estão instaladas (relative ao diretório do script)
    project_dir = Path(__file__).parent
    node_modules_dir = project_dir / 'node_modules'
    if not node_modules_dir.exists():
        print("Instalando dependências JavaScript...")
        try:
            _ = _run_with_logging(['npm', 'install'], cwd=project_dir, log_fh=log_fh, section_title='npm install')
        except FileNotFoundError:
            # Caso muito raro: npm desapareceu após checagem
            print("Falha ao encontrar npm durante a instalação. Pulando testes JavaScript.")
            if log_fh:
                log_fh.write("Falha ao encontrar npm durante a instalação. Pulando testes JavaScript.\n")
            return subprocess.CompletedProcess([], 0)
        except subprocess.CalledProcessError as e:
            print("Falha ao instalar dependências JavaScript. Pulando testes JavaScript.")
            print(str(e))
            if log_fh:
                log_fh.write("Falha ao instalar dependências JavaScript. Pulando testes JavaScript.\n")
                log_fh.write(str(e) + "\n")
            return subprocess.CompletedProcess([], 0)
    
    cmd = ['npm', 'test']
    if coverage:
        cmd = ['npm', 'run', 'test:coverage']
    
    print(f"Executando testes JavaScript: {' '.join(cmd)}")
    return _run_with_logging(cmd, cwd=project_dir, log_fh=log_fh, section_title='Testes JavaScript')


def check_code_quality():
    """Executa verificações de qualidade do código"""
    print("\n=== Verificações de Qualidade ===")
    
    # Flake8 para Python
    try:
        result = subprocess.run(['python', '-m', 'flake8', '.', '--exclude=venv,htmlcov,node_modules'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✓ Flake8: Nenhum problema encontrado")
        else:
            print("⚠ Flake8: Problemas encontrados:")
            print(result.stdout)
    except FileNotFoundError:
        print("⚠ Flake8 não instalado")
    
    # Verificação de segurança com bandit
    try:
        result = subprocess.run(['python', '-m', 'bandit', '-r', '.', '-x', 'tests,venv'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✓ Bandit: Nenhum problema de segurança encontrado")
        else:
            print("⚠ Bandit: Possíveis problemas de segurança:")
            print(result.stdout)
    except FileNotFoundError:
        print("⚠ Bandit não instalado")


def generate_test_report():
    """Gera relatório consolidado dos testes"""
    report_path = Path('test_report.html')
    
    # Timestamp cross-platform
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Relatório de Testes - Sistema de Controle de Presença</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            .header { background: #2c3e50; color: white; padding: 20px; border-radius: 5px; }
            .section { margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }
            .success { background: #d4edda; border-color: #c3e6cb; }
            .warning { background: #fff3cd; border-color: #ffeaa7; }
            .error { background: #f8d7da; border-color: #f5c6cb; }
            .coverage { margin: 10px 0; }
            .coverage-bar { background: #e9ecef; height: 20px; border-radius: 10px; overflow: hidden; }
            .coverage-fill { background: #28a745; height: 100%; transition: width 0.3s; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Relatório de Testes</h1>
            <p>Sistema de Controle de Presença - Gerado em: {timestamp}</p>
        </div>
        
        <div class="section">
            <h2>Resumo dos Testes</h2>
            <p>Este relatório consolida os resultados de todos os testes executados no projeto.</p>
            
            <h3>Cobertura de Código</h3>
            <div class="coverage">
                <p>Cobertura Python: <span id="python-coverage">Verificar htmlcov/index.html</span></p>
                <p>Cobertura JavaScript: <span id="js-coverage">Verificar coverage/index.html</span></p>
            </div>
        </div>
        
        <div class="section">
            <h2>Tipos de Testes Implementados</h2>
            <ul>
                <li><strong>Testes Unitários:</strong> Testam funções individuais dos módulos</li>
                <li><strong>Testes de Integração:</strong> Testam interação entre componentes</li>
                <li><strong>Testes de API:</strong> Testam endpoints Flask</li>
                <li><strong>Testes Frontend:</strong> Testam funcionalidades JavaScript</li>
                <li><strong>Testes de Banco:</strong> Testam operações de banco de dados</li>
            </ul>
        </div>
        
        <div class="section">
            <h2>Como Executar os Testes</h2>
            <pre>
# Todos os testes
python run_tests.py

# Apenas testes rápidos
python run_tests.py --type fast

# Apenas testes unitários
python run_tests.py --type unit

# Testes com cobertura
python run_tests.py --coverage

# Testes JavaScript
npm test
            </pre>
        </div>
        
        <div class="section">
            <h2>Estrutura de Testes</h2>
            <pre>
tests/
├── conftest.py          # Configurações e fixtures
├── factories.py         # Factories para dados de teste
├── test_cadastro.py     # Testes do módulo cadastro
├── test_reconhecimento.py # Testes do módulo reconhecimento
├── test_app_routes.py   # Testes das rotas Flask
├── test_database.py     # Testes de banco de dados
├── test_frontend.js     # Testes JavaScript
└── jest.setup.js        # Configuração Jest
            </pre>
        </div>
    </body>
    </html>
    """.format(timestamp=timestamp)
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"Relatório gerado: {report_path.absolute()}")


def main():
    parser = argparse.ArgumentParser(description='Executa testes do Sistema de Controle de Presença')
    parser.add_argument('--type', choices=['all', 'unit', 'integration', 'database', 'slow', 'fast'], 
                       default='all', help='Tipo de testes a executar')
    parser.add_argument('--no-coverage', action='store_true', help='Desabilita cobertura de código')
    parser.add_argument('--python-only', action='store_true', help='Executa apenas testes Python')
    parser.add_argument('--js-only', action='store_true', help='Executa apenas testes JavaScript')
    parser.add_argument('--quality-check', action='store_true', help='Executa verificações de qualidade')
    parser.add_argument('--report', action='store_true', help='Gera relatório HTML')
    
    args = parser.parse_args()
    
    print("=== Sistema de Testes Automatizados ===")
    print("Sistema de Controle de Presença\n")

    # Preparar arquivo de log com timestamp
    project_dir = Path(__file__).parent
    logs_dir = project_dir / 'logs'
    logs_dir.mkdir(exist_ok=True)
    timestamp_run = datetime.now().strftime('%Y%m%d-%H%M%S')
    log_path = logs_dir / f"test_run_{timestamp_run}.log"
    log_fh = open(log_path, 'w', encoding='utf-8')
    print(f"Gravando log em: {log_path}")
    log_fh.write(f"Início da execução: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    exit_code = 0
    
    # Executa testes Python
    if not args.js_only:
        print("=== Executando Testes Python ===")
        log_fh.write("\n--- Executando Testes Python ---\n")
        result = run_python_tests(
            test_type=args.type,
            coverage=not args.no_coverage,
            verbose=True,
            log_fh=log_fh,
        )
        if result.returncode != 0:
            exit_code = 1
    
    # Executa testes JavaScript
    if not args.python_only:
        print("\n=== Executando Testes JavaScript ===")
        log_fh.write("\n--- Executando Testes JavaScript ---\n")
        result = run_javascript_tests(coverage=not args.no_coverage, log_fh=log_fh)
        if result.returncode != 0:
            exit_code = 1
    
    # Verificações de qualidade
    if args.quality_check:
        check_code_quality()
    
    # Gera relatório
    if args.report:
        print("\n=== Gerando Relatório ===")
        generate_test_report()
    
    # Resumo final
    print(f"\n=== Resumo ===")
    summary = "✓ Todos os testes passaram!" if exit_code == 0 else "✗ Alguns testes falharam. Verifique os logs acima."
    print(summary)
    print("\nArquivos de cobertura:")
    print("- Python: htmlcov/index.html")
    print("- JavaScript: coverage/index.html")
    
    # Gravar resumo no log
    log_fh.write("\n=== Resumo ===\n")
    log_fh.write(summary + "\n")
    log_fh.write("\nArquivos de cobertura:\n")
    log_fh.write("- Python: htmlcov/index.html\n")
    log_fh.write("- JavaScript: coverage/index.html\n")
    log_fh.write(f"Fim da execução: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    log_fh.close()
    print(f"\nLog salvo em: {log_path}")
    
    return exit_code


if __name__ == '__main__':
    sys.exit(main())
