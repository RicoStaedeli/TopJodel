# TopJodel - Advanced Databases Project

This is a minimal social media backend project for a database class. It spins up PostgreSQL, MongoDB and Neo4j as docker containers.

## Prerequisites

- Docker and Docker Compose installed

## Quick start
[TopJodel](https://github.com/RicoStaedeli/TopJodel)
1. Clone or download the project from Github https://github.com/RicoStaedeli/TopJodel --> Unzip the project if need
2. Start Docker Desktop
3. In the project directory:
   4. docker compose build 
   5. docker compose up -d
4. Open [01_SQL.ipynb](01_SQL.ipynb) --> Run the cells step by step
5. Open [02_MongoDB.ipynb](02_MongoDB.ipynb) --> Run the cells step by step
6. Open [03_Neo4j.ipynb](03_Neo4j.ipynb) --> Run the cells step by step
7. When done, stop the containers:
  docker compose down

## Build and run
```bash
  docker compose up -d
```

To stop and remove containers:
```bash
docker compose down
```

## Services

- PostgreSQL - localhost:55432 - db: `socialdb`, user: `app`, password: `app_pw1234`
- MongoDB - localhost:27017 - root user: `app`, password: `app_pw1234`
- Neo4j - Browser http UI at http://localhost:7474 - Bolt at bolt://localhost:7687 - user: `neo4j`, password: `app_pw1234`

