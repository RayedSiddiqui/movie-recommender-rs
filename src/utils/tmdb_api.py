import os
import requests
from dotenv import load_dotenv

load_dotenv()

TMDB_API_KEY = os.getenv("TMDB_API_KEY")
TMDB_BASE_URL = "https://api.themoviedb.org/3"


def get_recent_movies():
    url = f"{TMDB_BASE_URL}/movie/now_playing"
    params = {"api_key": TMDB_API_KEY, "language": "en-US", "page": 1}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json().get("results", [])
    return []


def search_movies(query):
    url = f"{TMDB_BASE_URL}/search/movie"
    params = {"api_key": TMDB_API_KEY, "language": "en-US", "query": query, "page": 1, "include_adult": False}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json().get("results", [])
    return [] 