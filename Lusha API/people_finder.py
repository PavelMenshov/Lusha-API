import json
from pathlib import Path

import requests

api_key_auth = ""
apis_lusha_api_yaml = "https://api.lusha.com"
person_file = Path("person_info.json")
url = "https://api.lusha.com/v2/person"

base_dir = Path(__file__).resolve().parent
person_file = base_dir / "person_info.json"
with person_file.open("r", encoding="utf-8") as src:
  person_data = json.load(src)

query = {
  "firstName": person_data.get("firstName", ""),
  "lastName": person_data.get("lastName", ""),
  "companyName": person_data.get("companyName", ""),
  "refreshJobInfo": "true",
  "revealEmails": "true",
  "revealPhones": "true",
}

headers = {"api_key": api_key_auth}

response = requests.get(url, headers=headers, params=query)

data = response.json()
if response.status_code == 200:
    contact_data = data.get('contact', {})
    
    # Check for the specific 'EMPTY_DATA' error structure
    if contact_data.get('error', {}).get('name') == 'EMPTY_DATA':
        print("There is no such person in Lusha's database")
    elif contact_data.get('data'):
        # Data was found and is present
        print("Person found! Details:")
        print(json.dumps(contact_data['data'], indent=4))
    else:
        # Handle other possible contact errors or unexpected structures
        print("Lusha API returned an unexpected response structure.")
        print(data)

elif response.status_code == 400:
    # This handles the previous "Bad Request" error (e.g., missing mandatory fields)
    print("Error: Bad Request. Check if all mandatory fields (name and company) are present.")
    print(data)

else:
    # Handle other non-200/400 HTTP errors
    print(f"Error: API request failed with status code {response.status_code}")
    print(data)