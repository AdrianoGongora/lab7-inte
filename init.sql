CREATE DATABASE MovieLens;
GO

USE MovieLens;
GO

CREATE TABLE Movies (
    MovieID INT PRIMARY KEY,
    Title NVARCHAR(255),
    Genres NVARCHAR(255)
);

CREATE TABLE Users (
    UserID INT PRIMARY KEY,
    Gender CHAR(1),
    Age INT,
    OccupationID INT,
    ZipCode NVARCHAR(10)
);

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


CREATE INDEX idx_ratings_user_movie ON Ratings(UserID, MovieID);
CREATE INDEX idx_ratings_movie ON Ratings(MovieID);
CREATE INDEX idx_ratings_timestamp ON Ratings(Timestamp);

CREATE INDEX idx_movies_title ON Movies(Title);

CREATE INDEX idx_users_occupation ON Users(OccupationID);
CREATE INDEX idx_users_zipcode ON Users(ZipCode);
GO

BULK INSERT Movies
FROM '/var/opt/mssql/app/data/movies.dat'
WITH (
    FIELDTERMINATOR = '::',
    ROWTERMINATOR = '\n',
    FIRSTROW = 1
);

BULK INSERT Users
FROM '/var/opt/mssql/app/data/users.dat'
WITH (
    FIELDTERMINATOR = '::',
    ROWTERMINATOR = '\n',
    FIRSTROW = 1
);

BULK INSERT Ratings
FROM '/var/opt/mssql/app/data/ratings.dat'
WITH (
    FIELDTERMINATOR = '::',
    ROWTERMINATOR = '\n',
    FIRSTROW = 1
);
GO
