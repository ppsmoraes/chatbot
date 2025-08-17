# Vô Romário — Assistente de Casa de Bolos

Um chatbot simples em Python para apresentar o cardápio e encaminhar pedidos para a "Vô Romário - Casa de Bolos".

Projeto leve para demonstração de NLP básico usando NLTK e intents em JSON.

## Estrutura do repositório

- [main.py](main.py) — Implementação principal com a classe [`ChatbotVoRomario`](main.py) e seus métodos: [`load_menu`](main.py), [`preprocess_text`](main.py), [`bot_presentation`](main.py), [`buy_request`](main.py) e [`get_response`](main.py).
- [intents.json](intents.json) — Intents e respostas configuráveis.
- [menu.json](menu.json) — Cardápio consumido por [`ChatbotVoRomario`](main.py).
- [requirements.txt](requirements.txt) — Dependências do projeto.
- [run_checks.py](run_checks.py) — Script para executar verificações/linters/testes via CLI.
- [.gitignore](.gitignore) — Padrões ignorados pelo Git.

## Requisitos

- Python 3.8+
- Virtualenv (recomendado)
- Internet para baixar os dados do NLTK (apenas na primeira execução)

As dependências do projeto estão em [requirements.txt](requirements.txt).

## Instalação rápida

1. Criar e ativar um ambiente virtual (Opcional, mas recomendada):
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate
```

2. Instalar dependências:
```bash
pip install -r requirements.txt
```

3. Baixar os pacotes do NLTK (executar uma vez):
```py
python - <<'PY'
import nltk
nltk.download('punkt')
nltk.download('stopwords')
# (o projeto comenta 'punkt_tab' — adaptar se necessário)
```

## Uso

Inicie o chatbot:
```bash
python main.py
```

Exemplo de interação:
- Chatbot mostra a apresentação automática via [`bot_presentation`](main.py).
- Usuário digita `menu` ou `1` → intent `ver_menu` (veja [intents.json](intents.json)) e o bot responde com o conteúdo de [menu.json](menu.json) formatado por [`load_menu`](main.py).
- Usuário pode digitar palavras como `pedido`, `quero` para acionar o intent `atendente`.

Observação: o processamento de texto (remoção de pontuação, normalização, tokenização e remoção de stopwords) é feito em [`preprocess_text`](main.py).

## Testes e verificações

Execute as verificações definidas em [run_checks.py](run_checks.py):
```bash
python run_checks.py .
```
O script chama ferramentas em sequência: isort → black → pydocstyle → doctest → mypy → pytest (dependendo do ambiente).

## Personalização

- Edite as intenções e respostas em [intents.json](intents.json).
- Atualize o cardápio em [menu.json](menu.json).
- Para alterar comportamento do bot, edite a classe [`ChatbotVoRomario`](main.py).

## Notas e melhorias possíveis

- Tratar corretamente acentos/typos no JSON (ex.: "Maça" → "Maçã").
- Implementar fluxo de pedido (validação de seleção numérica, confirmação, armazenamento).
- Adicionar testes unitários e cobertura.
- Melhorar o mecanismo de matching (atualmente baseado em pre-processamento simples e comparação de tokens).

## Licença

Projeto para fins demonstrativos.