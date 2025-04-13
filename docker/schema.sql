CREATE DATABASE marketface;

CREATE TABLE "items" (
    "id" SERIAL PRIMARY KEY,
    "url" VARCHAR(255) NOT NULL,
    "title" VARCHAR(255),
    "description" VARCHAR(255),
    "priceArs" DECIMAL(10, 2),
    "priceUsd" DECIMAL(10, 2),
    "usd" BOOLEAN DEFAULT FALSE,
    "img_path" VARCHAR(255) NOT NULL,
    "deleted" BOOLEAN DEFAULT FALSE,
    "usdArsRate" DECIMAL(10, 2),
    "created" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    "updated" TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
