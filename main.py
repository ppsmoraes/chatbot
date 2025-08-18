# TODO Adicionar docstring

import json
import random
import re
import string
import unicodedata

from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

# TODO Utilize no formato try...execpt
# # Baixa dados do NLTK (executar uma vez)
# import nltk
# nltk.download('punkt')
# nltk.download('stopwords')
# nltk.download('punkt_tab')


class ChatbotVoRomario:
    def __init__(self) -> None:
        # TODO Adicionar docstring
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
        """Abre um arquivo json e retorna seu conteúdo.

        Parameters
        ----------
        file_path : str
            O caminho do arquivo.

        Returns
        -------
        dict
            O conteúdo do json.
        """
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)

    def load_intents(self, intents_file_path: str = 'intents.json') -> list[dict]:
        """Abre o arquivo de intents e retorna seu conteúdo.

        Parameters
        ----------
        intents_file_path : str, optional
            Caminho do arquivo, por padrão é 'intents.json'

        Returns
        -------
        list[dict]
            A lista de intents.
        """
        return self.load_json(intents_file_path).get('intents', [])

    def load_products(self, menu_file_path: str = 'menu.json') -> list[dict]:
        """Abre o arquivo do menu e retorna seu conteúdo.

        Parameters
        ----------
        menu_file_path : str, optional
            Caminho do arquivo, por padrão é 'menu.json'

        Returns
        -------
        list[dict]
            A lista de produtos.
        """
        # TODO Use um banco de dados relacionais (sql-based) no lugar de um json.
        return self.load_json(menu_file_path).get('produtos', [])

    def load_str_menu(self) -> str:
        """Retorna o menu em formato de texto.

        Returns
        -------
        str
            O menu formatado para texto.
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
        if not hasattr(self, '_stop_words'):
            self._stop_words: set[str] = set(stopwords.words('portuguese'))
        return self._stop_words

    def normalize(self, text: str) -> str:
        text = text.lower()
        text = text.translate(str.maketrans('', '', string.punctuation))
        text = ''.join(
            c
            for c in unicodedata.normalize('NFD', text)
            if unicodedata.category(c) != 'Mn'
        )
        return text

    def preprocess_text(self, text: str) -> list[str]:
        tokens: list[str] = word_tokenize(self.normalize(text), language='portuguese')
        result: list[str] = [word for word in tokens if word not in self.stop_words]
        return result

    # ----------------------------
    # Índice de sabores a partir do menu
    # ----------------------------
    def build_flavor_index(self, products: list[dict]) -> list[dict]:
        """Cria um índice com possíveis frases/keywords de sabores baseadas no 'nome' de cada produto.

        Examples
        --------
        'Bolo de Maçã' -> phrase='maca', keywords={'maca'}
        'Bolo de Doce de Leite' -> phrase='doce de leite', keywords={'doce', 'leite'}
        """
        # TODO Deixe essa docstring no padrão numpy.
        index: list[dict] = []
        for p in products:
            original_name: str = p.get('nome')
            norm_name: str = self.normalize(original_name)

            # tenta extrair a parte depois de "bolo(s) de "
            m: Match[str] | None = re.search(r'\bbolos?\s+de\s+(.+)', norm_name)
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
    # TODO Valide essas extrações
    def extrair_quantidade(self, text_norm: str) -> int | None:
        # Casos especiais: "meia dúzia", "uma dúzia"
        if re.search(r'\bmeia\s+d[uú]zia\b', text_norm):
            return 6
        if re.search(r'\b(um|uma)\s+d[uú]zia\b', text_norm):
            return 12

        # Dígitos
        m = re.search(r'\b(\d{1,3})\b', text_norm)
        if m:
            try:
                return int(m.group(1))
            except ValueError:
                pass

        # Números por extenso (básico)
        num_words = {
            'um': 1,
            'uma': 1,
            'dois': 2,
            'duas': 2,
            'tres': 3,
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
        }
        for w, n in num_words.items():
            if re.search(fr'\b{w}\b', text_norm):
                return n
        return None

    def extrair_sabor(self, text_norm: str) -> dict | None:
        """
        Tenta identificar o produto/sabor mais provável com base no menu.
        Retorna: {'produto': <nome do produto>, 'sabor': <frase de sabor normalizada>}
        """
        # TODO Deixe essa docstring no padrão numpy.
        if not self.flavor_index:
            # Fallback simples: pega o que vier depois de "de "
            m = re.search(r'\bde\s+([\w\s]{1,40})', text_norm)
            if m:
                return {
                    'produto': m.group(1).strip().title(),
                    'sabor': m.group(1).strip(),
                }
            return None

        tokens = set(re.findall(r'\w+', text_norm))
        best = None
        best_score = 0

        for item in self.flavor_index:
            score = 0

            # Pontos por "frase" aparecer como substring
            if item['phrase'] and item['phrase'] in text_norm:
                score += len(item['phrase'])

            # Pontos por keywords encontradas nos tokens do usuário
            if item['keywords']:
                score += len(item['keywords'] & tokens) * 3

            if score > best_score:
                best_score = score
                best = item

        if best and best_score > 0:
            return {'produto': best['original'], 'sabor': best['phrase']}
        return None

    def extrair_pedido(self, frase: str) -> dict | None:
        text_norm = self.normalize(frase)

        quantidade = self.extrair_quantidade(text_norm)
        sabor_info = self.extrair_sabor(text_norm)

        if quantidade is None and sabor_info is None:
            return None

        pedido = {}
        if quantidade is not None:
            pedido['quantidade'] = quantidade
        if sabor_info is not None:
            pedido.update(sabor_info)  # adiciona 'produto' e 'sabor'
        return pedido

    # ----------------------------
    # Fluxo de conversa
    # ----------------------------
    def bot_presentation(self) -> None:
        """Mostra a mensagem inicial automaticamente"""
        # TODO Deixe essa docstring no padrão numpy.
        presetation_intent = next(
            intent for intent in self.intents if intent['tag'] == 'apresentacao'
        )
        print('🤖: ' + random.choice(presetation_intent['responses']))

    def buy_request(self, user_input: str) -> str:
        pedido = self.extrair_pedido(user_input)

        if not pedido:
            return 'Entendi que você quer comprar. Pode me dizer a **quantidade** e o **sabor**? 🙂'

        # Guarda no contexto para próximos passos (confirmação, endereço, etc.)
        self.context['pedido'] = pedido

        qtd_txt = f"{pedido['quantidade']}x " if 'quantidade' in pedido else ""
        prod_txt = pedido.get('produto') or f"bolo de {pedido.get('sabor', '').title()}"
        return f"Anotei: {qtd_txt}{prod_txt}. Confere?"

    def get_response(self, user_input: str) -> str:
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

                if bot.context.get('comprar'):
                    print(self.flavor_index)
                    # self.build_flavor_index()
                    # return self.buy_request(user_input)

                response: str = random.choice(intent['responses'])
                return response.format(**self.data)

        return 'Desculpe, não entendi.'


if __name__ == '__main__':
    bot: ChatbotVoRomario = ChatbotVoRomario()

    while not bot.context.get('desligar'):
        user_input: str = input('Você: ')
        response: str = bot.get_response(user_input)
        print(f'🤖: {response}')
