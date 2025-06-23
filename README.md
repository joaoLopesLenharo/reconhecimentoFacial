# Sistema de Controle de Presença por Reconhecimento Facial

Este sistema permite o controle de presença de alunos através de reconhecimento facial, utilizando webcam e banco de dados MongoDB.

## Requisitos

- Python 3.8 ou superior
- MongoDB instalado e rodando localmente
- Webcam funcionando
- Dependências Python listadas em `requirements.txt`

## Instalação

1. Clone este repositório
2. Crie um ambiente virtual Python (recomendado):
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   ```
3. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```
4. Certifique-se que o MongoDB está rodando localmente na porta padrão (27017)

## Estrutura do Projeto

- `cadastro.py`: Funções para gerenciamento de alunos no MongoDB
- `interface_reconhecimento.py`: Interface gráfica e sistema de reconhecimento facial
- `requirements.txt`: Lista de dependências Python

## Uso

1. Execute o sistema:
   ```bash
   python interface_reconhecimento.py
   ```

2. A interface possui três abas:
   - **Monitoramento**: Inicia/para o monitoramento de presença
   - **Cadastro Rápido**: Cadastra novos alunos
   - **Listagem de Alunos**: Gerencia alunos cadastrados

3. Para cadastrar um aluno:
   - Preencha ID e Nome
   - Clique em "Capturar e Cadastrar"
   - Posicione o rosto na webcam

4. Para monitorar presença:
   - Clique em "Iniciar Monitoramento"
   - O sistema verificará a presença a cada 30 segundos
   - Os logs mostrarão quem está presente/ausente

## Funcionalidades

- Cadastro de alunos com foto
- Reconhecimento facial em tempo real
- Monitoramento automático de presença
- Gerenciamento de alunos (editar/excluir)
- Interface gráfica intuitiva
- Logs de presença/ausência

## Tratamento de Erros

O sistema inclui tratamento para:
- Falhas de conexão com MongoDB
- Erros de acesso à webcam
- Duplicidade de IDs
- Falhas em operações de arquivo
- Erros de reconhecimento facial

## Observações

- As codificações faciais dos alunos são salvas diretamente no banco de dados MongoDB, não mais imagens no diretório Alunos/
- O sistema usa a webcam padrão (índice 0)
- O monitoramento verifica a presença a cada 30 segundos
- É necessário ter boa iluminação para melhor reconhecimento facial 