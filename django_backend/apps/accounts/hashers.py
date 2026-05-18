"""Password hashers used during the Laravel to Django migration."""
from __future__ import annotations

from django.contrib.auth.hashers import BasePasswordHasher, mask_hash
from django.utils.crypto import constant_time_compare


class LaravelBcryptPasswordHasher(BasePasswordHasher):
    """Verify Laravel bcrypt hashes such as `$2y$...`.

    Laravel stores raw bcrypt hashes without Django's `algorithm$salt$hash`
    wrapper. This hasher is intentionally verify-only; successful logins are
    rehashed by Django's default hasher automatically.
    """

    algorithm = "laravel_bcrypt"
    library = ("bcrypt", "bcrypt")

    def salt(self):
        raise NotImplementedError("Laravel bcrypt hashes are imported, not generated")

    def encode(self, password, salt):
        raise NotImplementedError("Use Django's default hasher for new passwords")

    def identify(self, encoded):
        return isinstance(encoded, str) and encoded.startswith(("$2y$", "$2a$", "$2b$"))

    def verify(self, password, encoded):
        bcrypt = self._load_library()
        normalized = encoded.replace("$2y$", "$2b$", 1)
        candidate = password.encode()
        try:
            return constant_time_compare(
                bcrypt.hashpw(candidate, normalized.encode()).decode(),
                normalized,
            )
        except ValueError:
            return False

    def safe_summary(self, encoded):
        return {
            "algorithm": self.algorithm,
            "work factor": encoded.split("$")[2] if "$" in encoded else "unknown",
            "checksum": mask_hash(encoded),
        }

    def harden_runtime(self, password, encoded):
        return None
