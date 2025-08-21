"""Chatbot simples para o "Vô Romário".

Este módulo implementa a classe ChatbotVoRomario que carrega um menu e intents
a partir de arquivos JSON, realiza pré-processamento básico de texto em português,
extrai pedidos (quantidade + sabor) e mantém um contexto simples de conversa.

Observações
---------
- Uso de NLTK para tokenização e stopwords.
- Estrutura de intents esperada: {"intents": [{"tag": ..., "patterns": [...], "responses": [...]}]}
- Estrutura do menu esperada: {"produtos": [{"nome": ..., "preco": ...}, ...]}
"""

import json
import random
import re
import unicodedata
from string import punctuation

try:
    from nltk.corpus import stopwords  # type: ignore[import]

    stopwords.words('portuguese')
    del stopwords
except LookupError:
    import nltk  # type: ignore[import]

    nltk.download('stopwords', quiet=True)
    nltk.download('punkt_tab', quiet=True)
    del nltk
finally:
    from nltk.corpus import stopwords
    from nltk.tokenize import word_tokenize  # type: ignore[import]


class ChatbotVoRomario:
    """Chatbot para atender pedidos do menu do "Vô Romário".

    A classe carrega intents e produtos, constrói um índice de sabores a partir
    do nome dos produtos e fornece métodos para pré-processar texto, extrair
    entidades (quantidade, sabor) e gerar respostas simples com base em intents
    e contexto.

    Atributos
    ---------
    intents : list[dict]
        Lista de intents carregadas do arquivo de intents.
    products : list[dict]
        Lista de produtos carregados do arquivo de menu.
    flavor_index : list[dict]
        Índice construído a partir dos nomes dos produtos para ajudar a identificar sabores.
    data : dict
        Dados usados para formatação de respostas (ex.: menu como string).
    context : dict
        Dicionário que armazena o estado/contexto atual da conversa.
    """

    def __init__(self) -> None:
        """Inicializa o ChatbotVoRomario.

        A inicialização realiza as seguintes ações:
        - carrega as intents a partir de 'intents.json';
        - carrega os produtos a partir de 'menu.json';
        - constrói um índice de sabores a partir dos nomes dos produtos;
        - prepara o dicionário `data` com a representação em texto do menu;
        - inicializa o contexto da conversa;
        - exibe a apresentação do bot (chama bot_presentation).
        """
        self.intents: list[dict] = self.load_intents()
        self.products: list[dict] = self.load_products()
        self.flavor_index: list[dict] = self.build_flavor_index(self.products)
        self.data: dict = {'menu': self.load_str_menu()}
        self.context: dict = {}
        self.bot_presentation()

    # ----------------------------
    # Utilidades de dados/arquivos
    # ----------------------------
    def load_json(self, file_path: str) -> dict:
        """Abre um arquivo JSON e retorna seu conteúdo.

        Parameters
        ----------
        file_path : str
            Caminho do arquivo JSON.

        Returns
        -------
        dict
            Conteúdo do arquivo JSON desserializado.
        """
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)

    def load_intents(self, intents_file_path: str = 'intents.json') -> list[dict]:
        """Carrega intents a partir de um arquivo JSON.

        Parameters
        ----------
        intents_file_path : str, optional
            Caminho do arquivo, por padrão é 'intents.json'.

        Returns
        -------
        list[dict]
            Lista de intents. Retorna lista vazia se a chave 'intents' não existir.
        """
        return self.load_json(intents_file_path).get('intents', [])

    def load_products(self, menu_file_path: str = 'menu.json') -> list[dict]:
        """Carrega produtos do menu a partir de um arquivo JSON.

        Parameters
        ----------
        menu_file_path : str, optional
            Caminho do arquivo, por padrão é 'menu.json'

        Returns
        -------
        list[dict]
            Lista de produtos (cada produto é um dicionário).
        """
        # TODO Use um banco de dados relacionais (sql-based) no lugar de um json.
        return self.load_json(menu_file_path).get('produtos', [])

    def load_str_menu(self) -> str:
        """Gera uma representação em texto do menu para ser usada em respostas.

        Returns
        -------
        str
            Texto formatado contendo o nome e preço de cada produto.
        """
        string_menu = '\n'.join(
            [f'{b['nome']} - R${b['preco']:.2f}' for b in self.products]
        )
        return f'🍰 *MENU VÔ ROMÁRIO* 🍰\n{string_menu}'

    # ----------------------------
    # Normalização e NLP simples
    # ----------------------------
    # TODO Crie as docstrings de todos os métodos/funções daqui pra baixo
    @property
    def stop_words(self) -> set[str]:
        """Conjunto de stopwords em português.

        O resultado é cacheado no atributo privado _stop_words na primeira chamada.

        Returns
        -------
        set[str]
            Conjunto de palavras a serem ignoradas durante o pré-processamento.
        """
        if not hasattr(self, '_stop_words'):
            self._stop_words: set[str] = set(stopwords.words('portuguese'))
        return self._stop_words

    def normalize(self, text: str) -> str:
        """Normaliza o texto para facilitar comparação.

        Operações realizadas:
        - converte para minúsculas
        - remove pontuação
        - remove acentuação (normalização Unicode NFD e remoção de marcas)

        Parameters
        ----------
        text : str
            Texto original.

        Returns
        -------
        str
            Texto normalizado.
        """
        text = text.lower()
        text = text.translate(str.maketrans('', '', punctuation))
        text = ''.join(
            c
            for c in unicodedata.normalize('NFD', text)
            if unicodedata.category(c) != 'Mn'
        )
        return text

    def preprocess_text(self, text: str) -> list[str]:
        """Tokeniza e remove stopwords de uma string normalizada.

        Parameters
        ----------
        text : str
            Texto de entrada (pode ser não-normalizado; a função chama normalize()).

        Returns
        -------
        list[str]
            Lista de tokens úteis (sem stopwords).
        """
        tokens: list[str] = word_tokenize(self.normalize(text), language='portuguese')
        result: list[str] = [word for word in tokens if word not in self.stop_words]
        return result

    # ----------------------------
    # Índice de sabores a partir do menu
    # ----------------------------
    def build_flavor_index(self, products: list[dict]) -> list[dict]:
        """Cria um índice de sabores a partir dos nomes dos produtos.

        Para cada produto cria um dicionário com:
        - 'original': nome original exibido no menu
        - 'phrase': parte relevante do nome (normalizada), por exemplo a parte após "bolo(s) de"
        - 'keywords': conjunto de palavras-chave extraídas da phrase (stopwords removidas)

        Parameters
        ----------
        products : list[dict]
            Lista de produtos (cada um deve ter a chave 'nome').

        Returns
        -------
        list[dict]
            Índice de sabores usado para identificar correspondências em mensagens de usuários.

        Examples
        --------
        'Bolo de Maçã' -> {'original': 'Bolo de Maçã', 'phrase': 'maca', 'keywords': {'maca'}}
        'Bolo de Doce de Leite' -> {'original': 'Bolo de Doce de Leite',
                                     'phrase': 'doce de leite',
                                     'keywords': {'doce', 'leite'}}
        """
        index: list[dict] = []
        for p in products:
            original_name: str = p.get('nome')
            norm_name: str = self.normalize(original_name)

            # tenta extrair a parte depois de "bolo(s) de "
            # TODO Incluir type hint
            m = re.search(r'\bbolos?\s+de\s+(.+)', norm_name)
            phrase: str = m.group(1).strip() if m else norm_name

            # keywords = tokens da frase sem stopwords comuns
            tokens = [
                t
                for t in re.findall(r'\w+', phrase)
                if t not in self.stop_words and t not in {'bolo', 'bolos'}
            ]
            index.append(
                {
                    'original': original_name,  # Nome visível no menu
                    'phrase': phrase,  # Frase (normalizada) que descreve o sabor
                    'keywords': set(
                        tokens
                    ),  # Palavras-chave para "casar" com o texto do cliente
                }
            )
        return index

    # ----------------------------
    # Extração de entidades (pedido)
    # ----------------------------
    def extrair_quantidade(self, text_norm: str) -> int | None:
        """Extrai a quantidade solicitada no texto normalizado.

        A função reconhece:
        - expressões como "meia dúzia" (6) e "uma dúzia" (12)
        - números escritos como dígitos (até 2 dígitos)
        - números por extenso básicos (até vinte)

        Parameters
        ----------
        text_norm : str
            Texto já normalizado (minúsculas, sem acento/pontuação).

        Returns
        -------
        int | None
            Quantidade encontrada ou None se não houver indicação.
        """
        # Dúzias
        if re.search(r'\bmeia\s+d[uú]zia\b', text_norm):
            return 6
        if re.search(r'\b(um|uma)\s+d[uú]zia\b', text_norm):
            return 12

        # Dígitos
        m = re.search(r'\b(\d{1,2})\b', text_norm)  # Busca números de 1 ou 2 dígitos
        if m:
            try:
                return int(m.group(1))
            except ValueError:
                pass

        # Números por extenso
        num_words = {
            'um': 1,
            'uma': 1,
            'dois': 2,
            'duas': 2,
            'tres': 3,
            'quatro': 4,
            'cinco': 5,
            'seis': 6,
            'sete': 7,
            'oito': 8,
            'nove': 9,
            'dez': 10,
            'onze': 11,
            'doze': 12,
            'treze': 13,
            'quatorze': 14,
            'catore': 14,
            'quinze': 15,
            'dezesseis': 16,
            'dezessete': 17,
            'dezoito': 18,
            'dezenove': 19,
            'vinte': 20,
        }
        # TODO Fazer busca valores com mais de uma palavra, por exemplo: "vinte e dois".
        for w, n in num_words.items():
            if re.search(fr'\b{w}\b', text_norm):
                return n
        return None

    def extrair_sabor(self, text_norm: str) -> dict | None:
        """Identifica o sabor/produto mais provável a partir do texto.

        A função compara tokens do texto com o índice de sabores e calcula uma
        pontuação baseada em:
        - ocorrência direta da 'phrase' no texto
        - número de keywords em comum (peso aplicado)

        Parameters
        ----------
        text_norm : str
            Texto já normalizado.

        Returns
        -------
        dict | None
            Se encontrado, retorna {'produto': nome_exibido, 'sabor': frase_normalizada}.
            Caso contrário, retorna None.
        """
        tokens: set[str] = set(re.findall(r'\w+', text_norm))
        best: None | dict = None
        best_score: int = 0

        for item in self.flavor_index:
            score: int = 0

            # Pontos por "frase" aparecer como substring
            if item['phrase'] and item['phrase'] in text_norm:
                score += len(item['phrase'])

            # Pontos por keywords encontradas nos tokens do usuário
            if item['keywords']:
                # TODO 3 é o melhor fator a ser utilizado?
                score += len(item['keywords'] & tokens) * 3

            if score > best_score:
                best_score = score
                best = item

        if best and best_score > 0:
            return {'produto': best['original'], 'sabor': best['phrase']}
        return None

    def extrair_pedido(self, frase: str) -> dict | None:
        """Extrai um pedido (quantidade e/ou sabor) de uma frase livre.

        Parameters
        ----------
        frase : str
            Frase original do usuário.

        Returns
        -------
        dict | None
            Dicionário com chaves possíveis: 'quantidade', 'produto', 'sabor'.
            Retorna None se não for possível extrair quantidade nem sabor.
        """
        text_norm: str = self.normalize(frase)

        qtd: int | None = self.extrair_quantidade(text_norm)
        sabor_info: dict | None = self.extrair_sabor(text_norm)

        if qtd is None and sabor_info is None:
            return None

        pedido: dict = {}
        if qtd is not None:
            pedido['quantidade'] = qtd
        if sabor_info is not None:
            pedido.update(sabor_info)  # adiciona 'produto' e 'sabor'
        return pedido

    # ----------------------------
    # Fluxo de conversa
    # ----------------------------
    def bot_presentation(self) -> None:
        """Exibe a mensagem de apresentação do bot na inicialização."""
        presetation_intent = next(i for i in self.intents if i['tag'] == 'apresentacao')
        print('🤖: ' + random.choice(presetation_intent['responses']))

    # TODO Valide esse método
    def buy_request(self, user_input: str) -> str:
        """Processa um pedido quando o usuário demonstra intenção de comprar.

        Extrai quantidade e sabor a partir do texto; atualiza o contexto com o
        pedido identificado e retorna uma frase de confirmação/solicitação de mais dados.

        Parameters
        ----------
        user_input : str
            Texto do usuário contendo o pedido.

        Returns
        -------
        str
            Mensagem de retorno do bot (pede esclarecimento se necessário ou confirma o pedido).
        """
        pedido: dict | None = self.extrair_pedido(user_input)

        if not pedido:
            return 'Entendi que você quer comprar. Pode me dizer a **quantidade** e o **sabor**? 🙂'

        # Guarda no contexto para próximos passos (confirmação, endereço, etc.)
        self.context['pedido'] = pedido

        qtd_txt = f"{pedido['quantidade']}x " if 'quantidade' in pedido else ""
        prod_txt = pedido.get('produto') or f"bolo de {pedido.get('sabor', '').title()}"
        return f"Anotei: {qtd_txt}{prod_txt}. Confere?"

    def get_response(self, user_input: str) -> str:
        """Gera uma resposta com base nas intents e no contexto atual.

        O método pré-processa a entrada do usuário, tenta casar com intents
        (respeitando filtros de contexto) e retorna uma resposta formatada.

        Parameters
        ----------
        user_input : str
            Texto inserido pelo usuário.

        Returns
        -------
        str
            Resposta selecionada (ou mensagem padrão se não houver correspondência).
        """
        processed_input: list[str] = self.preprocess_text(user_input)

        for intent in self.intents:
            if intent.get('context_filter') and not all(
                self.context.get(c) for c in intent['context_filter']
            ):
                continue  # Pula intents com contexto não satisfeito

            if any(
                word in processed_input
                for word in self.preprocess_text(' '.join(intent.get('patterns', [])))
            ):
                if intent.get('context_set'):
                    self.context = {k: True for k in intent['context_set']}

                if self.context.get('comprar'):
                    # TODO Construa esse código
                    print(self.flavor_index)
                    # self.build_flavor_index()
                    # return self.buy_request(user_input)

                response: str = random.choice(intent['responses'])
                return response.format(**self.data)

        return 'Desculpe, não entendi.'


def main() -> None:
    """Ponto de entrada do programa: inicializa o bot e interage em loop com o usuário."""
    bot: ChatbotVoRomario = ChatbotVoRomario()

    while not bot.context.get('desligar'):
        user_input: str = input('Você: ')
        response: str = bot.get_response(user_input)
        print(f'🤖: {response}')


if __name__ == '__main__':
    main()
