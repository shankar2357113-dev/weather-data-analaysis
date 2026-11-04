CREATE DATABASE IF NOT EXISTS weather_analysis
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE weather_analysis;

CREATE TABLE IF NOT EXISTS weather_records (
    record_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    observation_date DATE NOT NULL,
    location VARCHAR(100) NOT NULL,
    temperature DECIMAL(6,2) NULL COMMENT 'Degrees Celsius',
    humidity DECIMAL(5,2) NULL COMMENT 'Percent, 0 to 100',
    rainfall DECIMAL(8,2) NULL COMMENT 'Millimetres, non-negative',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_weather_date_location (observation_date, location),
    INDEX idx_weather_location (location)
);
