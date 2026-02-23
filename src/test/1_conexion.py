from openai import OpenAI

client = OpenAI()

mi_mensaje = "imprime 0"

resp = client.chat.completions.create(
    model="gpt-5",
    messages=[{"role": "user", "content": f"{mi_mensaje}"}]
)



print(resp.choices[0].message.content)
