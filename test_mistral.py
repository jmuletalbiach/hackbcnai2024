
from mistralai.client import MistralClient
from mistralai.models.chat_completion import ChatMessage
import environment_var

api_key = environment_var.mistral_ai_key
model = "mistral-large-latest"

client = MistralClient(api_key=api_key)

chat_response = client.chat(
    model=model,
    messages=[ChatMessage(role="user", content="What is the best French cheese?")]
)

print(chat_response.choices[0].message.content)