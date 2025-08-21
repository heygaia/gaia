import json
from typing import Dict, Optional

import httpx
import jwt
from fastapi import HTTPException, Request
from jwt import PyJWK

from app.config.loggers import mail_webhook_logger as logger
from app.config.settings import settings
from app.db.redis import get_cache, set_cache


class PubSubAuthenticationError(Exception):
    """Exception raised when Pub/Sub authentication fails."""

    pass


class GoogleJWTVerifier:
    """Verifies JWT tokens from Google Cloud Pub/Sub push subscriptions."""

    def __init__(self):
        self._cache_ttl = 3600  # Cache keys for 1 hour
        self._token_cache_ttl = 300  # Cache tokens for 5 minutes
        self._keys_cache_key = "google_jwt_keys"
        self._token_cache_prefix = "jwt_token:"

    async def _get_google_public_keys(self) -> Dict[str, Dict]:
        """Fetch Google's public keys and return as dictionary indexed by kid."""
        # Try to get from Redis cache first
        cached_keys = await get_cache(self._keys_cache_key)
        if cached_keys:
            logger.debug("Using cached Google public keys from Redis")
            return json.loads(cached_keys)

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://www.googleapis.com/oauth2/v3/certs", timeout=10.0
                )
                response.raise_for_status()
                keys_response = response.json()

                # Convert keys list to dictionary indexed by kid
                keys_dict = {}
                for key in keys_response.get("keys", []):
                    kid = key.get("kid")
                    if kid:
                        keys_dict[kid] = key

                # Cache in Redis
                await set_cache(
                    self._keys_cache_key, json.dumps(keys_dict), ttl=self._cache_ttl
                )

                logger.info(f"Cached {len(keys_dict)} Google public keys in Redis")
                return keys_dict

        except Exception as e:
            logger.error(f"Failed to fetch Google public keys: {e}")
            raise PubSubAuthenticationError("Cannot fetch verification keys")

    def _get_project_number_from_topic(self, topic_name: str) -> str:
        """Extract project number from topic name."""
        # Topic format: projects/{project-number}/topics/{topic-name}
        try:
            parts = topic_name.split("/")
            if len(parts) >= 2 and parts[0] == "projects":
                return parts[1]
            raise ValueError("Invalid topic format")
        except Exception:
            raise PubSubAuthenticationError("Cannot extract project number from topic")

    async def _get_cached_token(self, token: str) -> Optional[Dict]:
        """Get cached token payload if valid."""
        cache_key = f"{self._token_cache_prefix}{hash(token)}"
        cached_payload = await get_cache(cache_key)
        if cached_payload:
            logger.debug("Using cached JWT token verification from Redis")
            return json.loads(cached_payload)
        return None

    async def _cache_token(self, token: str, payload: Dict) -> None:
        """Cache token payload in Redis."""
        cache_key = f"{self._token_cache_prefix}{hash(token)}"
        await set_cache(cache_key, json.dumps(payload), ttl=self._token_cache_ttl)

    async def verify_jwt_token(self, token: str) -> Dict:
        """
        Verify a JWT token from Pub/Sub push subscription.

        Args:
            token: The JWT token from Authorization header

        Returns:
            Dict: Decoded JWT payload if valid

        Raises:
            PubSubAuthenticationError: If token is invalid
        """
        # Check cache first
        cached_payload = await self._get_cached_token(token)
        if cached_payload:
            return cached_payload

        try:
            # Get Google's public keys as dictionary
            keys_dict = await self._get_google_public_keys()

            # Decode header to get key ID
            unverified_header = jwt.get_unverified_header(token)
            key_id = unverified_header.get("kid")

            if not key_id:
                raise PubSubAuthenticationError("No key ID in JWT header")

            # Get key data directly from dictionary
            key_data = keys_dict.get(key_id)
            if not key_data:
                raise PubSubAuthenticationError("Public key not found")

            # Convert JWK to public key
            jwk = PyJWK(key_data)
            public_key = jwk.key

            # Verify and decode the token
            payload = jwt.decode(
                token,
                public_key,
                algorithms=["RS256"],
                audience=settings.HOST + "/api/v1/mail-webhook/receive",
                issuer="https://accounts.google.com",
                options={
                    "verify_signature": True,
                    "verify_aud": True,
                    "verify_iss": True,
                    "verify_exp": True,
                    "verify_iat": True,
                },
            )

            # Cache the verified token
            await self._cache_token(token, payload)

            return payload

        except jwt.ExpiredSignatureError:
            raise PubSubAuthenticationError("JWT token has expired")
        except jwt.InvalidAudienceError:
            raise PubSubAuthenticationError("Invalid audience in JWT token")
        except jwt.InvalidIssuerError:
            raise PubSubAuthenticationError("Invalid issuer in JWT token")
        except jwt.InvalidSignatureError:
            raise PubSubAuthenticationError("Invalid JWT signature")
        except jwt.InvalidTokenError as e:
            raise PubSubAuthenticationError(f"Invalid JWT token: {str(e)}")
        except Exception as e:
            logger.error(f"JWT verification error: {e}")
            raise PubSubAuthenticationError("JWT verification failed")


# Global verifier instance for caching
_jwt_verifier = GoogleJWTVerifier()


# Dependency function for FastAPI
async def get_verified_pubsub_request(request: Request) -> Dict:
    """
    FastAPI dependency to verify Pub/Sub requests.

    Args:
        request: FastAPI request object (injected by Depends)

    Returns:
        Dict: Decoded JWT payload if verification succeeds, empty dict if verification is disabled

    Raises:
        HTTPException: If verification fails when enabled
    """
    if not settings.ENABLE_PUBSUB_JWT_VERIFICATION:
        return {}

    auth_header = request.headers.get("authorization", "")
    jwt_token = auth_header.split("Bearer ")[-1].strip() if auth_header else ""

    if not jwt_token:
        logger.warning("No JWT token found in Authorization header")
        raise HTTPException(
            status_code=401, detail="Missing or invalid Authorization header"
        )

    # Verify the JWT token using global verifier instance
    try:
        return await _jwt_verifier.verify_jwt_token(jwt_token)
    except PubSubAuthenticationError as e:
        logger.error(f"Pub/Sub authentication failed: {e}")
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")
