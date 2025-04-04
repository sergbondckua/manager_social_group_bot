FROM nginx:alpine
LABEL authors="sergbondckua"
LABEL description="Nginx container"

# Видалення конфігурації за замовчуванням
RUN rm /etc/nginx/conf.d/default.conf

# Копіювання конфігурацій
COPY nginx.conf /etc/nginx/conf.d
COPY proxy_params /etc/nginx