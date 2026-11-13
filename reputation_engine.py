"""IP reputation scoring engine with multi-source threat intelligence."""

import logging
import time
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Optional, List

import requests

from config import Config

logger = logging.getLogger(__name__)


class ReputationScore:
    """IP reputation score with multiple threat intelligence sources."""

    def __init__(self, ip: str):
        self.ip = ip
        self.scores: Dict[str, int] = {}
        self.sources_checked: List[str] = []
        self.final_score = 0
        self.last_updated: Optional[datetime] = None
        self.is_blocklisted = False

    def add_score(self, source: str, score: int, is_blocklisted: bool = False) -> None:
        """Add score from a threat intelligence source."""
        if 0 <= score <= 100:
            self.scores[source] = score
            if is_blocklisted:
                self.is_blocklisted = True
        self.sources_checked.append(source)

    def calculate_score(self) -> int:
        """Calculate weighted average reputation score."""
        if not self.scores:
            return 0

        # Default weights for known sources
        weights = {
            'abuseipdb': 0.4,
            'virustotal': 0.3,
            'alienvault': 0.3,
        }

        total_weight = 0
        weighted_sum = 0

        for source, score in self.scores.items():
            weight = weights.get(source, 0.1)
            weighted_sum += score * weight
            total_weight += weight

        if total_weight > 0:
            self.final_score = int(weighted_sum / total_weight)
        else:
            self.final_score = 0

        self.last_updated = datetime.utcnow()
        return self.final_score

    def should_block(self, threshold: int = 75) -> bool:
        """Determine if IP should be blocked based on reputation."""
        return self.final_score >= threshold or self.is_blocklisted

    def to_dict(self) -> Dict:
        """Convert reputation score to dictionary."""
        return {
            'ip': self.ip,
            'final_score': self.final_score,
            'scores': self.scores,
            'sources_checked': self.sources_checked,
            'is_blocklisted': self.is_blocklisted,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None,
        }


class ReputationEngine:
    """Multi-source reputation scoring engine."""

    def __init__(self, cache_ttl: int = 3600):
        self.cache = SimpleCache(ttl=cache_ttl)
        self.abuseipdb_key = Config.ABUSEIPDB_API_KEY

    def check_reputation(self, ip: str, use_cache: bool = True) -> ReputationScore:
        """Check IP reputation across multiple sources."""
        # Check cache first
        if use_cache:
            cached = self.cache.get(ip)
            if cached:
                logger.debug(f"Using cached reputation for {ip}")
                return cached

        reputation = ReputationScore(ip)

        # Check AbuseIPDB
        if self.abuseipdb_key:
            try:
                self._check_abuseipdb(ip, reputation)
            except Exception as e:
                logger.error(f"AbuseIPDB check failed for {ip}: {e}")

        # Calculate final score
        reputation.calculate_score()

        # Cache result
        self.cache.set(ip, reputation)

        logger.info(
            f"Reputation score for {ip}: {reputation.final_score} "
            f"(blocklisted: {reputation.is_blocklisted})"
        )

        return reputation

    def _check_abuseipdb(self, ip: str, reputation: ReputationScore) -> None:
        """Check AbuseIPDB for IP reputation."""
        url = "https://api.abuseipdb.com/api/v2/check"
        headers = {
            "Key": self.abuseipdb_key,
            "Accept": "application/json",
        }
        params = {
            "ipAddress": ip,
            "maxAgeInDays": 90,
            "verbose": "",
        }

        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()

        if data.get("data"):
            abuse_data = data["data"]
            confidence_score = abuse_data.get("abuseConfidenceScore", 0)
            is_whitelisted = abuse_data.get("isWhitelisted", False)
            is_blacklisted = abuse_data.get("isBlacklisted", False)

            reputation.add_score(
                "abuseipdb",
                confidence_score,
                is_blocklisted=is_blacklisted and not is_whitelisted,
            )

            logger.debug(
                f"AbuseIPDB: {ip} confidence={confidence_score}, "
                f"blacklisted={is_blacklisted}, whitelisted={is_whitelisted}"
            )

    def batch_check(self, ips: List[str]) -> Dict[str, ReputationScore]:
        """Check reputation for multiple IPs."""
        results = {}
        for ip in ips:
            try:
                results[ip] = self.check_reputation(ip)
            except Exception as e:
                logger.error(f"Failed to check reputation for {ip}: {e}")
        return results

    def get_blocklist_candidates(
        self,
        ips: List[str],
        threshold: int = 75,
    ) -> List[str]:
        """Get list of IPs that should be blocked."""
        candidates = []
        for ip in ips:
            try:
                reputation = self.check_reputation(ip)
                if reputation.should_block(threshold):
                    candidates.append(ip)
                    logger.info(f"Flagged for blocking: {ip} (score: {reputation.final_score})")
            except Exception as e:
                logger.error(f"Error checking {ip}: {e}")
        return candidates


class SimpleCache:
    """Simple in-memory cache with TTL support."""

    def __init__(self, ttl: int = 3600):
        self.ttl = ttl
        self.cache: Dict[str, tuple] = {}

    def set(self, key: str, value) -> None:
        """Set cache value with timestamp."""
        self.cache[key] = (value, time.time())

    def get(self, key: str):
        """Get cache value if not expired."""
        if key not in self.cache:
            return None

        value, timestamp = self.cache[key]
        if time.time() - timestamp > self.ttl:
            del self.cache[key]
            return None

        return value

    def clear(self) -> None:
        """Clear all cache entries."""
        self.cache.clear()

    def cleanup_expired(self) -> int:
        """Remove expired entries, return count removed."""
        now = time.time()
        expired_keys = [
            key
            for key, (_, timestamp) in self.cache.items()
            if now - timestamp > self.ttl
        ]
        for key in expired_keys:
            del self.cache[key]
        return len(expired_keys)


# Global reputation engine instance
reputation_engine = ReputationEngine(cache_ttl=3600)


def check_ip_reputation(ip: str) -> Dict:
    """Check reputation for a single IP."""
    try:
        reputation = reputation_engine.check_reputation(ip)
        return reputation.to_dict()
    except Exception as e:
        logger.error(f"Failed to check reputation for {ip}: {e}")
        return {
            'ip': ip,
            'final_score': 0,
            'error': str(e),
            'sources_checked': [],
        }


def should_auto_block(ip: str, threshold: int = 75) -> bool:
    """Determine if IP should be automatically blocked."""
    try:
        reputation = reputation_engine.check_reputation(ip)
        return reputation.should_block(threshold)
    except Exception as e:
        logger.error(f"Failed to check block status for {ip}: {e}")
        return False
