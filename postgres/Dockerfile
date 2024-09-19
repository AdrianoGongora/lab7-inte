FROM postgres:alpine

COPY postgres.sh /usr/local/bin/postgres-healthcheck.sh
RUN chmod +x /usr/local/bin/postgres-healthcheck.sh

HEALTHCHECK --interval=5s --timeout=3s --start-period=30s --retries=3 \
  CMD /usr/local/bin/postgres-healthcheck.sh || exit 1
