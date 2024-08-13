import requests
from base import Base
class Vllm(Base):
    def __init__(self, config=None):
        super().__init__(config)
        if config is None or "vllm_host" not in config:
            self.host = "http://localhost:8000"
        else:
            self.host = config["vllm_host"]

        if config is None or "model" not in config:
            raise ValueError("check the config for vllm")
        else:
            self.model = config["model"]

        if "auth-key" in config:
            self.auth_key = config["auth-key"]
        else:
            self.auth_key = None

    def system_message(self, message: str) -> any:
        return {"role": "system", "content": message}

    def user_message(self, message: str) -> any:
        return {"role": "user", "content": message}

    def assistant_message(self, message: str) -> any:
        return {"role": "assistant", "content": message}

    def submit_prompt(self, prompt, **kwargs) -> str:
        url = f"{self.host}/v1/chat/completions"
        data = {
            "model": self.model,
            "stream": False,
            "messages": prompt,
        }
        if self.auth_key is not None:
            headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.auth_key}'
            }
            response = requests.post(url, headers=headers,json=data)
        else:
            response = requests.post(url, json=data)
        response_dict = response.json()
        return response_dict['choices'][0]['message']['content']







