import base64
from openai import OpenAI
from dotenv import load_dotenv
import os

# Load API key
load_dotenv(dotenv_path=".env", override=True)
api_key1 = os.getenv("OPENAI_API_KEY")

# Initialize client
client = OpenAI(api_key=api_key1)

# Load image from local PC and convert to base64
image_path = "math2.webp"  # your local image
with open(image_path, "rb") as f:
    image_base64 = base64.b64encode(f.read()).decode("utf-8")

# Ask GPT-4o mini with text + image
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "user", "content": [
            {"type": "text", "text": "solve the following math problem"},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
        ]}
    ],
)

print(response.choices[0].message.content)
