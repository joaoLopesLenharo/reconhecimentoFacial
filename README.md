# Sistema de Reconhecimento Facial para Registro de Presença

Este projeto é um sistema de reconhecimento facial desenvolvido em Python que permite registrar a presença de alunos em um ambiente educacional. O sistema utiliza uma câmera para detectar e identificar alunos, registrando a presença no banco de dados apenas uma vez enquanto eles estão na câmera.

## Funcionalidades

- Reconhecimento facial em tempo real.
- Registro da presença dos alunos no banco de dados SQLite.
- Garantia de que a presença seja registrada apenas uma vez enquanto o aluno estiver na câmera.
- Visualização das informações dos alunos e registro de presença no terminal.

## Tecnologias Utilizadas

- Python
- OpenCV
- SQLite
- NumPy

## Estrutura do Projeto

```
/reconhecimentoFacial
├── app.py # Arquivo principal para executar o sistema
├── camera.py # Módulo para capturar imagens da câmera
├── chamada.py # Módulo para gerenciar a chamada e o registro de presença
├── database.py # Módulo para interagir com o banco de dados SQLite
├── groq_api.py # Módulo para integração com a API Groq
├── interface.py # Módulo para a interface gráfica do usuário
└── requirements.txt # Lista de dependências do projeto
```

## Instalação

1. Clone o repositório:

   ```bash
   git clone https://github.com/joaoLopesLenharo/reconhecimentoFacial
   cd reconhecimentoFacial
   ```

2. Crie um ambiente virtual (opcional, mas recomendado):

   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   ```

3. Instale as dependências:

   ```bash
   pip install -r requirements.txt
   ```

## Uso

1. Certifique-se de que a câmera esteja conectada e funcionando.
2. Execute o módulo `app.py`:

   ```bash
   python app.py
   ```

3. A interface de reconhecimento facial será aberta.


## Configuração do Banco de Dados

O sistema utiliza um banco de dados SQLite chamado `alunos.db`. O módulo `database.py` cuida da criação das tabelas e da inserção de dados. As tabelas são criadas automaticamente pelo sistema.

## Contribuição

Contribuições são bem-vindas! Se você tiver sugestões de melhorias ou correções, sinta-se à vontade para abrir um issue ou enviar um pull request.

## Contato

Para dúvidas ou sugestões, entre em contato com joao.pedro.lopes.lenharo@gmail.com.
