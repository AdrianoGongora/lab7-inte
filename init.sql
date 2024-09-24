-- Crear la base de datos
CREATE DATABASE MovieLens;
GO

-- Usar la base de datos
USE MovieLens;
GO

-- Crear tabla de películas
CREATE TABLE Movies (
    MovieID INT PRIMARY KEY,
    Title NVARCHAR(255),
    Genres NVARCHAR(255)
);

-- Crear tabla de usuarios
CREATE TABLE Users (
    UserID INT PRIMARY KEY,
    Gender CHAR(1),
    Age INT,
    OccupationID INT,
    ZipCode NVARCHAR(10)
);

-- Crear tabla de ratings
CREATE TABLE Ratings (
    UserID INT,
    MovieID INT,
    Rating INT,
    Timestamp BIGINT,
    PRIMARY KEY (UserID, MovieID),
    FOREIGN KEY (UserID) REFERENCES Users(UserID),
    FOREIGN KEY (MovieID) REFERENCES Movies(MovieID)
);
GO

-- Insertar datos en la tabla Movies
BULK INSERT Movies
FROM '/var/opt/mssql/app/data/movies.dat'
WITH (
    FIELDTERMINATOR = '::',
    ROWTERMINATOR = '\n',
    FIRSTROW = 1
);

-- Insertar datos en la tabla Users
BULK INSERT Users
FROM '/var/opt/mssql/app/data/users.dat'
WITH (
    FIELDTERMINATOR = '::',
    ROWTERMINATOR = '\n',
    FIRSTROW = 1
);

-- Insertar datos en la tabla Ratings
BULK INSERT Ratings
FROM '/var/opt/mssql/app/data/ratings.dat'
WITH (
    FIELDTERMINATOR = '::',
    ROWTERMINATOR = '\n',
    FIRSTROW = 1
);
GO
