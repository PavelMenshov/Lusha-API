import json
import sys
from pathlib import Path
from typing import Iterable, List, Optional, Set, Tuple
import requests
from markitdown import MarkItDown

API_HOST = "https://api.lusha.com"
SEARCH_ENDPOINT = f"{API_HOST}/prospecting/contact/search"
ENRICH_ENDPOINT = f"{API_HOST}/prospecting/contact/enrich"
API_KEY = "" 
PARSE_HISTORY_FILE = Path("parse_history.json")
DATA_FILE = Path("data.json")
PARSED_CONTACTS_JSON = Path("parsed_contacts.json")
PARSED_CONTACTS_MD = Path("parsed_contacts.md")
MAX_PAGES = 2 #don't make too big 
PAGE_SIZE = 50


def ensure_file(path: Path, default_content: str) -> None:
    """Ensure a file exists with default content if missing."""
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(default_content, encoding="utf-8")

def load_api_key() -> str:
    api_key = str(API_KEY)
    if not api_key:
        raise RuntimeError(
            f"Missing API key. Set the `{API_KEY}` environment variable or update FALLBACK_API_KEY."
        )
    return api_key


def load_parse_history() -> Set[str]:
    if not PARSE_HISTORY_FILE.exists():
        ensure_file(PARSE_HISTORY_FILE, "[]")
        return set()

    try:
        with PARSE_HISTORY_FILE.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        if isinstance(data, list):
            return {item for item in data if isinstance(item, str)}
    except json.JSONDecodeError:
        print("Warning: parse_history.json is corrupt; starting fresh.")
    return set()


def save_parse_history(history: Set[str]) -> None:
    with PARSE_HISTORY_FILE.open("w", encoding="utf-8") as handle:
        json.dump(sorted(history), handle, indent=2)


def run_contact_search(session: requests.Session, headers: dict, page: int) -> dict:
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

    response = session.post(SEARCH_ENDPOINT, json=payload, headers=headers, timeout=20)
    response.raise_for_status()
    data = response.json()

    with DATA_FILE.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2)

    return data


def extract_identifiers(search_result: dict) -> Tuple[str, List[str]]:
    request_id: Optional[str] = search_result.get("requestId")

    contact_ids: List[str] = []
    data_section = search_result.get("data")
    if isinstance(data_section, list):
        found_any = False
        for entry in data_section:
            if not isinstance(entry, dict):
                continue
            candidate = entry.get("contactId")
            if isinstance(candidate, str) and candidate.strip():
                contact_ids.append(candidate.strip())
                found_any = True
        if not found_any:
            print("No contactId found in data section")
    else:
        print("Data section missing or not a list")
    print(contact_ids)

    if not request_id:
        raise ValueError("Could not locate requestId in the search response.")
    if not contact_ids:
        raise ValueError("Could not locate any contact IDs in the search response.")

    return request_id, contact_ids


def run_contact_enrich(
    session: requests.Session, headers: dict, request_id: str, contact_ids: List[str]
) -> dict:
    payload = {
        "requestId": request_id,
        "contactIds": contact_ids,
        "revealEmails": True,
        "revealPhones": True,
    }

    response = session.post(ENRICH_ENDPOINT, json=payload, headers=headers, timeout=20)
    response.raise_for_status()
    data = response.json()

    with PARSED_CONTACTS_JSON.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2)

    return data


def main() -> None:
    api_key = load_api_key()
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "api_key": api_key,
    }

    ensure_file(DATA_FILE, "[]")
    ensure_file(PARSED_CONTACTS_JSON, "{}")
    ensure_file(PARSED_CONTACTS_MD, "# Parsed Contacts\n\n_No data yet._\n")
    parse_history = load_parse_history()

    session = requests.Session()

    try:
        page = 0
        total_processed = 0
        while page < MAX_PAGES:
            print(f"Fetching page {page}...")
            search_result = run_contact_search(session, headers, page)

            data_section = search_result.get("data")
            if not data_section:
                print("No more results; stopping pagination.")
                break

            request_id, contact_ids = extract_identifiers(search_result)
            new_contact_ids = [cid for cid in contact_ids if cid not in parse_history]

            if not new_contact_ids:
                print("All contact IDs on this page already processed; skipping enrich.")
            else:
                print(
                    f"Processing {len(new_contact_ids)} new contact IDs (page {page})."
                )
                enrich_result = run_contact_enrich(
                    session, headers, request_id, new_contact_ids
                )
                total_processed += len(new_contact_ids)
                parse_history.update(new_contact_ids)
                save_parse_history(parse_history)
                print(
                    f"Enrich call returned {len(enrich_result.get('contacts', []))} contacts."
                )

            if isinstance(data_section, list) and len(data_section) < PAGE_SIZE:
                print("Fewer results than page size; likely end of data.")
                break

            page += 1

        print(f"Finished pagination. Total new contacts processed: {total_processed}")
    except requests.HTTPError as http_err:
        print(f"HTTP error {http_err.response.status_code}: {http_err.response.text}", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:
        print(f"Failed: {exc}", file=sys.stderr)
        sys.exit(1)
    finally:
        session.close()

    md = MarkItDown(enable_plugins=False)
    result = md.convert(str(PARSED_CONTACTS_JSON))
    PARSED_CONTACTS_MD.write_text(str(result), encoding="utf-8")
    print(f"Saved Markdown summary to {PARSED_CONTACTS_MD.resolve()}")


if __name__ == "__main__":
    main()