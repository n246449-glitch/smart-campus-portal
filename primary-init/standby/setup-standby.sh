#!/bin/sh
set -e

echo "Waiting for Primary server..."

until pg_isready -h postgres_primary -p 5432 -U replicator; do
    sleep 2
done

echo "Primary server is ready"

if [ ! -s "$PGDATA/PG_VERSION" ]; then

    echo "Creating standby backup..."

    rm -rf "$PGDATA"/*

    export PGPASSWORD=replpass

    gosu postgres pg_basebackup \
        -h postgres_primary \
        -p 5432 \
        -D "$PGDATA" \
        -U replicator \
        -Fp -Xs -P -R

    chmod 700 "$PGDATA"

    echo "Backup completed"

fi

echo "Starting PostgreSQL Standby..."

exec docker-entrypoint.sh postgres -c hot_standby=on