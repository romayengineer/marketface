CREATE DATABASE marketface;

CREATE TABLE "items" (
    "created" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    "deleted" BOOLEAN DEFAULT FALSE,
    "description" VARCHAR(255),
    "id" SERIAL PRIMARY KEY,
    "img_path" VARCHAR(255) NOT NULL,
    "priceArs" DECIMAL(10, 2),
    "priceUsd" DECIMAL(10, 2),
    "title" VARCHAR(255),
    "updated" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    "url" VARCHAR(255) NOT NULL,
    "usd" BOOLEAN DEFAULT FALSE,
    "usdArsRate" DECIMAL(10, 2)
)
