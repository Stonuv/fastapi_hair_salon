FROM node:20-alpine AS build

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
# import.meta.env.VITE_* запекается в бандл на этапе сборки (Vite), не
# читается в рантайме — поэтому это build ARG, а не обычная переменная
# окружения контейнера. Пусто -> Sentry.init(...) в main.js вообще не
# вызывается и весь @sentry/vue выпиливается tree-shaking'ом (см.
# VITE_SENTRY_DSN в .env.example) — включить/сменить DSN значит
# пересобрать образ (`docker compose up --build -d frontend`), одного
# перезапуска контейнера недостаточно.
ARG VITE_SENTRY_DSN
ENV VITE_SENTRY_DSN=$VITE_SENTRY_DSN
RUN npm run build


FROM nginx:alpine

COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
