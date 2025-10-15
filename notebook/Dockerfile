# Base: a small Jupyter image
FROM jupyter/minimal-notebook:python-3.11

# Avoid prompts during install
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies for psycopg2 and others
USER root
RUN apt-get update && apt-get install -y --no-install-recommends     build-essential     libpq-dev     && rm -rf /var/lib/apt/lists/*

# Back to jovyan
USER ${NB_UID}

# Install Python deps
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Jupyter listens on 8888 in the container
EXPOSE 8888

# Start exactly like your command
CMD ["start-notebook.py"]