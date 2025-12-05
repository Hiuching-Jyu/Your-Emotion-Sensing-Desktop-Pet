import requests

DOUBAO_URL = "https://api.doubao.com/v1/chat/completions"
DOUBAO_KEY = "YOUR_KEY_HERE"

def ask_doubao(user_text):
    """
    Send user_text to Doubao and return the assistant's reply.
    """
    headers = {
        "Authorization": f"Bearer {DOUBAO_KEY}",
        "Content-Type": "application/json"
    }

    body = {
        "model": "doubao-lite-v1",   
        "messages": [
            {"role": "user", "content": user_text}
        ]
    }

    try:
        r = requests.post(DOUBAO_URL, json=body, headers=headers, timeout=30)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]
    except Exception as e:
        print("Doubao API error:", e)
        return "（豆包接口暂时无法连接）"
