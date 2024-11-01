# groq_api.py
from groq import Groq
import base64
import cv2

class GroQAPI:
    def __init__(self):
        self.client = Groq(api_key="your-api-key")

    def encode_image(self, image):
        _, buffer = cv2.imencode('.jpg', image)
        return base64.b64encode(buffer).decode('utf-8')

    def get_description(self, image):
        base64_image = self.encode_image(image)
        # Código para obter a descrição da aparência
        chat_completion = self.client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Descreva a aparência física observada da pessoa..."},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}},
                    ],
                }
            ],
            model="llama-3.2-11b-vision-preview",
        )
        return chat_completion.choices[0].message.content

