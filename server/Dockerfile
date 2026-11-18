# Build tu thu muc goc du an:  docker build -f server/Dockerfile -t shk-server .
# Chay:                        docker run -p 8788:8788 shk-server
FROM node:22-alpine
WORKDIR /app
COPY server/package.json server/package-lock.json ./server/
RUN cd server && npm ci --omit=dev
COPY server/ ./server/
COPY data/game_species_all.json data/shk_data.json data/server_names.json ./data/
COPY game/son-hai-kinh-phieu-luu-ky.html ./game/
EXPOSE 8788
ENV PORT=8788
CMD ["node", "server/server.js"]
