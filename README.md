# Mini Social - Multi database project

This is a minimal social media backend project for a database class. It spins up PostgreSQL, MongoDB, Neo4j, and a Jupyter Notebook so you can create schemas, run queries, and explore.

## Prerequisites

- Docker and Docker Compose installed

## Quick start

```bash
# 1. Unzip the project
# 2. In the project directory:
docker compose build
docker compose up -d

# 3. Open Jupyter in your browser
#    Token: devtoken
#    URL: http://localhost:8888
#    Open the notebook: 00_connect_and_setup.ipynb
```

To stop and remove containers:
```bash
docker compose down
```

## Services

- PostgreSQL - localhost:5432 - db: `socialdb`, user: `app`, password: `app_pw`
- MongoDB - localhost:27017 - root user: `app`, password: `app_pw`
- Neo4j - Browser http UI at http://localhost:7474 - Bolt at bolt://localhost:7687 - user: `neo4j`, password: `app_pw`
- Jupyter Notebook - http://localhost:8888 - token: `devtoken`

## What you will do in the notebook

- PostgreSQL: Create `users` and `posts` tables, run basic queries.
- MongoDB: Create a `comments` collection, insert and query documents.
- Neo4j: Create graph constraints, `FOLLOWS` and `LIKES` relationships, run Cypher queries.
- Show simple cross-database workflows for this minimal social model.

All DBs start empty so you can follow along and create everything step by step.
