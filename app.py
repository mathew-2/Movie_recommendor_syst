import pandas as pd
import streamlit as st
import pickle
import requests

movies_dict =pickle.load(open('movie_dict.pkl', 'rb'))
similarity=pickle.load(open('similarity.pkl', 'rb'))
similarity=pd.DataFrame(similarity)
movies=pd.DataFrame(movies_dict)

def fetch_poster(movie_id):
    response=requests.get('https://api.themoviedb.org/3/movie/{'
                 '}?api_key=6c72a14672ddab79e21c04cdcb4cef68&language=en-US'.format(movie_id))
    data = response.json()
    return "https://image.tmdb.org/t/p/w500"+data['poster_path']
def recommend(movie):
    movie_index_id = movies[movies['title'] == movie].index[0]
    movie_similarities = similarity[movie_index_id]

    movies_index_list = sorted(list(enumerate(movie_similarities)), reverse=True, key=lambda x: x[1])[1:6]

    recommended_movie_list=[]
    recommended_movie_posters=[]
    for movie in movies_index_list:
        # print(final_movies_df.iloc[movie[0]].title)
        recommended_movie_list.append(movies.iloc[movie[0]].title)
        recommended_movie_posters.append(fetch_poster(movies.iloc[movie[0]].movie_id))

    return recommended_movie_list,recommended_movie_posters


st.title("Movie recommendor system")


selected_movie_name=st.selectbox(
'What sort of recommendations would you like?',
movies['title'].values
)

if st.button('Recommend'):
    recommended_movie_list, recommended_movie_poster=recommend(selected_movie_name)
    st.write('movies similar to {} are:'.format(selected_movie_name))

    col1,col2,col3,col4,col5=st.columns(5)

    with col1:
        st.text(recommended_movie_list[0])
        st.image(recommended_movie_poster[0])
    with col2:
        st.text(recommended_movie_list[1])
        st.image(recommended_movie_poster[1])
    with col3:
        st.text(recommended_movie_list[2])
        st.image(recommended_movie_poster[2])
    with col4:
        st.text(recommended_movie_list[3])
        st.image(recommended_movie_poster[3])
    with col5:
        st.text(recommended_movie_list[4])
        st.image(recommended_movie_poster[4])