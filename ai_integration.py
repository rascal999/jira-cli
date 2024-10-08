import openai
import os

class AIIntegration:
    def __init__(self):
        openai.api_key = os.getenv('OPENAI_API_KEY')
        self.model = os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo')

    def ask_question(self, question):
        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": question}
                ]
            )
            answer = response.choices[0].message['content'].strip()
            return answer
        except Exception as e:
            return f"Error in AI response: {e}"
