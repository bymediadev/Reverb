import requests
import base64


CLIENT_ID = "fc7aceda6bcb46349e6bf8f87738925a"
CLIENT_SECRET = "286be0b936194a578836ca5e65c6b449"


TARGET_CATEGORY_IDS = {
    "Business": "business",
    "Comedy": "comedy",
    "True Crime": "truecrime",
    "News & Politics": "news",
    "Sports": "sports"
}

def get_token(client_id, client_secret):
    auth_str = f"{client_id}:{client_secret}"
    b64_auth_str = base64.b64encode(auth_str.encode()).decode()
    headers = {"Authorization": f"Basic {b64_auth_str}"}
    data = {"grant_type": "client_credentials"}
    response = requests.post("https://accounts.spotify.com/api/token", headers=headers, data=data)
    response.raise_for_status()
    return response.json()["access_token"]

def list_all_categories(token):
    url = "https://api.spotify.com/v1/browse/categories?limit=50"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    categories = response.json()["categories"]["items"]
    print("\nAvailable Spotify Categories:\n")
    for cat in categories:
        print(f"- {cat['name']} (ID: {cat['id']})")

def get_category_shows(category_id, token, limit=50, offset=0):
    url = f"https://api.spotify.com/v1/browse/categories/{category_id}/shows?limit={limit}&offset={offset}"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()["shows"]["items"]

if __name__ == "__main__":
    token = get_token(CLIENT_ID, CLIENT_SECRET)

    # Optional: Show all available Spotify categories
    list_all_categories(token)

    for category_name, category_id in TARGET_CATEGORY_IDS.items():
        print(f"\n🎧 {category_name} (ID: {category_id}):")

        try:
            shows_page_1 = get_category_shows(category_id, token, limit=50, offset=0)
            shows_page_2 = get_category_shows(category_id, token, limit=50, offset=50)
            all_shows = shows_page_1 + shows_page_2

            for show in all_shows:
                print(f"- {show['name']} (Show ID: {show['id']})")
        except requests.exceptions.RequestException as e:
            print(f"⚠️ Failed to fetch shows for {category_name}: {e}")
