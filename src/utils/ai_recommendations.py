import os
import openai
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY


def get_movie_recommendations(user_query, candidate_movies):
    """
    Given a user query (movie title or description) and a list of candidate movies (dicts with 'title' and 'overview'),
    use OpenAI to recommend the best matches.
    """
    if not candidate_movies:
        return []
    movie_list = "\n".join([f"- {m['title']}: {m.get('overview', '')}" for m in candidate_movies[:10]])
    prompt = f"""
You are a helpful movie recommender. A user is interested in movies similar to: '{user_query}'.
Here are some candidate movies:
{movie_list}

Which 3 movies from the list would you recommend and why? Respond with only the movie titles, one per line.
"""
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=100,
            temperature=0.7,
        )
        recommendations = response.choices[0].message.content.strip().split("\n")
        return [title.strip() for title in recommendations if title.strip()]
    except Exception as e:
        print(f"OpenAI error: {e}")
        return [] 