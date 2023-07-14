import openai


class ChatGPT:
    def __init__(self, api_key, history_messages=None, model='gpt-3.5-turbo'):
        self.api_key = api_key
        self.history_messages = history_messages if history_messages else []
        self.model = model

    def query(self, message: str):
        new_message = self.history_messages + [{"role": "user", "content": message}]

        openai.api_key = self.api_key
        result = openai.ChatCompletion.create(model=self.model, messages=new_message)

        self.history_messages = new_message + [result.choices[0].message]
        return result.choices[0].message.content

    def temp_query(self, message):
        new_message = self.history_messages + [{"role": "user", "content": message}]

        openai.api_key = self.api_key
        result = openai.ChatCompletion.create(model=self.model, messages=new_message)

        return result.choices[0].message.content

    def get_history_messages(self):
        return self.history_messages
