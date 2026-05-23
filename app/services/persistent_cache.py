import json
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Optional


class PersistentCache:
    def __init__(
        self,
        host: str,
        port: int,
        user: str,
        password: str,
        database: str,
        ttl_days: int = 365,
    ) -> None:
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.ttl_days = ttl_days
        self._schema_ready = False

    @classmethod
    def from_env(cls) -> Optional["PersistentCache"]:
        host = os.getenv("MONTHLY_FORTUNE_MARIADB_HOST")
        user = os.getenv("MONTHLY_FORTUNE_MARIADB_USER")
        password = os.getenv("MONTHLY_FORTUNE_MARIADB_PASSWORD")
        database = os.getenv("MONTHLY_FORTUNE_MARIADB_DATABASE")

        if not all([host, user, password, database]):
            return None

        return cls(
            host=host,
            port=int(os.getenv("MONTHLY_FORTUNE_MARIADB_PORT", "3306")),
            user=user,
            password=password,
            database=database,
            ttl_days=int(os.getenv("MONTHLY_FORTUNE_CACHE_TTL_DAYS", "365")),
        )

    def get(self, namespace: str, cache_key: str) -> Optional[dict[str, Any]]:
        try:
            self._ensure_schema()
            with self._connect() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT payload_json
                        FROM fortune_result_cache
                        WHERE namespace = %s
                          AND cache_key = %s
                          AND expires_at > UTC_TIMESTAMP()
                        LIMIT 1
                        """,
                        (namespace, cache_key),
                    )
                    row = cursor.fetchone()
        except Exception:
            return None

        if not row:
            return None

        try:
            return json.loads(row[0])
        except (TypeError, json.JSONDecodeError):
            return None

    def set(self, namespace: str, cache_key: str, payload: dict[str, Any]) -> None:
        expires_at = datetime.now(timezone.utc) + timedelta(days=self.ttl_days)
        payload_json = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
        try:
            self._ensure_schema()
            with self._connect() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO fortune_result_cache
                          (namespace, cache_key, payload_json, expires_at)
                        VALUES (%s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE
                          payload_json = VALUES(payload_json),
                          expires_at = VALUES(expires_at),
                          updated_at = UTC_TIMESTAMP()
                        """,
                        (namespace, cache_key, payload_json, expires_at.replace(tzinfo=None)),
                    )
                connection.commit()
        except Exception:
            return

    def _ensure_schema(self) -> None:
        if self._schema_ready:
            return

        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS fortune_result_cache (
                      id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
                      namespace VARCHAR(80) NOT NULL,
                      cache_key VARCHAR(512) NOT NULL,
                      payload_json LONGTEXT NOT NULL,
                      expires_at DATETIME NOT NULL,
                      created_at DATETIME NOT NULL DEFAULT UTC_TIMESTAMP(),
                      updated_at DATETIME NOT NULL DEFAULT UTC_TIMESTAMP()
                        ON UPDATE UTC_TIMESTAMP(),
                      UNIQUE KEY uq_fortune_result_cache (namespace, cache_key),
                      KEY idx_fortune_result_cache_expires_at (expires_at)
                    ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
                    """
                )
            connection.commit()
        self._schema_ready = True

    def _connect(self):
        import pymysql

        return pymysql.connect(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            database=self.database,
            charset="utf8mb4",
            autocommit=False,
        )
