import requests

response = requests.get("http://127.0.0.1:8000/api/test")
print(response.status_code)
print(response.text)

answer = response.json()["message"]
print(f"Answer: {answer}")
