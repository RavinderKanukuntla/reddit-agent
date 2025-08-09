from typing import Any
import httpx
import os
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
import requests
import requests.auth
import time

# Load .env variables
load_dotenv()
# Initialize FastMCP server
mcp = FastMCP("SearchAgent")

# Reddit API credentials
CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
USERNAME = os.getenv("REDDIT_USERNAME")
PASSWORD = os.getenv("REDDIT_PASSWORD")
USER_AGENT = os.getenv("USER_AGENT", "MyRedditApp/0.1")

# Reddit API endpoints
TOKEN_URL = "https://www.reddit.com/api/v1/access_token"
SEARCH_URL_TEMPLATE = "https://oauth.reddit.com/{subreddit}/search"

# Store token and expiry
access_token = None
token_expiry = 0

def get_access_token():
    global access_token, token_expiry

    # Check if token is still valid
    if access_token and time.time() < token_expiry:
        return access_token
    
    print(f"calling access_token")
    auth = requests.auth.HTTPBasicAuth(CLIENT_ID, CLIENT_SECRET)
    data = {"grant_type": "client_credentials", "username": USERNAME, "password": PASSWORD}
    headers = {"User-Agent": "MyRedditApp/0.1"}

    # Request token
    response = requests.post(TOKEN_URL, auth=auth, data=data, headers=headers)

    if response.status_code != 200:
        raise Exception(f"Failed to get token: {response.status_code} - {response.text}")

    token_data = response.json()
    access_token = token_data['access_token']
    expires_in = token_data.get('expires_in', 3600)  # default to 1 hour
    token_expiry = time.time() + expires_in - 60  # refresh 1 min early

    return access_token

def call_api(subreddit: str, query: str) -> str:
    token = get_access_token()
    params = {'limit': 5, 'q': query}
    headers = {'Authorization': f'Bearer {token}'}
    url = SEARCH_URL_TEMPLATE.format(subreddit=subreddit)
    response = requests.get(url, headers=headers, params=params)

    try:
        if response.status_code != 200:
            return f"API call failed: {response.status_code} - {response.text[:20]} - {url} - {token}"
        else:
            final_text = []
            try:
                for post in response.json()['data']['children']:
                    try:
                        final_text.append(post['data']['selftext'])
                    except Exception as e:
                        print(f"")    
            except Exception as e:
                print(f"error: %s", e, exc_info=True)
            
            return "\n".join(final_text)         
                        
    except Exception as e:
        #logging.error("error: %s", e, exc_info=True)
        #return f"Error generating response: {e}"
        return f""

@mcp.tool()
async def reddit(channel: str, query: str) -> str:
    """Get latest 5 channel feeds for given channel.

    Args:
        channel: Reddit channel name.
    """
    #logging.info("Received reddit channel: %r", channel)
    return call_api(channel, query)
    #return channel

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport="stdio")
