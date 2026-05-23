import hashlib
import hmac
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional


class AuthServiceUnavailable(RuntimeError):
    pass


class AuthService:
    def __init__(
        self,
        host: str,
        port: int,
        user: str,
        password: str,
        database: str,
        session_days: int = 30,
    ) -> None:
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.session_days = session_days
        self._schema_ready = False

    @classmethod
    def from_env(cls) -> Optional["AuthService"]:
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
            session_days=int(os.getenv("MONTHLY_FORTUNE_SESSION_DAYS", "30")),
        )

    def signup(self, email: str, password: str) -> tuple[str, str]:
        self._ensure_schema()
        normalized_email = email.strip().casefold()
        password_hash = self._hash_password(password)
        try:
            with self._connect() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO fortune_users (email, password_hash)
                        VALUES (%s, %s)
                        """,
                        (normalized_email, password_hash),
                    )
                    user_id = cursor.lastrowid
                connection.commit()
        except Exception as exc:
            raise ValueError("이미 가입된 이메일이거나 회원가입을 처리할 수 없습니다.") from exc

        token = self._create_session(user_id)
        return token, normalized_email

    def login(self, email: str, password: str) -> tuple[str, str]:
        self._ensure_schema()
        normalized_email = email.strip().casefold()
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT id, password_hash FROM fortune_users WHERE email = %s LIMIT 1",
                    (normalized_email,),
                )
                row = cursor.fetchone()

        if not row or not self._verify_password(password, row[1]):
            raise ValueError("이메일 또는 비밀번호가 올바르지 않습니다.")

        token = self._create_session(row[0])
        return token, normalized_email

    def get_user_email(self, token: str) -> Optional[str]:
        self._ensure_schema()
        token_hash = self._hash_token(token)
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT u.email
                    FROM fortune_user_sessions s
                    JOIN fortune_users u ON u.id = s.user_id
                    WHERE s.token_hash = %s
                      AND s.expires_at > UTC_TIMESTAMP()
                    LIMIT 1
                    """,
                    (token_hash,),
                )
                row = cursor.fetchone()
        return row[0] if row else None

    def _create_session(self, user_id: int) -> str:
        token = secrets.token_urlsafe(32)
        token_hash = self._hash_token(token)
        expires_at = datetime.now(timezone.utc) + timedelta(days=self.session_days)
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO fortune_user_sessions (user_id, token_hash, expires_at)
                    VALUES (%s, %s, %s)
                    """,
                    (user_id, token_hash, expires_at.replace(tzinfo=None)),
                )
            connection.commit()
        return token

    def _hash_password(self, password: str) -> str:
        salt = secrets.token_hex(16)
        digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 120000)
        return f"pbkdf2_sha256$120000${salt}${digest.hex()}"

    def _verify_password(self, password: str, stored_hash: str) -> bool:
        try:
            algorithm, iterations, salt, expected = stored_hash.split("$", 3)
        except ValueError:
            return False
        if algorithm != "pbkdf2_sha256":
            return False
        digest = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            int(iterations),
        ).hex()
        return hmac.compare_digest(digest, expected)

    def _hash_token(self, token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    def _ensure_schema(self) -> None:
        if self._schema_ready:
            return

        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS fortune_users (
                      id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
                      email VARCHAR(255) NOT NULL,
                      password_hash VARCHAR(255) NOT NULL,
                      created_at DATETIME NOT NULL DEFAULT UTC_TIMESTAMP(),
                      updated_at DATETIME NOT NULL DEFAULT UTC_TIMESTAMP()
                        ON UPDATE UTC_TIMESTAMP(),
                      UNIQUE KEY uq_fortune_users_email (email)
                    ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
                    """
                )
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS fortune_user_sessions (
                      id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
                      user_id BIGINT UNSIGNED NOT NULL,
                      token_hash CHAR(64) NOT NULL,
                      expires_at DATETIME NOT NULL,
                      created_at DATETIME NOT NULL DEFAULT UTC_TIMESTAMP(),
                      UNIQUE KEY uq_fortune_user_sessions_token (token_hash),
                      KEY idx_fortune_user_sessions_user_id (user_id),
                      KEY idx_fortune_user_sessions_expires_at (expires_at),
                      CONSTRAINT fk_fortune_user_sessions_user
                        FOREIGN KEY (user_id) REFERENCES fortune_users(id)
                        ON DELETE CASCADE
                    ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
                    """
                )
            connection.commit()
        self._schema_ready = True

    def _connect(self):
        import pymysql

        try:
            return pymysql.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database,
                charset="utf8mb4",
                autocommit=False,
            )
        except Exception as exc:
            raise AuthServiceUnavailable("회원 기능을 사용하려면 MariaDB 설정이 필요합니다.") from exc
