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

# nginx:alpine уже включает непривилегированного пользователя nginx
# (uid/gid 101) — отдаём ему то, во что процесс реально пишет в рантайме
# (кэш, pid-файл); статику из /usr/share/nginx/html только читает, владение
# там менять не нужно. `user nginx;` в базовом /etc/nginx/nginx.conf (не
# наш файл, часть образа) при старте не от root просто игнорируется nginx'ом
# с safe-варнингом в лог — на поведение не влияет.
RUN chown -R nginx:nginx /var/cache/nginx /run

USER nginx

EXPOSE 8080
