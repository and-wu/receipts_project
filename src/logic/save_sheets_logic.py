import json
import os

USER_SHEETS_FILE = "user_sheets.json"


def load_user_sheets():
    try:
        with open(USER_SHEETS_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def save_user_sheets(data: dict):
    with open(USER_SHEETS_FILE, "w") as f:
        json.dump(data, f, indent=4)


USER_SHEETS = load_user_sheets()
