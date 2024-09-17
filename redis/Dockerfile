FROM redis:alpine

COPY redis.sh /usr/local/bin/redis-healthcheck.sh
RUN chmod +x /usr/local/bin/redis-healthcheck.sh

CMD ["redis-server"]

HEALTHCHECK --interval=5s --timeout=3s --start-period=30s --retries=3 \
  CMD /usr/local/bin/redis-healthcheck.sh
