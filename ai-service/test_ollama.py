
import ollama

response = ollama.chat(
    model="qwen2.5:7b",
    messages=[
        {
            "role": "user",
            "content": "Explain what a hospital discharge summary is in simple English."
        }
    ]
)

print(response["message"]["content"])
