import requests
import certifi

url = 'https://example.com'
response = requests.get(url, verify=certifi.where())
print(response.content)
