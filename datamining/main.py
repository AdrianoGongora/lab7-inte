from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine
import pandas as pd
from functools import lru_cache

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

server = 'mssql'
database = 'MovieLens'
username = 'sa'
password = 'mssql1Ipw'
connection_string = (
    f'mssql+pyodbc://{username}:{password}@{server}/{database}?driver=ODBC+Driver+17+for+SQL+Server'
)

engine = create_engine(connection_string)

@lru_cache(maxsize=1)
def get_ratings_and_movies():
    with engine.connect() as conn:
        query_ratings = """
            SELECT UserID, MovieID, Rating
            FROM Ratings
        """
        ratings_df = pd.read_sql(query_ratings, conn)

        query_movies = """
            SELECT MovieID, Title
            FROM Movies
        """
        movies_df = pd.read_sql(query_movies, conn)

    ratings_matrix = ratings_df.pivot_table(index='UserID', columns='MovieID', values='Rating')

    similarity_matrix = ratings_matrix.corr(method='pearson', min_periods=50)

    return ratings_matrix, similarity_matrix, movies_df

def recommend_movies(user_id: int, ratings_matrix: pd.DataFrame, similarity_matrix: pd.DataFrame, threshold=4.0):
    if user_id not in ratings_matrix.index:
        raise HTTPException(status_code=404, detail=f"User {user_id} not found in the database.")

    user_ratings = ratings_matrix.loc[user_id].dropna()
    liked_movies = user_ratings[user_ratings >= threshold].index

    recommendations = pd.Series(dtype=float)
    for movie_id in liked_movies:
        similar_movies = similarity_matrix[movie_id].dropna()
        similar_movies = similar_movies[similar_movies > 0.0]
        similar_movies = similar_movies * user_ratings[movie_id]
        recommendations = pd.concat([recommendations, similar_movies])

    recommendations = recommendations.groupby(recommendations.index).sum()

    recommendations = recommendations.drop(user_ratings.index, errors='ignore')

    return recommendations.sort_values(ascending=False)

@app.get("/recommendations/{user_id}")
def get_recommendations(user_id: int):
    ratings_matrix, similarity_matrix, movies_df = get_ratings_and_movies()

    recommendations = recommend_movies(user_id, ratings_matrix, similarity_matrix)

    recommended_movie_ids = recommendations.index
    recommended_movies = movies_df[movies_df['MovieID'].isin(recommended_movie_ids)]

    top_10_recommendations = recommended_movies.head(10)

    return top_10_recommendations.to_dict(orient="records")
