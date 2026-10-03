"""
Fraud Detection Agent for UGC Marketplace.

Provides fraud scoring and investigation capabilities for marketplace transactions.
Uses realistic mock data for demonstration and testing purposes.
"""

from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any


# ---------------------------------------------------------------------------
# Enums & Data Classes
# ---------------------------------------------------------------------------


class FraudRiskLevel(str, Enum):
    """Risk classification for a transaction."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class FraudFlagType(str, Enum):
    """Types of fraud indicators that can be raised."""

    VELOCITY = "velocity"
    GEO_ANOMALY = "geo_anomaly"
    AMOUNT_ANOMALY = "amount_anomaly"
    DEVICE_MISMATCH = "device_mismatch"
    ACCOUNT_AGE = "account_age"
    BEHAVIOR_PATTERN = "behavior_pattern"
    DUPLICATE_PAYMENT = "duplicate_payment"
    SELLER_RISK = "seller_risk"
    CHARGEBACK_HISTORY = "chargeback_history"
    IP_REPUTATION = "ip_reputation"


@dataclass
class FraudFlag:
    """A single fraud indicator raised during analysis."""

    flag_type: FraudFlagType
    severity: float  # 0.0 – 1.0
    description: str
    evidence: dict[str, Any] = field(default_factory=dict)


@dataclass
class FraudScore:
    """Result of a fraud detection scan."""

    transaction_id: str
    score: float  # 0.0 – 1.0 (higher = more suspicious)
    risk_level: FraudRiskLevel
    flags: list[FraudFlag]
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "transaction_id": self.transaction_id,
            "score": round(self.score, 4),
            "risk_level": self.risk_level.value,
            "flags": [
                {
                    "type": f.flag_type.value,
                    "severity": round(f.severity, 4),
                    "description": f.description,
                    "evidence": f.evidence,
                }
                for f in self.flags
            ],
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class InvestigationReport:
    """Detailed investigation report for a flagged transaction."""

    transaction_id: str
    summary: str
    risk_level: FraudRiskLevel
    overall_score: float
    flags: list[FraudFlag]
    timeline: list[dict[str, Any]]
    related_transactions: list[dict[str, Any]]
    recommendations: list[str]
    investigated_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "transaction_id": self.transaction_id,
            "summary": self.summary,
            "risk_level": self.risk_level.value,
            "overall_score": round(self.overall_score, 4),
            "flags": [
                {
                    "type": f.flag_type.value,
                    "severity": round(f.severity, 4),
                    "description": f.description,
                    "evidence": f.evidence,
                }
                for f in self.flags
            ],
            "timeline": self.timeline,
            "related_transactions": self.related_transactions,
            "recommendations": self.recommendations,
            "investigated_at": self.investigated_at.isoformat(),
        }


# ---------------------------------------------------------------------------
# Mock Data Store
# ---------------------------------------------------------------------------

# Deterministic mock transactions keyed by transaction_id
_MOCK_TRANSACTIONS: dict[str, dict[str, Any]] = {
    "txn_001": {
        "user_id": "user_42",
        "seller_id": "seller_7",
        "amount": 29.99,
        "currency": "USD",
        "payment_method": "credit_card",
        "card_country": "US",
        "ip_country": "US",
        "device_id": "dev_abc123",
        "account_age_days": 365,
        "txn_count_24h": 1,
        "txn_count_7d": 3,
        "avg_amount_30d": 35.00,
        "chargeback_count_90d": 0,
        "seller_rating": 4.8,
        "seller_txn_count": 1200,
        "ip_reputation_score": 0.05,
        "timestamp": "2026-10-01T14:30:00Z",
    },
    "txn_002": {
        "user_id": "user_99",
        "seller_id": "seller_3",
        "amount": 499.99,
        "currency": "USD",
        "payment_method": "credit_card",
        "card_country": "NG",
        "ip_country": "RU",
        "device_id": "dev_xyz789",
        "account_age_days": 2,
        "txn_count_24h": 15,
        "txn_count_7d": 42,
        "avg_amount_30d": 12.50,
        "chargeback_count_90d": 3,
        "seller_rating": 2.1,
        "seller_txn_count": 5,
        "ip_reputation_score": 0.92,
        "timestamp": "2026-10-02T03:15:00Z",
    },
    "txn_003": {
        "user_id": "user_15",
        "seller_id": "seller_12",
        "amount": 150.00,
        "currency": "USD",
        "payment_method": "paypal",
        "card_country": "GB",
        "ip_country": "GB",
        "device_id": "dev_def456",
        "account_age_days": 180,
        "txn_count_24h": 2,
        "txn_count_7d": 8,
        "avg_amount_30d": 120.00,
        "chargeback_count_90d": 0,
        "seller_rating": 4.5,
        "seller_txn_count": 350,
        "ip_reputation_score": 0.15,
        "timestamp": "2026-10-02T10:00:00Z",
    },
    "txn_004": {
        "user_id": "user_77",
        "seller_id": "seller_1",
        "amount": 999.99,
        "currency": "USD",
        "payment_method": "credit_card",
        "card_country": "US",
        "ip_country": "US",
        "device_id": "dev_abc123",
        "account_age_days": 400,
        "txn_count_24h": 1,
        "txn_count_7d": 5,
        "avg_amount_30d": 80.00,
        "chargeback_count_90d": 0,
        "seller_rating": 4.9,
        "seller_txn_count": 5000,
        "ip_reputation_score": 0.02,
        "timestamp": "2026-10-03T08:45:00Z",
    },
    "txn_005": {
        "user_id": "user_88",
        "seller_id": "seller_20",
        "amount": 75.00,
        "currency": "USD",
        "payment_method": "debit_card",
        "card_country": "CA",
        "ip_country": "BR",
        "device_id": "dev_ghi789",
        "account_age_days": 30,
        "txn_count_24h": 5,
        "txn_count_7d": 20,
        "avg_amount_30d": 45.00,
        "chargeback_count_90d": 1,
        "seller_rating": 3.2,
        "seller_txn_count": 80,
        "ip_reputation_score": 0.65,
        "timestamp": "2026-10-03T16:20:00Z",
    },
}

# Fallback generator seed offsets for unknown transaction IDs
_FALLBACK_PROFILES = [
    {"amount_range": (10, 50), "risk_bias": 0.1},
    {"amount_range": (50, 200), "risk_bias": 0.3},
    {"amount_range": (200, 500), "risk_bias": 0.5},
    {"amount_range": (500, 1000), "risk_bias": 0.7},
]


def _generate_mock_transaction(transaction_id: str) -> dict[str, Any]:
    """Generate a deterministic mock transaction for unknown IDs."""
    # Use hash of transaction_id for deterministic randomness
    hash_int = int(hashlib.sha256(transaction_id.encode()).hexdigest(), 16)
    rng = random.Random(hash_int)

    profile = _FALLBACK_PROFILES[hash_int % len(_FALLBACK_PROFILES)]
    amount = round(rng.uniform(*profile["amount_range"]), 2)

    return {
        "user_id": f"user_{hash_int % 100}",
        "seller_id": f"seller_{hash_int % 25}",
        "amount": amount,
        "currency": "USD",
        "payment_method": rng.choice(["credit_card", "debit_card", "paypal"]),
        "card_country": rng.choice(["US", "GB", "CA", "DE", "FR", "NG", "RU"]),
        "ip_country": rng.choice(["US", "GB", "CA", "DE", "FR", "NG", "RU", "BR"]),
        "device_id": f"dev_{hash_int % 1000:04d}",
        "account_age_days": rng.randint(1, 500),
        "txn_count_24h": rng.randint(1, 20),
        "txn_count_7d": rng.randint(1, 50),
        "avg_amount_30d": round(rng.uniform(5, 200), 2),
        "chargeback_count_90d": rng.randint(0, 5),
        "seller_rating": round(rng.uniform(1.0, 5.0), 1),
        "seller_txn_count": rng.randint(1, 5000),
        "ip_reputation_score": round(rng.uniform(0, 1), 2),
        "timestamp": (datetime.utcnow() - timedelta(hours=rng.randint(1, 72))).isoformat() + "Z",
    }


def _get_transaction(transaction_id: str) -> dict[str, Any]:
    """Retrieve a transaction from mock data or generate one."""
    if transaction_id in _MOCK_TRANSACTIONS:
        return _MOCK_TRANSACTIONS[transaction_id]
    return _generate_mock_transaction(transaction_id)


# ---------------------------------------------------------------------------
# Scoring Helpers
# ---------------------------------------------------------------------------


def _score_velocity(txn: dict[str, Any]) -> FraudFlag | None:
    """Detect unusual transaction velocity."""
    txn_24h = txn["txn_count_24h"]
    txn_7d = txn["txn_count_7d"]

    if txn_24h > 10:
        severity = min(0.3 + (txn_24h - 10) * 0.05, 0.95)
        return FraudFlag(
            flag_type=FraudFlagType.VELOCITY,
            severity=severity,
            description=f"High transaction velocity: {txn_24h} transactions in 24h",
            evidence={"txn_count_24h": txn_24h, "txn_count_7d": txn_7d},
        )
    elif txn_24h > 5:
        return FraudFlag(
            flag_type=FraudFlagType.VELOCITY,
            severity=0.3,
            description=f"Elevated transaction velocity: {txn_24h} transactions in 24h",
            evidence={"txn_count_24h": txn_24h, "txn_count_7d": txn_7d},
        )
    return None


def _score_geo_anomaly(txn: dict[str, Any]) -> FraudFlag | None:
    """Detect geographic mismatches."""
    card_country = txn["card_country"]
    ip_country = txn["ip_country"]

    if card_country != ip_country:
        # Higher severity for high-risk country pairs
        high_risk_countries = {"NG", "RU", "BR"}
        if card_country in high_risk_countries or ip_country in high_risk_countries:
            severity = 0.85
        else:
            severity = 0.55
        return FraudFlag(
            flag_type=FraudFlagType.GEO_ANOMALY,
            severity=severity,
            description=f"Card country ({card_country}) does not match IP country ({ip_country})",
            evidence={"card_country": card_country, "ip_country": ip_country},
        )
    return None


def _score_amount_anomaly(txn: dict[str, Any]) -> FraudFlag | None:
    """Detect unusual transaction amounts."""
    amount = txn["amount"]
    avg_amount = txn["avg_amount_30d"]

    if avg_amount > 0:
        ratio = amount / avg_amount
        if ratio > 5:
            return FraudFlag(
                flag_type=FraudFlagType.AMOUNT_ANOMALY,
                severity=min(0.4 + (ratio - 5) * 0.1, 0.9),
                description=f"Amount ${amount} is {ratio:.1f}x higher than 30-day average (${avg_amount})",
                evidence={"amount": amount, "avg_amount_30d": avg_amount, "ratio": round(ratio, 2)},
            )
        elif ratio > 3:
            return FraudFlag(
                flag_type=FraudFlagType.AMOUNT_ANOMALY,
                severity=0.4,
                description=f"Amount ${amount} is {ratio:.1f}x higher than 30-day average (${avg_amount})",
                evidence={"amount": amount, "avg_amount_30d": avg_amount, "ratio": round(ratio, 2)},
            )
    return None


def _score_account_age(txn: dict[str, Any]) -> FraudFlag | None:
    """Flag very new accounts making large purchases."""
    age_days = txn["account_age_days"]
    amount = txn["amount"]

    if age_days < 7 and amount > 100:
        severity = min(0.5 + (7 - age_days) * 0.05, 0.9)
        return FraudFlag(
            flag_type=FraudFlagType.ACCOUNT_AGE,
            severity=severity,
            description=f"Account only {age_days} days old making ${amount} purchase",
            evidence={"account_age_days": age_days, "amount": amount},
        )
    elif age_days < 30 and amount > 200:
        return FraudFlag(
            flag_type=FraudFlagType.ACCOUNT_AGE,
            severity=0.4,
            description=f"Young account ({age_days} days) making large purchase (${amount})",
            evidence={"account_age_days": age_days, "amount": amount},
        )
    return None


def _score_seller_risk(txn: dict[str, Any]) -> FraudFlag | None:
    """Assess seller risk based on rating and history."""
    rating = txn["seller_rating"]
    seller_txns = txn["seller_txn_count"]

    if rating < 2.5 and seller_txns < 50:
        return FraudFlag(
            flag_type=FraudFlagType.SELLER_RISK,
            severity=0.75,
            description=f"Low-rated seller ({rating}/5.0) with only {seller_txns} transactions",
            evidence={"seller_rating": rating, "seller_txn_count": seller_txns},
        )
    elif rating < 3.0:
        return FraudFlag(
            flag_type=FraudFlagType.SELLER_RISK,
            severity=0.4,
            description=f"Below-average seller rating: {rating}/5.0",
            evidence={"seller_rating": rating, "seller_txn_count": seller_txns},
        )
    return None


def _score_chargeback_history(txn: dict[str, Any]) -> FraudFlag | None:
    """Flag users with recent chargeback history."""
    chargebacks = txn["chargeback_count_90d"]

    if chargebacks >= 3:
        return FraudFlag(
            flag_type=FraudFlagType.CHARGEBACK_HISTORY,
            severity=0.8,
            description=f"User has {chargebacks} chargebacks in the last 90 days",
            evidence={"chargeback_count_90d": chargebacks},
        )
    elif chargebacks >= 1:
        return FraudFlag(
            flag_type=FraudFlagType.CHARGEBACK_HISTORY,
            severity=0.35,
            description=f"User has {chargebacks} chargeback(s) in the last 90 days",
            evidence={"chargeback_count_90d": chargebacks},
        )
    return None


def _score_ip_reputation(txn: dict[str, Any]) -> FraudFlag | None:
    """Flag transactions from IPs with poor reputation."""
    ip_score = txn["ip_reputation_score"]

    if ip_score > 0.8:
        return FraudFlag(
            flag_type=FraudFlagType.IP_REPUTATION,
            severity=0.7,
            description=f"IP reputation score is very poor: {ip_score}",
            evidence={"ip_reputation_score": ip_score},
        )
    elif ip_score > 0.5:
        return FraudFlag(
            flag_type=FraudFlagType.IP_REPUTATION,
            severity=0.35,
            description=f"IP reputation score is concerning: {ip_score}",
            evidence={"ip_reputation_score": ip_score},
        )
    return None


def _score_behavior_pattern(txn: dict[str, Any]) -> FraudFlag | None:
    """Detect suspicious behavior patterns."""
    # Pattern: new account + high velocity + large amount
    if (
        txn["account_age_days"] < 14
        and txn["txn_count_24h"] > 5
        and txn["amount"] > 100
    ):
        return FraudFlag(
            flag_type=FraudFlagType.BEHAVIOR_PATTERN,
            severity=0.65,
            description="Suspicious pattern: new account with high velocity and large amount",
            evidence={
                "account_age_days": txn["account_age_days"],
                "txn_count_24h": txn["txn_count_24h"],
                "amount": txn["amount"],
            },
        )
    return None


# ---------------------------------------------------------------------------
# Risk Level Calculation
# ---------------------------------------------------------------------------


def _calculate_risk_level(score: float) -> FraudRiskLevel:
    """Map a numeric score to a risk level."""
    if score >= 0.8:
        return FraudRiskLevel.CRITICAL
    elif score >= 0.6:
        return FraudRiskLevel.HIGH
    elif score >= 0.3:
        return FraudRiskLevel.MEDIUM
    return FraudRiskLevel.LOW


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def detect_fraud(transaction_id: str) -> FraudScore:
    """
    Analyze a transaction and return a fraud score with flags.

    Args:
        transaction_id: Unique identifier for the transaction to analyze.

    Returns:
        FraudScore containing the overall score (0.0–1.0), risk level,
        and any fraud flags raised.
    """
    txn = _get_transaction(transaction_id)

    # Collect all applicable flags
    flags: list[FraudFlag] = []
    scorers = [
        _score_velocity,
        _score_geo_anomaly,
        _score_amount_anomaly,
        _score_account_age,
        _score_seller_risk,
        _score_chargeback_history,
        _score_ip_reputation,
        _score_behavior_pattern,
    ]

    for scorer in scorers:
        flag = scorer(txn)
        if flag is not None:
            flags.append(flag)

    # Calculate composite score
    if not flags:
        score = 0.05  # baseline low risk
    else:
        # Weighted combination: max severity + average of remaining
        severities = sorted([f.severity for f in flags], reverse=True)
        max_sev = severities[0]
        avg_rest = sum(severities[1:]) / len(severities[1:]) if len(severities) > 1 else 0
        score = min(max_sev * 0.7 + avg_rest * 0.3, 1.0)

    risk_level = _calculate_risk_level(score)

    return FraudScore(
        transaction_id=transaction_id,
        score=score,
        risk_level=risk_level,
        flags=flags,
    )


def investigate_fraud(transaction_id: str) -> InvestigationReport:
    """
    Perform a detailed investigation of a potentially fraudulent transaction.

    Builds on detect_fraud by adding timeline analysis, related transactions,
    and actionable recommendations.

    Args:
        transaction_id: Unique identifier for the transaction to investigate.

    Returns:
        InvestigationReport with full analysis, timeline, related data,
        and recommendations.
    """
    # Get base fraud detection results
    fraud_score = detect_fraud(transaction_id)
    txn = _get_transaction(transaction_id)

    # Build investigation timeline
    txn_time = datetime.fromisoformat(txn["timestamp"].replace("Z", "+00:00"))
    timeline: list[dict[str, Any]] = [
        {
            "event": "transaction_initiated",
            "timestamp": txn["timestamp"],
            "details": f"Transaction of ${txn['amount']} initiated by {txn['user_id']}",
        },
        {
            "event": "payment_processed",
            "timestamp": (txn_time + timedelta(minutes=2)).isoformat(),
            "details": f"Payment via {txn['payment_method']} processed",
        },
    ]

    # Add fraud detection events
    for flag in fraud_score.flags:
        timeline.append({
            "event": f"flag_raised_{flag.flag_type.value}",
            "timestamp": (txn_time + timedelta(minutes=5)).isoformat(),
            "details": flag.description,
        })

    timeline.append({
        "event": "investigation_completed",
        "timestamp": datetime.utcnow().isoformat(),
        "details": f"Risk level assessed as {fraud_score.risk_level.value}",
    })

    # Find related transactions (same user or same device)
    related: list[dict[str, Any]] = []
    for mock_id, mock_txn in _MOCK_TRANSACTIONS.items():
        if mock_id == transaction_id:
            continue
        if (
            mock_txn["user_id"] == txn["user_id"]
            or mock_txn["device_id"] == txn["device_id"]
        ):
            related.append({
                "transaction_id": mock_id,
                "amount": mock_txn["amount"],
                "timestamp": mock_txn["timestamp"],
                "seller_id": mock_txn["seller_id"],
                "relationship": "same_user" if mock_txn["user_id"] == txn["user_id"] else "same_device",
            })

    # Generate recommendations based on flags
    recommendations: list[str] = []
    flag_types = {f.flag_type for f in fraud_score.flags}

    if fraud_score.risk_level in (FraudRiskLevel.HIGH, FraudRiskLevel.CRITICAL):
        recommendations.append("Block transaction pending manual review")
        recommendations.append("Notify account manager for immediate follow-up")

    if FraudFlagType.VELOCITY in flag_types:
        recommendations.append("Implement rate limiting on user account")
        recommendations.append("Review all transactions from last 24 hours")

    if FraudFlagType.GEO_ANOMALY in flag_types:
        recommendations.append("Request additional identity verification")
        recommendations.append("Cross-check with user's typical locations")

    if FraudFlagType.AMOUNT_ANOMALY in flag_types:
        recommendations.append("Verify purchase intent with user via registered contact")

    if FraudFlagType.ACCOUNT_AGE in flag_types:
        recommendations.append("Apply enhanced monitoring for first 30 days")

    if FraudFlagType.SELLER_RISK in flag_types:
        recommendations.append("Review seller account for policy violations")
        recommendations.append("Consider temporary seller suspension")

    if FraudFlagType.CHARGEBACK_HISTORY in flag_types:
        recommendations.append("Flag user for chargeback monitoring program")

    if FraudFlagType.IP_REPUTATION in flag_types:
        recommendations.append("Block IP range if pattern continues")
        recommendations.append("Check against known VPN/proxy lists")

    if FraudFlagType.BEHAVIOR_PATTERN in flag_types:
        recommendations.append("Apply step-up authentication for future transactions")

    if not recommendations:
        recommendations.append("No immediate action required")
        recommendations.append("Continue standard monitoring")

    # Build summary
    if fraud_score.flags:
        flag_summary = ", ".join(f.flag_type.value for f in fraud_score.flags)
        summary = (
            f"Transaction {transaction_id} scored {fraud_score.score:.2f} "
            f"({fraud_score.risk_level.value} risk). Flags raised: {flag_summary}."
        )
    else:
        summary = (
            f"Transaction {transaction_id} appears legitimate "
            f"(score: {fraud_score.score:.2f}, low risk)."
        )

    return InvestigationReport(
        transaction_id=transaction_id,
        summary=summary,
        risk_level=fraud_score.risk_level,
        overall_score=fraud_score.score,
        flags=fraud_score.flags,
        timeline=timeline,
        related_transactions=related,
        recommendations=recommendations,
    )


# ---------------------------------------------------------------------------
# Module-level convenience (optional CLI usage)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import json
    import sys

    if len(sys.argv) < 2:
        print("Usage: python fraud_detection.py <transaction_id> [--investigate]")
        sys.exit(1)

    txn_id = sys.argv[1]
    if "--investigate" in sys.argv:
        report = investigate_fraud(txn_id)
        print(json.dumps(report.to_dict(), indent=2))
    else:
        score = detect_fraud(txn_id)
        print(json.dumps(score.to_dict(), indent=2))
