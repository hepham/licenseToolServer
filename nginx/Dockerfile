FROM nginx:alpine

# Remove default nginx config
RUN rm /etc/nginx/conf.d/default.conf

# Copy both configs - use SSL if certificates exist
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY nginx.ssl.conf /etc/nginx/conf.d/ssl.conf.template

# Startup script to check for SSL certs
RUN echo '#!/bin/sh' > /docker-entrypoint.d/10-check-ssl.sh && \
    echo 'if [ -f /etc/letsencrypt/live/hehetool.site/fullchain.pem ]; then' >> /docker-entrypoint.d/10-check-ssl.sh && \
    echo '  cp /etc/nginx/conf.d/ssl.conf.template /etc/nginx/conf.d/ssl.conf' >> /docker-entrypoint.d/10-check-ssl.sh && \
    echo '  echo "SSL config enabled"' >> /docker-entrypoint.d/10-check-ssl.sh && \
    echo 'fi' >> /docker-entrypoint.d/10-check-ssl.sh && \
    chmod +x /docker-entrypoint.d/10-check-ssl.sh

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost/health || exit 1

EXPOSE 80 443

CMD ["nginx", "-g", "daemon off;"]
