import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

TABLE_NAME = "movie_ratings"

# Add or update a movie rating
def add_rating(tmdb_movie_id, movie_title, user_rating):
    # Upsert (insert or update) the rating
    data = {
        "tmdb_movie_id": tmdb_movie_id,
        "movie_title": movie_title,
        "user_rating": user_rating,
    }
    result = supabase.table(TABLE_NAME).upsert(data, on_conflict=["tmdb_movie_id"]).execute()
    return result

# Remove a movie rating (from watchlist)
def remove_rating(tmdb_movie_id):
    result = supabase.table(TABLE_NAME).delete().eq("tmdb_movie_id", tmdb_movie_id).execute()
    return result

# Get all ratings (for the user)
def get_ratings():
    result = supabase.table(TABLE_NAME).select("*").execute()
    if result.data:
        return result.data
    return []

# Get all movies in the watchlist (rated, regardless of rating)
def get_watchlist():
    # Watchlist is all movies with a rating (could filter by rating if needed)
    return get_ratings() 