# Lusha-API-
This repo includes two main codes, that are used to find a distinct person by his/her name and company name OR personal ID and to parse and mark down a specific amount of people (chosen by specified requirements)
## Overview: 
*Don't forget to use your own valid API!*
```
API_KEY = ""  #for api_parser.py
api_key_auth = "" #for people_finder.py
```
The program called people_finder.py uses the Lusha API to easily find different people and their additional personal information (such as phone number, email, LinkedIn profile link, company, position, location, etc.). This program uses Lusha API to send a HTTP request to Lusha’s open data base and find all the additional info. The code works together with the AI, since a worker can either specify who he/she wants to find or not. The program can be used with first, last name and company’s name OR with explanation of which person a worker wants to find. 
The program called api_parser.py uses API key to send the request to the Lusha for parsing specified amount of people who meet the requirements written in the code, mark down the content and save it in the same directory with the code. Two additional files are required to be in the directory with the code - `data.json` for saving IDs of all the people who meet the requirements, `parsed_contacts.json` for saving enriched contacts with all the available additional information (by using the API call with person's ID) and `parse_history.json` to save all the IDs that were enriched previously. 
(*Don't forget to change these settings!*)
```
payload = {
        "pages": {"page": page, "size": PAGE_SIZE},
        "filters": {
            "contacts": {
                "include": {
                    "departments": [], #include valid departments here (can be found similar way as industries IDs)
                    "existing_data_points": ["phone", "work_email"],
                }
            },
            "companies": {
                "include": { #both IDs can be found using Lusha's API documentation or parsing the request on your own
                    "mainIndustriesIds": [], #include industries' ID here
                    "subIndustriesIds": [], #include subindustries' ID here
                }
            },
        },
    }
```
## How to use the program:
1. Copy this repo using Terminal command
```
git clone <this repo's full URL>
```
2. Download all the neccessary dependencies by using this command in Terminal
```
pip install requests markitdown #requests are used to send HTTP requests, markitdown used only in api_parser.py (see the Overview)
```
3. Now you can run the code

### Good luck on your programming journew - I know you can do whatever you wish!
