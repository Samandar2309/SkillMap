import requests

url = "https://wrc5knt6jwfmb7kpqi57mfec.agents.do-ai.run/api/v1/chat/completions"

headers = {
    "Authorization": "Bearer xaFfwLNLlQF0IVlQG9E4RVo_wA4Q1tUl",
    "Content-Type": "application/json"
}

data = {
    "messages": [
        {
            "role": "user",
            "content": "Create a Django backend roadmap for beginner"
        }
    ],
    "stream": False,
    "include_functions_info": True,
    "include_retrieval_info": True,
    "include_guardrails_info": True
}

res = requests.post(url, headers=headers, json=data)

print(res.json())
