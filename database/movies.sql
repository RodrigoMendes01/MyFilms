CREATE DATABASE movies;
USE movies;

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY, 
    name VARCHAR(100) NOT NULL,             
    email VARCHAR(150) NOT NULL UNIQUE,     
    password VARCHAR(255) NOT NULL           
);

CREATE TABLE movies (
	id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    commentary VARCHAR(200) DEFAULT "SEM COMENTÁRIOS",
    image VARCHAR(200) NOT NULL,
    rating TINYINT DEFAULT 1,
    recommend BOOLEAN NOT NULL,
    times_watched TINYINT NOT NULL,
    
    user_id INT NOT NULL, 
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

SELECT * FROM movies;
