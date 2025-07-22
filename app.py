import streamlit as st
from src.utils.tmdb_api import get_recent_movies, search_movies
from src.utils.ai_recommendations import get_movie_recommendations
from src.utils.database import add_rating, remove_rating, get_ratings
import requests
import openai
import os

st.set_page_config(page_title="Movie Recommender", layout="wide")

# Custom CSS for red and black theme, Kanit font, and centering
tmdb_img_base = "https://image.tmdb.org/t/p/w500"

st.markdown(
    """
    <link href="https://fonts.googleapis.com/css2?family=Kanit:wght@400;700&display=swap" rel="stylesheet">
    <style>
    html, body, [class*="st-"] {
        font-family: 'Kanit', sans-serif !important;
        background-color: #111;
    }
    .main {
        background-color: #111;
    }
    .stApp {
        background-color: #111;
    }
    h1, h2, h3, h4, h5, h6 {
        color: #e50914;
        text-align: center;
        font-family: 'Kanit', sans-serif !important;
    }
    .stRadio > div {
        justify-content: center;
        display: flex;
    }
    .stRadio label {
        font-family: 'Kanit', sans-serif !important;
        font-size: 1.1em;
        color: #fff;
        margin: 0 1.5em;
    }
    .movie-card {
        background: #222;
        border-radius: 12px;
        padding: 1em 1em 1.5em 1em;
        margin: 1em auto;
        box-shadow: 0 2px 8px rgba(229,9,20,0.2);
        color: #fff;
        max-width: 320px;
        font-family: 'Kanit', sans-serif !important;
        display: flex;
        flex-direction: column;
        align-items: center;
    }
    .movie-title {
        color: #e50914;
        font-size: 1.2em;
        font-weight: bold;
        text-align: center;
        margin-bottom: 0.5em;
    }
    .movie-img {
        display: block;
        margin: 0 auto 0.5em auto;
        border-radius: 8px;
        box-shadow: 0 2px 8px rgba(229,9,20,0.2);
        max-width: 200px;
        max-height: 300px;
    }
    .movie-meta {
        color: #fff;
        font-size: 0.95em;
        margin: 0.5em 0 0.5em 0;
        text-align: center;
    }
    .movie-desc {
        color: #fff;
        font-size: 0.95em;
        margin-top: 0.5em;
        text-align: center;
    }
    .recommendation-list {
        text-align: center;
        color: #fff;
        font-family: 'Kanit', sans-serif !important;
    }
    .stTextInput > div > div > input {
        background: #222;
        color: #fff;
        border: 1px solid #e50914;
        font-family: 'Kanit', sans-serif !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Helper to get runtime and certification from TMDB API
@st.cache_data(show_spinner=False)
def get_movie_details(movie_id):
    api_key = st.secrets["TMDB_API_KEY"] if "TMDB_API_KEY" in st.secrets else None
    if not api_key:
        api_key = os.getenv("TMDB_API_KEY")
    url = f"https://api.themoviedb.org/3/movie/{movie_id}"
    params = {"api_key": api_key, "language": "en-US"}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        runtime = data.get("runtime", None)
        # Get US certification if available
        cert = None
        for rel in data.get("releases", {}).get("countries", []):
            if rel.get("iso_3166_1") == "US":
                cert = rel.get("certification")
                break
        return runtime, cert
    return None, None

# Helper to summarize movie description using OpenAI
def summarize_description(desc):
    openai.api_key = os.getenv("OPENAI_API_KEY")
    if not desc or len(desc) < 30:
        return desc
    prompt = f"Summarize the following movie description in under 100 words:\n{desc}"
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=120,
            temperature=0.5,
        )
        summary = response.choices[0].message.content.strip()
        return summary
    except Exception as e:
        return desc

# Initialize session state for watchlist
if "watchlist" not in st.session_state:
    st.session_state["watchlist"] = set()

# Top navigation as a centered radio bar
menu = ["Movies & Recommendations", "Rated Movies", "About"]
choice = st.radio("Navigation", menu, horizontal=True)

st.markdown('<h1 style="color:#e50914;">Movie Recommender</h1>', unsafe_allow_html=True)

if choice == "Movies & Recommendations":
    st.markdown('<h2>Recent Movies</h2>', unsafe_allow_html=True)
    recent_movies = get_recent_movies()
    if recent_movies:
        cols = st.columns(4)
        for idx, movie in enumerate(recent_movies[:8]):
            with cols[idx % 4]:
                with st.container():
                    st.markdown(f'<div class="movie-card">', unsafe_allow_html=True)
                    st.markdown(f'<div class="movie-title">{movie["title"]}</div>', unsafe_allow_html=True)
                    poster_path = movie.get("poster_path")
                    if poster_path:
                        st.image(f"{tmdb_img_base}{poster_path}", use_container_width=True, output_format="JPEG")
                    else:
                        st.image("https://via.placeholder.com/200x300?text=No+Image", use_container_width=True)
                    # Rating with emoji
                    rating = movie.get("vote_average", 0)
                    if rating >= 8:
                        emoji = "🌟"
                    elif rating >= 6:
                        emoji = "👍"
                    elif rating > 0:
                        emoji = "👌"
                    else:
                        emoji = "❓"
                    st.markdown(f'<div class="movie-meta">Rating: {emoji} {rating:.1f}</div>', unsafe_allow_html=True)
                    # Get runtime and certification
                    runtime = movie.get("runtime")
                    cert = movie.get("certification")
                    if runtime is None or cert is None:
                        details_runtime, details_cert = None, None
                        try:
                            details_runtime, details_cert = get_movie_details(movie["id"])
                        except Exception:
                            pass
                        runtime = runtime or details_runtime
                        cert = cert or details_cert
                    meta = []
                    if runtime:
                        meta.append(f"⏱️ {runtime} min")
                    if cert:
                        meta.append(f"🔞 {cert}")
                    if meta:
                        st.markdown(f'<div class="movie-meta">{" | ".join(meta)}</div>', unsafe_allow_html=True)
                    # Summarize description
                    desc = movie.get("overview", "No description available.")
                    summary = summarize_description(desc)
                    desc_key = f"show_desc_{movie['id']}"
                    if desc_key not in st.session_state:
                        st.session_state[desc_key] = False  # Hide by default
                    # Button with same width as image
                    btn_container = st.container()
                    with btn_container:
                        st.markdown(
                            f"""
                            <style>
                            .desc-btn-{movie['id']} {{
                                width: 200px;
                                display: block;
                                margin-left: auto;
                                margin-right: auto;
                                margin-bottom: 0.5em;
                            }}
                            </style>
                            """,
                            unsafe_allow_html=True
                        )
                        if st.button(
                            "Show Description" if not st.session_state[desc_key] else "Hide Description",
                            key=f"toggle_desc_{movie['id']}",
                            help="Show or hide the movie description.",
                            args=(),
                            kwargs={},
                            type="secondary",
                        ):
                            st.session_state[desc_key] = not st.session_state[desc_key]
                        st.markdown(f'<div class="desc-btn-{movie["id"]}"></div>', unsafe_allow_html=True)
                    if st.session_state[desc_key]:
                        st.markdown(f'<div class="movie-desc">{summary}</div>', unsafe_allow_html=True)
                    # Watchlist buttons side by side
                    watchlist_col1, watchlist_col2 = st.columns(2)
                    with watchlist_col1:
                        if st.button("Add to Watchlist", key=f"watch_{movie['id']}"):
                            st.session_state["watchlist"].add(movie["id"])
                            st.success(f"Added '{movie['title']}' to your watchlist!")
                    with watchlist_col2:
                        if st.button("Remove from Watchlist", key=f"remove_{movie['id']}"):
                            st.session_state["watchlist"].remove(movie["id"])
                            st.success(f"Removed '{movie['title']}' from your watchlist!")
                    # Rating slider and buttons side by side
                    new_rating = st.slider("Rate this movie:", 1, 5, st.session_state.get(f"rating_{movie['id']}", 3), key=f"slider_{movie['id']}")
                    rating_btn_col1, rating_btn_col2 = st.columns(2)
                    with rating_btn_col1:
                        if st.button("Add/Update Rating", key=f"add_rating_{movie['id']}"):
                            add_rating(movie["id"], movie["title"], new_rating)
                            st.session_state[f"rating_{movie['id']}"] = new_rating
                            st.success(f"You rated '{movie['title']}' {new_rating}/5!")
                    with rating_btn_col2:
                        if st.button("Remove Rating", key=f"remove_rating_{movie['id']}"):
                            remove_rating(movie["id"])
                            st.session_state.pop(f"rating_{movie['id']}", None)
                            st.success(f"Removed rating for '{movie['title']}'!")
                    st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.write("No recent movies found or TMDB API key missing.")

    st.markdown('<h2>Movie Recommendations</h2>', unsafe_allow_html=True)
    # Recommendations based on best and worst rated movies
    user_ratings = get_ratings()
    if user_ratings:
        # Find best and worst rated movies
        best = max(user_ratings, key=lambda x: x['user_rating'])
        worst = min(user_ratings, key=lambda x: x['user_rating'])
        rec_query = f"I liked {best['movie_title']} and disliked {worst['movie_title']}"
        st.info(f"Recommendations are based on your ratings: Liked '{best['movie_title']}' ({best['user_rating']}/5), Disliked '{worst['movie_title']}' ({worst['user_rating']}/5)")
        # Use the best movie as the search query
        search_results = search_movies(best['movie_title'])
        if search_results:
            recommended_titles = get_movie_recommendations(rec_query, search_results)
            if recommended_titles:
                st.markdown('<div class="recommendation-list">', unsafe_allow_html=True)
                st.subheader("Recommended Movies:")
                for title in recommended_titles:
                    st.markdown(f"<div style='color:#e50914;font-weight:bold;'>{title}</div>", unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.write("No recommendations found.")
        else:
            st.write("No movies found for your ratings.")
    else:
        # Fallback to manual search
        search_query = st.text_input("Search for a movie to get recommendations:")
        if search_query:
            search_results = search_movies(search_query)
            if search_results:
                recommended_titles = get_movie_recommendations(search_query, search_results)
                if recommended_titles:
                    st.markdown('<div class="recommendation-list">', unsafe_allow_html=True)
                    st.subheader("Recommended Movies:")
                    for title in recommended_titles:
                        st.markdown(f"<div style='color:#e50914;font-weight:bold;'>{title}</div>", unsafe_allow_html=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                else:
                    st.write("No recommendations found.")
            else:
                st.write("No movies found for your search.")
        else:
            st.write("Enter a movie name to get recommendations or add movies to your watchlist.")

elif choice == "Rated Movies":
    st.markdown('<h2>Rated Movies</h2>', unsafe_allow_html=True)
    st.write("Display a list of movies you've rated here.")
    st.markdown('<h3>Your Watchlist</h3>', unsafe_allow_html=True)
    if st.session_state["watchlist"]:
        watchlist_movies = [m for m in get_recent_movies() if m["id"] in st.session_state["watchlist"]]
        cols = st.columns(4)
        for idx, movie in enumerate(watchlist_movies):
            with cols[idx % 4]:
                with st.container():
                    st.markdown(f'<div class="movie-card">', unsafe_allow_html=True)
                    st.markdown(f'<div class="movie-title">{movie["title"]}</div>', unsafe_allow_html=True)
                    poster_path = movie.get("poster_path")
                    if poster_path:
                        st.image(f"{tmdb_img_base}{poster_path}", use_container_width=True, output_format="JPEG")
                    else:
                        st.image("https://via.placeholder.com/200x300?text=No+Image", use_container_width=True)
                    desc = movie.get("overview", "No description available.")
                    summary = summarize_description(desc)
                    st.markdown(f'<div class="movie-desc">{summary}</div>', unsafe_allow_html=True)
                    # Remove from watchlist button
                    if st.button("Remove from Watchlist", key=f"remove_watchlist_{movie['id']}"):
                        st.session_state["watchlist"].remove(movie["id"])
                        st.success(f"Removed '{movie['title']}' from your watchlist!")
                    st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.write("Your watchlist is empty.")

elif choice == "About":
    st.markdown('<h2>About</h2>', unsafe_allow_html=True)
    st.markdown("""
    <div style='text-align:center;color:#fff;'>
    <b>Movie Recommender</b> helps you discover new movies, get recommendations, and keep track of your favorites.<br>
    <span style='color:#e50914;'>Powered by Streamlit, OpenAI, TMDB, and Supabase.</span>
    </div>
    """, unsafe_allow_html=True) 