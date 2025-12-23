import requests

def fetch_xml(full_url):
    response = requests.get(full_url)
    print(response)
    if response.status_code == 200:
        return response.content
    else:
        raise Exception(f"API request failed with status: {response.status_code}")
