from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
from sqlalchemy import create_engine

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permitir solicitudes desde cualquier origen, puedes restringirlo a dominios específicos
    allow_credentials=True,
    allow_methods=["*"],  # Permitir todos los métodos (GET, POST, etc.)
    allow_headers=["*"],  # Permitir todas las cabeceras
)

server = 'mssql'
database = 'MovieLens'
username = 'sa'
password = 'mssql1Ipw'
connection_string = (
    f'mssql+pyodbc://{username}:{password}@{server}/{database}?driver=ODBC+Driver+17+for+SQL+Server'
)

# Crear el motor de SQLAlchemy
engine = create_engine(connection_string)

def get_ratings_and_movies():
    # Conexión a la base de datos con SQLAlchemy
    with engine.connect() as conn:
        # Cargar los ratings de los usuarios
        query_ratings = """
            SELECT UserID, MovieID, Rating
            FROM Ratings
        """
        ratings_df = pd.read_sql(query_ratings, conn)

        # Cargar los títulos de las películas
        query_movies = """
            SELECT MovieID, Title
            FROM Movies
        """
        movies_df = pd.read_sql(query_movies, conn)

    # Crear la matriz de ratings
    ratings_matrix = ratings_df.pivot_table(index='UserID', columns='MovieID', values='Rating')

    # Crear la matriz de similitud entre películas
    similarity_matrix = ratings_matrix.corr(method='pearson', min_periods=50)

    return ratings_matrix, similarity_matrix, movies_df

def recommend_movies(user_id: int, ratings_matrix: pd.DataFrame, similarity_matrix: pd.DataFrame, threshold=4.0):
    # Verificar si el usuario existe en la matriz
    if user_id not in ratings_matrix.index:
        raise HTTPException(status_code=404, detail=f"User {user_id} not found in the database.")

    user_ratings = ratings_matrix.loc[user_id].dropna()

    liked_movies = user_ratings[user_ratings >= threshold].index

    recommendations = pd.Series(dtype=float)  # Asegurarse de que sea float
    for movie_id in liked_movies:
        similar_movies = similarity_matrix[movie_id].dropna()
        similar_movies = similar_movies[similar_movies > 0.0]
        similar_movies = similar_movies * user_ratings[movie_id]
        
        recommendations = pd.concat([recommendations, similar_movies])

    recommendations = recommendations.groupby(recommendations.index).sum()

    # Remover películas ya vistas
    recommendations = recommendations.drop(user_ratings.index, errors='ignore')

    return recommendations.sort_values(ascending=False)


# Endpoint para obtener recomendaciones
@app.get("/recommendations/{user_id}")
def get_recommendations(user_id: int):
    # Cargar los datos
    ratings_matrix, similarity_matrix, movies_df = get_ratings_and_movies()

    # Obtener recomendaciones
    recommendations = recommend_movies(user_id, ratings_matrix, similarity_matrix)

    # Filtrar las películas recomendadas por ID
    recommended_movie_ids = recommendations.index
    recommended_movies = movies_df[movies_df['MovieID'].isin(recommended_movie_ids)]

    # Limitar a las 10 primeras películas
    top_10_recommendations = recommended_movies.head(10)

    # Retornar las recomendaciones
    return top_10_recommendations.to_dict(orient="records")
