from groq import Groq, GroqError

from app.core.config import settings
from app.core.exceptions import UniAssistException
from app.core.logger import logger


class GroqClient:

    def __init__(self):

        self.client = Groq(
            api_key=settings.GROQ_API_KEY
        )

    def generate(self, prompt):

        try:

            response = self.client.chat.completions.create(

                model=settings.MODEL_NAME,

                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],

                temperature=0.2

            )

        except GroqError as e:

            logger.error(f"[GROQ] Generation failed: {e}")

            raise UniAssistException(
                f"Failed to generate a response from the language model: {e}"
            ) from e

        return response.choices[0].message.content