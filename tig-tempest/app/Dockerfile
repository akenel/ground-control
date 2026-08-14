FROM python:3.12-slim
WORKDIR /app

# Build context is tig-tempest/ (see docker-compose.yml) so we can reach both
# app/ and its sibling game/.
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ .
# The game is served as static files; bake it in so the image runs standalone.
# In dev, docker-compose bind-mounts ./game over this for live edits.
COPY game/ /srv/game/
ENV GAME_DIR=/srv/game

EXPOSE 8000
CMD ["sh", "entrypoint.sh"]
