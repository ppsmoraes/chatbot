# # Baixa dados do NLTK (executar uma vez)
# import nltk
# nltk.download('punkt')
# nltk.download('stopwords')
# nltk.download('punkt_tab')

#     def get_intent_responses(self, tag: str) -> list[str]:
#         """Retorna todas as respostas de uma intent específica."""
#         for intent in self.intents:
#             if intent['tag'] == tag:
#                 return intent['responses']
#         return []

#     def set_user_name(self) -> str:
#         self.user_data['nome'] = user_input.strip()
#         self.context = {'nome_coletado': True}
#         responses = self.get_intent_responses('capturar_nome')
#         return random.choice(responses).replace('{nome}', self.user_data['nome'])

import json
import random
import string
import unicodedata

from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize


class ChatbotVoRomario:
    def __init__(self) -> None:
        self.intents: list[dict] = self.load_intents()
        self.stop_words: set[str] = set(stopwords.words('portuguese'))
        self.data: dict = {'menu': self.load_menu()}
        self.context: dict = {}
        self.bot_presentation()

    def load_json(self, file_path: str) -> dict:
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)

    def load_intents(self, intents_file_path: str = 'intents.json') -> list[dict]:
        return self.load_json(intents_file_path).get('intents')

    def load_menu(self, menu_file_path: str = 'menu.json') -> list[dict]:
        menu: list[dict] = self.load_json(menu_file_path).get('produtos')
        string_menu = '\n'.join([f'{b['nome']} - R${b['preco']:.2f}' for b in menu])
        return f'🍰 *MENU VÔ ROMÁRIO* 🍰\n{string_menu}'

    def preprocess_text(self, text: str) -> list[str]:
        # Remover pontuação
        prossed_text: str = text.translate(str.maketrans('', '', string.punctuation))
        # Transformar em minúsculo
        prossed_text = prossed_text.lower()
        # Remover acentos
        prossed_text = ''.join(
            c
            for c in unicodedata.normalize('NFD', prossed_text)
            if unicodedata.category(c) != 'Mn'
        )
        # Tokeniza as palavras
        tokens: list[str] = word_tokenize(prossed_text, language='portuguese')
        # Remove as 'stop_words'
        result: list[str] = [word for word in tokens if word not in self.stop_words]
        return result

    def bot_presentation(self) -> None:
        """Mostra a mensagem inicial automaticamente"""
        presetation_intent = next(
            intent for intent in self.intents if intent['tag'] == 'apresentacao'
        )
        print('🤖: ' + random.choice(presetation_intent['responses']))

    def buy_request(self):
        self.contexto['aguardando_pedido'] = True
        return 'Digite o *NÚMERO* do bolo desejado:\n' + self.show_menu()

    def get_response(self, user_input: str) -> str:
        processed_input: list[str] = self.preprocess_text(user_input)

        for intent in self.intents:
            if intent.get('context_filter') and not all(
                self.context.get(c) for c in intent['context_filter']
            ):
                continue  # Pula intents com contexto não satisfeito

            if any(
                word in processed_input
                for word in self.preprocess_text(' '.join(intent['patterns']))
            ):
                if intent.get('context_set'):
                    self.context = {k: True for k in intent['context_set']}

                response: str = random.choice(intent['responses'])
                return response.format(**self.data)

        return 'Desculpe, não entendi.'


if __name__ == '__main__':
    bot: ChatbotVoRomario = ChatbotVoRomario()

    while not bot.context.get('desligar'):
        user_input: str = input('Você: ')
        response: str = bot.get_response(user_input)
        print(f'🤖: {response}')
