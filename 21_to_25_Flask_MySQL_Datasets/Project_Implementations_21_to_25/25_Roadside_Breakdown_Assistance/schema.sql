CREATE DATABASE IF NOT EXISTS 25roadsidebreakdownassistance;
USE 25roadsidebreakdownassistance;
CREATE TABLE IF NOT EXISTS users (
 id INT AUTO_INCREMENT PRIMARY KEY,
 name VARCHAR(120) NOT NULL,
 email VARCHAR(190) NOT NULL UNIQUE,
 role ENUM('admin','director','user','driver','hospital','mechanic') NOT NULL,
 password_hash VARCHAR(255) NOT NULL,
 status VARCHAR(30) DEFAULT 'active',
 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS records (
 id INT AUTO_INCREMENT PRIMARY KEY,
 record_type VARCHAR(60) NOT NULL,
 title VARCHAR(190) NOT NULL,
 category VARCHAR(100),
 location VARCHAR(190),
 description TEXT,
 contact VARCHAR(100),
 owner_email VARCHAR(190),
 status VARCHAR(50) DEFAULT 'active',
 extra_json JSON NULL,
 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS applications (
 id INT AUTO_INCREMENT PRIMARY KEY,
 vacancy_id INT NOT NULL,
 applicant_email VARCHAR(190) NOT NULL,
 resume_filename VARCHAR(255),
 status VARCHAR(40) DEFAULT 'Applied',
 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
 UNIQUE KEY uq_application (vacancy_id, applicant_email)
);
CREATE TABLE IF NOT EXISTS saved_items (
 id INT AUTO_INCREMENT PRIMARY KEY,
 user_email VARCHAR(190) NOT NULL,
 record_id INT NOT NULL,
 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
 UNIQUE KEY uq_saved (user_email, record_id)
);
