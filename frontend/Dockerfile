FROM node:20-alpine

WORKDIR /app

# Copie des fichiers de dépendances
COPY package*.json ./

# Installation des paquets NPM
RUN npm install

# Copie du reste du projet
COPY . .

EXPOSE 5173