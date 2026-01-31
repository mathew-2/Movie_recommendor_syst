import os
import pickle
import requests
import numpy as np
import pandas as pd
import streamlit as st
import gdown
from concurrent.futures import ThreadPoolExecutor

# --- configuration ---
GDRIVE_FILE_ID = "1Y_-xU5ore3bCk-vHbLBmbzJ1fFOvVsza"  # file id for similarity.pkl
GDRIVE_URL = f"https://drive.google.com/uc?id={GDRIVE_FILE_ID}"
SIMILARITY_LOCAL = "similarity.pkl"
MOVIE_DICT_LOCAL = "movie_dict.pkl"
TMDB_API_KEY = "6c72a14672ddab79e21c04cdcb4cef68"
TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/w500"

# --- helpers and cached loaders ---
@st.cache_data
def ensure_file(local_path: str, gdrive_url: str):
    if not os.path.exists(local_path):
        gdown.download(gdrive_url, local_path, quiet=True)
    return local_path

@st.cache_data
def load_similarity(local_path: str):
    # load and return as numpy array for faster numeric ops
    with open(local_path, "rb") as f:
        sim = pickle.load(f)
    return np.array(sim)

@st.cache_data
def load_movies(local_path: str):
    # movie_dict.pkl should be present in the repo
    with open(local_path, "rb") as f:
        movies_dict = pickle.load(f)
    return pd.DataFrame(movies_dict)

@st.cache_data
def fetch_poster_cached(movie_id: int):
    try:
        url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={TMDB_API_KEY}&language=en-US"
        resp = requests.get(url, timeout=5)
        if resp.ok:
            data = resp.json()
            poster_path = data.get("poster_path")
            if poster_path:
                return TMDB_IMAGE_BASE + poster_path
    except Exception:
        pass
    return None

# --- recommendation logic (efficient) ---
def recommend(movie_title: str, k: int = 5):
    # find index of the movie title
    try:
        movie_idx = int(movies[movies["title"] == movie_title].index[0])
    except Exception:
        return [], []

    sims = similarity[:, movie_idx]  # numpy 1D array of similarities

    # fast top-(k+1) selection (includes the movie itself)
    topk = np.argpartition(-sims, k + 1)[: (k + 1)]
    topk = topk[np.argsort(-sims[topk])]

    # remove the movie itself and take top k
    topk = [int(i) for i in topk if int(i) != movie_idx][:k]

    titles = movies.iloc[topk]["title"].tolist()
    movie_ids = movies.iloc[topk]["movie_id"].tolist()

    # fetch posters in parallel
    with ThreadPoolExecutor(max_workers=5) as ex:
        posters = list(ex.map(fetch_poster_cached, movie_ids))

    return titles, posters

# --- app startup ---
sure_file(SIMILARITY_LOCAL, GDRIVE_URL)
similarity = load_similarity(SIMILARITY_LOCAL)  # numpy array cached
movies = load_movies(MOVIE_DICT_LOCAL)          # cached DataFrame

# fallback if similarity is 2D list or DataFrame
if isinstance(similarity, list):
    similarity = np.array(similarity)

# --- Streamlit UI ---
st.title("Movie recommendor system")

# If the movie list is large, consider replacing selectbox with text_input + fuzzy search.
selected_movie_name = st.selectbox(
    'What sort of recommendations would you like?',
    movies['title'].values
)

if st.button('Recommend'):
    with st.spinner('Finding recommendations...'):
        recommended_movie_list, recommended_movie_posters = recommend(selected_movie_name)

    st.write(f'movies similar to {selected_movie_name} are:')

    # render results
    cols = st.columns(5)
    for i, col in enumerate(cols):
        if i < len(recommended_movie_list):
            title = recommended_movie_list[i]
            poster = recommended_movie_posters[i]
            with col:
                st.text(title)
                if poster:
                    st.image(poster)
                else:
                    st.text('No poster available')