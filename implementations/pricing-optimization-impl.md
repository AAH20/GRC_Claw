# AI-Powered Pricing Optimization Implementation Plan

## LangChain DeepAgents Architecture

---

## Table of Contents

1. [Agent Architecture](#1-agent-architecture)
2. [Market Intelligence Agent](#2-market-intelligence-agent)
3. [Pricing Optimization Engine](#3-pricing-optimization-engine)
4. [Testing Agent](#4-testing-agent)
5. [Implementation Agent](#5-implementation-agent)
6. [Monitoring Agent](#6-monitoring-agent)
7. [Performance Analytics Agent](#7-performance-analytics-agent)
8. [Code Examples and Snippets](#8-code-examples-and-snippets)
9. [Testing Strategy](#9-testing-strategy)

---

## 1. Agent Architecture

### 1.1 System Overview

The AI-powered pricing optimization system uses a multi-agent architecture built on LangChain DeepAgents. The system consists of six specialized agents that collaborate to monitor markets, optimize prices, test changes, implement updates, and track performance.

```
┌─────────────────────────────────────────────────────────────────┐
│                    Pricing Optimization System                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐       │
│  │   Market     │    │   Pricing    │    │   Testing    │       │
│  │ Intelligence │───▶│ Optimization │───▶│    Agent     │       │
│  │    Agent     │    │   Engine     │    │              │       │
│  └──────────────┘    └──────────────┘    └──────────────┘       │
│         │                   │                   │                 │
│         ▼                   ▼                   ▼                 │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐       │
│  │    Monitor   │    │  Performance │    │Implementation│       │
│  │    Agent     │    │  Analytics   │    │    Agent     │       │
│  │              │    │    Agent     │    │              │       │
│  └──────────────┘    └──────────────┘    └──────────────┘       │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 Agent Communication Protocol

All agents communicate through a shared event bus using a standardized message format:

```python
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid


class AgentType(Enum):
    MARKET_INTELLIGENCE = "market_intelligence"
    PRICING_OPTIMIZATION = "pricing_optimization"
    TESTING = "testing"
    IMPLEMENTATION = "implementation"
    MONITORING = "monitoring"
    PERFORMANCE_ANALYTICS = "performance_analytics"


class MessagePriority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class AgentMessage:
    """Standard inter-agent communication message."""
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source_agent: AgentType = None
    target_agent: Optional[AgentType] = None  # None = broadcast
    message_type: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)
    priority: MessagePriority = MessagePriority.MEDIUM
    timestamp: datetime = field(default_factory=datetime.utcnow)
    correlation_id: Optional[str] = None  # Links related messages
    ttl_seconds: int = 300  # Message time-to-live

    def to_dict(self) -> Dict[str, Any]:
        return {
            "message_id": self.message_id,
            "source_agent": self.source_agent.value if self.source_agent else None,
            "target_agent": self.target_agent.value if self.target_agent else None,
            "message_type": self.message_type,
            "payload": self.payload,
            "priority": self.priority.value,
            "timestamp": self.timestamp.isoformat(),
            "correlation_id": self.correlation_id,
            "ttl_seconds": self.ttl_seconds,
        }
```

### 1.3 Shared State Management

```python
from typing import Any, Dict, List, Optional
from datetime import datetime
import json
import redis
from contextlib import contextmanager


class SharedStateManager:
    """Centralized state management for all agents."""

    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        self.redis = redis.from_url(redis_url, decode_responses=True)
        self._local_cache: Dict[str, Any] = {}

    def set(self, key: str, value: Any, ttl_seconds: int = 3600) -> None:
        """Store a value with optional TTL."""
        serialized = json.dumps(value, default=str)
        self.redis.setex(key, ttl_seconds, serialized)
        self._local_cache[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """Retrieve a value."""
        if key in self._local_cache:
            return self._local_cache[key]
        raw = self.redis.get(key)
        if raw is None:
            return default
        value = json.loads(raw)
        self._local_cache[key] = value
        return value

    def publish(self, channel: str, message: Dict[str, Any]) -> None:
        """Publish a message to a channel."""
        self.redis.publish(channel, json.dumps(message, default=str))

    def subscribe(self, channel: str):
        """Subscribe to a channel."""
        pubsub = self.redis.pubsub()
        pubsub.subscribe(channel)
        return pubsub

    @contextmanager
    def lock(self, lock_name: str, timeout: int = 10):
        """Distributed lock for critical sections."""
        lock_key = f"lock:{lock_name}"
        identifier = str(uuid.uuid4())
        acquired = self.redis.set(lock_key, identifier, nx=True, ex=timeout)
        if not acquired:
            raise RuntimeError(f"Could not acquire lock: {lock_name}")
        try:
            yield identifier
        finally:
            # Only release if we still own the lock
            current = self.redis.get(lock_key)
            if current == identifier:
                self.redis.delete(lock_key)
```

### 1.4 Base Agent Class

```python
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional
import logging
import asyncio
from datetime import datetime

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Base class for all pricing optimization agents."""

    def __init__(
        self,
        agent_type: AgentType,
        state_manager: SharedStateManager,
        config: Optional[Dict[str, Any]] = None,
    ):
        self.agent_type = agent_type
        self.state_manager = state_manager
        self.config = config or {}
        self._handlers: Dict[str, Callable] = {}
        self._running = False
        self._message_queue: asyncio.Queue = asyncio.Queue()
        self.logger = logging.getLogger(f"agent.{agent_type.value}")

    def register_handler(self, message_type: str, handler: Callable) -> None:
        """Register a message handler for a specific message type."""
        self._handlers[message_type] = handler

    async def start(self) -> None:
        """Start the agent's message processing loop."""
        self._running = True
        self.logger.info(f"Agent {self.agent_type.value} starting")
        await self.on_start()
        while self._running:
            try:
                message = await asyncio.wait_for(
                    self._message_queue.get(), timeout=1.0
                )
                await self._process_message(message)
            except asyncio.TimeoutError:
                await self._idle_tick()
            except Exception as e:
                self.logger.error(f"Error processing message: {e}", exc_info=True)

    async def stop(self) -> None:
        """Stop the agent."""
        self._running = False
        await self.on_stop()
        self.logger.info(f"Agent {self.agent_type.value} stopped")

    async def send_message(self, message: AgentMessage) -> None:
        """Send a message to another agent or broadcast."""
        channel = (
            f"agent:{message.target_agent.value}"
            if message.target_agent
            else "agent:broadcast"
        )
        self.state_manager.publish(channel, message.to_dict())

    async def receive_message(self, message: AgentMessage) -> None:
        """Receive a message for processing."""
        await self._message_queue.put(message)

    async def _process_message(self, message: AgentMessage) -> None:
        """Process an incoming message."""
        handler = self._handlers.get(message.message_type)
        if handler:
            try:
                await handler(message)
            except Exception as e:
                self.logger.error(
                    f"Handler error for {message.message_type}: {e}",
                    exc_info=True,
                )
        else:
            self.logger.warning(
                f"No handler for message type: {message.message_type}"
            )

    async def _idle_tick(self) -> None:
        """Called when no messages are available. Override for polling."""
        pass

    @abstractmethod
    async def on_start(self) -> None:
        """Called when the agent starts. Override in subclasses."""
        pass

    @abstractmethod
    async def on_stop(self) -> None:
        """Called when the agent stops. Override in subclasses."""
        pass
```

---

## 2. Market Intelligence Agent

### 2.1 Purpose

The Market Intelligence Agent continuously monitors competitor pricing, market trends, demand signals, and external factors (seasonality, events, economic indicators) that affect pricing decisions.

### 2.2 Implementation

```python
import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class CompetitorPrice:
    """Represents a competitor's price observation."""
    competitor_id: str
    product_id: str
    price: float
    currency: str
    timestamp: datetime
    source_url: Optional[str] = None
    confidence: float = 1.0  # 0-1 confidence in the data
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MarketSignal:
    """A market intelligence signal."""
    signal_type: str  # "competitor_price_change", "demand_surge", "seasonality", etc.
    product_id: str
    value: Any
    confidence: float
    timestamp: datetime
    source: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class MarketIntelligenceAgent(BaseAgent):
    """
    Monitors market conditions and competitor pricing.
    
    Responsibilities:
    - Scrape competitor prices from web sources
    - Monitor demand signals (search trends, social sentiment)
    - Track seasonality patterns
    - Detect market events (product launches, promotions)
    - Emit pricing-relevant signals to other agents
    """

    def __init__(
        self,
        state_manager: SharedStateManager,
        config: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(AgentType.MARKET_INTELLIGENCE, state_manager, config)
        self.competitor_urls: List[str] = config.get("competitor_urls", [])
        self.poll_interval_seconds: int = config.get("poll_interval_seconds", 300)
        self.product_catalog: List[str] = config.get("product_catalog", [])
        self._session: Optional[aiohttp.ClientSession] = None
        self._price_history: Dict[str, List[CompetitorPrice]] = {}

        # Register message handlers
        self.register_handler("price_check_request", self._handle_price_check_request)
        self.register_handler("competitor_update", self._handle_competitor_update)

    async def on_start(self) -> None:
        """Initialize HTTP session and load state."""
        self._session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={
                "User-Agent": "PricingBot/1.0 (Market Intelligence)"
            },
        )
        # Load historical price data
        history = self.state_manager.get("market:price_history", {})
        self._price_history = history
        self.logger.info(
            f"Market Intelligence Agent started with "
            f"{len(self.competitor_urls)} competitors, "
            f"{len(self.product_catalog)} products"
        )

    async def on_stop(self) -> None:
        """Clean up resources."""
        if self._session:
            await self._session.close()
        # Persist price history
        self.state_manager.set("market:price_history", self._price_history)

    async def _idle_tick(self) -> None:
        """Periodic market scanning."""
        await self._scan_competitor_prices()
        await self._analyze_market_trends()
        await asyncio.sleep(self.poll_interval_seconds)

    async def _scan_competitor_prices(self) -> None:
        """Scrape competitor prices from configured sources."""
        tasks = []
        for url in self.competitor_urls:
            for product_id in self.product_catalog:
                tasks.append(self._fetch_competitor_price(url, product_id))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, Exception):
                logger.warning(f"Failed to fetch competitor price: {result}")
                continue
            if result:
                await self._process_price_observation(result)

    async def _fetch_competitor_price(
        self, url: str, product_id: str
    ) -> Optional[CompetitorPrice]:
        """Fetch a single competitor price."""
        try:
            # In production, use proper scraping with parsing
            # This is a simplified example
            async with self._session.get(
                f"{url}/products/{product_id}"
            ) as response:
                if response.status != 200:
                    return None
                data = await response.json()
                return CompetitorPrice(
                    competitor_id=self._extract_competitor_id(url),
                    product_id=product_id,
                    price=float(data["price"]),
                    currency=data.get("currency", "USD"),
                    timestamp=datetime.utcnow(),
                    source_url=f"{url}/products/{product_id}",
                    confidence=0.9,
                    metadata={"raw_data": data},
                )
        except Exception as e:
            logger.error(f"Error fetching {url}/products/{product_id}: {e}")
            return None

    async def _process_price_observation(
        self, observation: CompetitorPrice
    ) -> None:
        """Process a new price observation and detect changes."""
        key = f"{observation.competitor_id}:{observation.product_id}"
        history = self._price_history.get(key, [])

        # Check for significant price change
        if history:
            last_price = history[-1].price
            change_pct = (
                (observation.price - last_price) / last_price * 100
            )
            if abs(change_pct) > 2.0:  # 2% threshold
                signal = MarketSignal(
                    signal_type="competitor_price_change",
                    product_id=observation.product_id,
                    value={
                        "old_price": last_price,
                        "new_price": observation.price,
                        "change_pct": change_pct,
                        "competitor_id": observation.competitor_id,
                    },
                    confidence=observation.confidence,
                    timestamp=datetime.utcnow(),
                    source="market_intelligence",
                )
                await self._emit_signal(signal)

        # Update history
        history.append(observation)
        # Keep last 100 observations
        self._price_history[key] = history[-100:]

    async def _analyze_market_trends(self) -> None:
        """Analyze collected data for market trends."""
        for product_id in self.product_catalog:
            # Calculate average competitor price
            prices = []
            for key, history in self._price_history.items():
                if key.endswith(f":{product_id}") and history:
                    prices.append(history[-1].price)

            if len(prices) >= 2:
                avg_price = sum(prices) / len(prices)
                min_price = min(prices)
                max_price = max(prices)
                price_spread = (max_price - min_price) / avg_price * 100

                # Emit market position signal
                signal = MarketSignal(
                    signal_type="market_position",
                    product_id=product_id,
                    value={
                        "avg_competitor_price": avg_price,
                        "min_competitor_price": min_price,
                        "max_competitor_price": max_price,
                        "price_spread_pct": price_spread,
                        "competitor_count": len(prices),
                    },
                    confidence=0.85,
                    timestamp=datetime.utcnow(),
                    source="market_intelligence",
                )
                await self._emit_signal(signal)

    async def _emit_signal(self, signal: MarketSignal) -> None:
        """Emit a market signal to the pricing optimization agent."""
        message = AgentMessage(
            source_agent=self.agent_type,
            target_agent=AgentType.PRICING_OPTIMIZATION,
            message_type="market_signal",
            payload={
                "signal_type": signal.signal_type,
                "product_id": signal.product_id,
                "value": signal.value,
                "confidence": signal.confidence,
                "timestamp": signal.timestamp.isoformat(),
                "source": signal.source,
            },
            priority=MessagePriority.HIGH
            if signal.signal_type == "competitor_price_change"
            else MessagePriority.MEDIUM,
        )
        await self.send_message(message)

    async def _handle_price_check_request(
        self, message: AgentMessage
    ) -> None:
        """Handle a request for current market prices."""
        product_id = message.payload.get("product_id")
        if not product_id:
            return

        # Gather current prices for the product
        current_prices = {}
        for key, history in self._price_history.items():
            if key.endswith(f":{product_id}") and history:
                competitor_id = key.split(":")[0]
                current_prices[competitor_id] = {
                    "price": history[-1].price,
                    "currency": history[-1].currency,
                    "timestamp": history[-1].timestamp.isoformat(),
                }

        # Send response back to requester
        response = AgentMessage(
            source_agent=self.agent_type,
            target_agent=message.source_agent,
            message_type="price_check_response",
            payload={
                "product_id": product_id,
                "current_prices": current_prices,
                "correlation_id": message.correlation_id,
            },
            correlation_id=message.correlation_id,
        )
        await self.send_message(response)

    async def _handle_competitor_update(
        self, message: AgentMessage
    ) -> None:
        """Handle manual competitor update from external source."""
        competitor_data = message.payload.get("competitor_data")
        if competitor_data:
            observation = CompetitorPrice(
                competitor_id=competitor_data["competitor_id"],
                product_id=competitor_data["product_id"],
                price=competitor_data["price"],
                currency=competitor_data.get("currency", "USD"),
                timestamp=datetime.utcnow(),
                source_url=competitor_data.get("source_url"),
                confidence=competitor_data.get("confidence", 0.8),
            )
            await self._process_price_observation(observation)

    def _extract_competitor_id(self, url: str) -> str:
        """Extract a competitor ID from a URL."""
        from urllib.parse import urlparse
        parsed = urlparse(url)
        return parsed.netloc.replace(".", "_")
```

### 2.3 Data Sources Configuration

```python
MARKET_INTELLIGENCE_CONFIG = {
    "competitor_urls": [
        "https://api.competitor-a.com/v1",
        "https://api.competitor-b.com/v2",
        "https://api.competitor-c.com/v1",
    ],
    "product_catalog": [
        "PROD-001", "PROD-002", "PROD-003",
        "PROD-004", "PROD-005",
    ],
    "poll_interval_seconds": 300,  # 5 minutes
    "price_change_threshold_pct": 2.0,
    "trend_analysis_window_hours": 24,
    "external_data_sources": {
        "google_trends": {"enabled": True, "api_key": "${GOOGLE_TRENDS_API_KEY}"},
        "social_sentiment": {"enabled": True, "platforms": ["twitter", "reddit"]},
        "economic_indicators": {"enabled": True, "sources": ["bls", "bea"]},
    },
}
```

---

## 3. Pricing Optimization Engine

### 3.1 Purpose

The Pricing Optimization Engine is the core decision-making component. It receives market signals, demand forecasts, and business constraints to compute optimal prices using a combination of rule-based logic and ML models.

### 3.2 Implementation

```python
import numpy as np
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
import logging

logger = logging.getLogger(__name__)


class PricingStrategy(Enum):
    COST_PLUS = "cost_plus"
    COMPETITIVE = "competitive"
    VALUE_BASED = "value_based"
    DYNAMIC = "dynamic"
    PENETRATION = "penetration"
    SKIMMING = "skimming"


@dataclass
class PricingConstraint:
    """Business constraints for pricing."""
    min_price: float
    max_price: float
    min_margin_pct: float
    max_discount_pct: float
    price_ending: float = 0.99  # Psychological pricing ending
    round_to: float = 1.0  # Round to nearest


@dataclass
class PricingDecision:
    """A pricing decision with full context."""
    product_id: str
    current_price: float
    recommended_price: float
    strategy: PricingStrategy
    confidence: float
    expected_demand_change_pct: float
    expected_revenue_change_pct: float
    expected_profit_change_pct: float
    reasoning: List[str] = field(default_factory=list)
    constraints_applied: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    valid_until: datetime = field(
        default_factory=lambda: datetime.utcnow() + timedelta(hours=24)
    )


class DemandForecaster:
    """ML-based demand forecasting."""

    def __init__(self, model_path: Optional[str] = None):
        self.model = None
        self.model_path = model_path
        self._load_model()

    def _load_model(self) -> None:
        """Load the demand forecasting model."""
        if self.model_path:
            import joblib
            self.model = joblib.load(self.model_path)
            logger.info(f"Loaded demand model from {self.model_path}")

    def forecast(
        self,
        product_id: str,
        price: float,
        features: Dict[str, Any],
    ) -> Dict[str, float]:
        """
        Forecast demand at a given price point.
        
        Returns dict with:
        - expected_demand: predicted units
        - demand_uncertainty: standard deviation
        - elasticity: price elasticity at this point
        """
        if self.model is None:
            # Fallback: simple elasticity model
            base_demand = features.get("base_demand", 100)
            elasticity = features.get("price_elasticity", -1.5)
            reference_price = features.get("reference_price", price)
            expected_demand = base_demand * (price / reference_price) ** elasticity
            return {
                "expected_demand": max(0, expected_demand),
                "demand_uncertainty": expected_demand * 0.15,
                "elasticity": elasticity,
            }

        # Use ML model
        feature_vector = self._build_feature_vector(product_id, price, features)
        prediction = self.model.predict([feature_vector])[0]
        uncertainty = self.model.predict_std([feature_vector])[0] if hasattr(
            self.model, "predict_std"
        ) else prediction * 0.15

        return {
            "expected_demand": max(0, prediction),
            "demand_uncertainty": max(0, uncertainty),
            "elasticity": self._estimate_elasticity(feature_vector),
        }

    def _build_feature_vector(
        self, product_id: str, price: float, features: Dict[str, Any]
    ) -> np.ndarray:
        """Build feature vector for the ML model."""
        return np.array([
            price,
            features.get("base_demand", 100),
            features.get("avg_competitor_price", price),
            features.get("seasonality_index", 1.0),
            features.get("day_of_week", 1),
            features.get("month", 1),
            features.get("is_holiday", 0),
            features.get("marketing_spend", 0),
        ])

    def _estimate_elasticity(self, feature_vector: np.ndarray) -> float:
        """Estimate price elasticity at a point."""
        # Simplified elasticity estimation
        return -1.5  # Default elasticity


class PricingOptimizationEngine(BaseAgent):
    """
    Core pricing optimization engine.
    
    Responsibilities:
    - Receive market signals and demand forecasts
    - Compute optimal prices using multiple strategies
    - Apply business constraints
    - Generate pricing decisions with confidence scores
    - Coordinate with testing agent for validation
    """

    def __init__(
        self,
        state_manager: SharedStateManager,
        config: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(AgentType.PRICING_OPTIMIZATION, state_manager, config)
        self.demand_forecaster = DemandForecaster(
            config.get("demand_model_path")
        )
        self.default_strategy = PricingStrategy(
            config.get("default_strategy", "dynamic")
        )
        self.optimization_interval_seconds: int = config.get(
            "optimization_interval_seconds", 600
        )
        self.min_confidence_threshold: float = config.get(
            "min_confidence_threshold", 0.7
        )
        self.max_price_change_pct: float = config.get(
            "max_price_change_pct", 15.0
        )

        # Product-specific configuration
        self.product_config: Dict[str, Dict[str, Any]] = config.get(
            "product_config", {}
        )

        # Register handlers
        self.register_handler("market_signal", self._handle_market_signal)
        self.register_handler("pricing_request", self._handle_pricing_request)
        self.register_handler("test_result", self._handle_test_result)

    async def on_start(self) -> None:
        """Initialize pricing engine state."""
        self._current_prices: Dict[str, float] = self.state_manager.get(
            "pricing:current_prices", {}
        )
        self._price_history: Dict[str, List[Dict]] = self.state_manager.get(
            "pricing:price_history", {}
        )
        self._active_decisions: Dict[str, PricingDecision] = {}
        self.logger.info("Pricing Optimization Engine started")

    async def on_stop(self) -> None:
        """Persist state."""
        self.state_manager.set("pricing:current_prices", self._current_prices)
        self.state_manager.set("pricing:price_history", self._price_history)

    async def _idle_tick(self) -> None:
        """Periodic optimization run."""
        await self._run_optimization_cycle()
        await asyncio.sleep(self.optimization_interval_seconds)

    async def _run_optimization_cycle(self) -> None:
        """Run a full optimization cycle for all products."""
        for product_id in self.product_config:
            try:
                decision = await self._optimize_product_price(product_id)
                if decision and decision.confidence >= self.min_confidence_threshold:
                    await self._propose_price_change(decision)
            except Exception as e:
                self.logger.error(
                    f"Error optimizing {product_id}: {e}", exc_info=True
                )

    async def _optimize_product_price(
        self, product_id: str
    ) -> Optional[PricingDecision]:
        """Compute optimal price for a single product."""
        config = self.product_config[product_id]
        current_price = self._current_prices.get(
            product_id, config.get("base_price", 100.0)
        )
        constraints = PricingConstraint(
            min_price=config.get("min_price", current_price * 0.7),
            max_price=config.get("max_price", current_price * 1.5),
            min_margin_pct=config.get("min_margin_pct", 10.0),
            max_discount_pct=config.get("max_discount_pct", 30.0),
        )

        # Gather market context
        market_context = await self._gather_market_context(product_id)

        # Try multiple strategies and pick the best
        candidates = []
        for strategy in PricingStrategy:
            decision = await self._evaluate_strategy(
                strategy, product_id, current_price, constraints, market_context
            )
            if decision:
                candidates.append(decision)

        if not candidates:
            return None

        # Pick the decision with highest expected profit
        best = max(candidates, key=lambda d: d.expected_profit_change_pct)

        # Cap the price change
        max_change = current_price * (self.max_price_change_pct / 100)
        if abs(best.recommended_price - current_price) > max_change:
            if best.recommended_price > current_price:
                best.recommended_price = current_price + max_change
            else:
                best.recommended_price = current_price - max_change
            best.constraints_applied.append("max_price_change_cap")

        return best

    async def _evaluate_strategy(
        self,
        strategy: PricingStrategy,
        product_id: str,
        current_price: float,
        constraints: PricingConstraint,
        market_context: Dict[str, Any],
    ) -> Optional[PricingDecision]:
        """Evaluate a single pricing strategy."""
        config = self.product_config[product_id]
        cost = config.get("unit_cost", current_price * 0.6)

        if strategy == PricingStrategy.COST_PLUS:
            target_margin = config.get("target_margin_pct", 25.0)
            recommended = cost / (1 - target_margin / 100)

        elif strategy == PricingStrategy.COMPETITIVE:
            avg_competitor = market_context.get("avg_competitor_price", current_price)
            position = config.get("competitive_position", "match")
            if position == "match":
                recommended = avg_competitor
            elif position == "undercut":
                recommended = avg_competitor * 0.98
            elif position == "premium":
                recommended = avg_competitor * 1.05
            else:
                recommended = current_price

        elif strategy == PricingStrategy.DYNAMIC:
            recommended = self._dynamic_pricing(
                current_price, market_context, config
            )

        elif strategy == PricingStrategy.VALUE_BASED:
            value_score = market_context.get("value_score", 0.5)
            recommended = current_price * (0.9 + 0.2 * value_score)

        elif strategy == PricingStrategy.PENETRATION:
            recommended = cost * 1.05  # Minimal margin for market entry

        elif strategy == PricingStrategy.SKIMMING:
            recommended = constraints.max_price * 0.95

        else:
            return None

        # Apply constraints
        recommended = self._apply_constraints(
            recommended, constraints, current_price, cost
        )

        # Forecast demand at recommended price
        forecast = self.demand_forecaster.forecast(
            product_id,
            recommended,
            {
                "base_demand": config.get("base_demand", 100),
                "reference_price": current_price,
                "price_elasticity": config.get("price_elasticity", -1.5),
                "avg_competitor_price": market_context.get(
                    "avg_competitor_price", current_price
                ),
                "seasonality_index": market_context.get("seasonality", 1.0),
            },
        )

        # Calculate expected outcomes
        current_forecast = self.demand_forecaster.forecast(
            product_id,
            current_price,
            {
                "base_demand": config.get("base_demand", 100),
                "reference_price": current_price,
                "price_elasticity": config.get("price_elasticity", -1.5),
            },
        )

        demand_change = (
            (forecast["expected_demand"] - current_forecast["expected_demand"])
            / max(current_forecast["expected_demand"], 1)
            * 100
        )
        revenue_change = (
            (forecast["expected_demand"] * recommended
             - current_forecast["expected_demand"] * current_price)
            / max(current_forecast["expected_demand"] * current_price, 1)
            * 100
        )
        profit_change = (
            ((forecast["expected_demand"] * (recommended - cost))
             - (current_forecast["expected_demand"] * (current_price - cost)))
            / max(current_forecast["expected_demand"] * (current_price - cost), 1)
            * 100
        )

        # Calculate confidence
        confidence = self._calculate_confidence(
            strategy, forecast, market_context
        )

        reasoning = [
            f"Strategy: {strategy.value}",
            f"Current price: ${current_price:.2f}",
            f"Recommended price: ${recommended:.2f}",
            f"Expected demand change: {demand_change:+.1f}%",
            f"Expected revenue change: {revenue_change:+.1f}%",
            f"Expected profit change: {profit_change:+.1f}%",
            f"Demand forecast: {forecast['expected_demand']:.0f} units",
        ]

        return PricingDecision(
            product_id=product_id,
            current_price=current_price,
            recommended_price=recommended,
            strategy=strategy,
            confidence=confidence,
            expected_demand_change_pct=demand_change,
            expected_revenue_change_pct=revenue_change,
            expected_profit_change_pct=profit_change,
            reasoning=reasoning,
        )

    def _dynamic_pricing(
        self,
        current_price: float,
        market_context: Dict[str, Any],
        config: Dict[str, Any],
    ) -> float:
        """Compute dynamic price based on multiple factors."""
        base = current_price

        # Demand adjustment
        demand_factor = market_context.get("demand_factor", 1.0)
        base *= demand_factor

        # Competitor adjustment
        avg_competitor = market_context.get("avg_competitor_price", current_price)
        competitor_ratio = avg_competitor / current_price
        if competitor_ratio < 0.95:
            base *= 0.98  # Slight decrease to stay competitive
        elif competitor_ratio > 1.05:
            base *= 1.02  # Room to increase

        # Seasonality adjustment
        seasonality = market_context.get("seasonality", 1.0)
        base *= seasonality

        # Inventory adjustment
        inventory_level = market_context.get("inventory_level", 1.0)
        if inventory_level > 1.5:  # Overstocked
            base *= 0.95
        elif inventory_level < 0.5:  # Low stock
            base *= 1.05

        return base

    def _apply_constraints(
        self,
        price: float,
        constraints: PricingConstraint,
        current_price: float,
        cost: float,
    ) -> float:
        """Apply business constraints to a price."""
        # Min/max price
        price = max(constraints.min_price, min(constraints.max_price, price))

        # Margin constraint
        min_price_for_margin = cost / (1 - constraints.min_margin_pct / 100)
        price = max(price, min_price_for_margin)

        # Max discount constraint
        max_discount_price = current_price * (1 - constraints.max_discount_pct / 100)
        price = max(price, max_discount_price)

        # Psychological pricing ending
        if constraints.price_ending:
            price = np.floor(price) + constraints.price_ending

        # Round to nearest
        if constraints.round_to > 0:
            price = round(price / constraints.round_to) * constraints.round_to

        return price

    def _calculate_confidence(
        self,
        strategy: PricingStrategy,
        forecast: Dict[str, float],
        market_context: Dict[str, Any],
    ) -> float:
        """Calculate confidence score for a pricing decision."""
        confidence = 0.7  # Base confidence

        # Adjust based on forecast uncertainty
        uncertainty_ratio = forecast["demand_uncertainty"] / max(
            forecast["expected_demand"], 1
        )
        confidence -= uncertainty_ratio * 0.3

        # Adjust based on data quality
        if market_context.get("competitor_count", 0) >= 3:
            confidence += 0.1

        # Strategy-specific adjustments
        if strategy == PricingStrategy.DYNAMIC:
            confidence += 0.05  # More data-driven

        return max(0.0, min(1.0, confidence))

    async def _gather_market_context(
        self, product_id: str
    ) -> Dict[str, Any]:
        """Gather market context for a product."""
        context = {
            "avg_competitor_price": None,
            "min_competitor_price": None,
            "max_competitor_price": None,
            "competitor_count": 0,
            "demand_factor": 1.0,
            "seasonality": 1.0,
            "inventory_level": 1.0,
            "value_score": 0.5,
        }

        # Get competitor prices from state
        competitor_prices = self.state_manager.get(
            f"market:competitor_prices:{product_id}", {}
        )
        if competitor_prices:
            prices = [p["price"] for p in competitor_prices.values()]
            context["avg_competitor_price"] = sum(prices) / len(prices)
            context["min_competitor_price"] = min(prices)
            context["max_competitor_price"] = max(prices)
            context["competitor_count"] = len(prices)

        # Get demand signals
        demand_signals = self.state_manager.get(
            f"market:demand_signals:{product_id}", {}
        )
        context["demand_factor"] = demand_signals.get("demand_factor", 1.0)
        context["seasonality"] = demand_signals.get("seasonality", 1.0)

        # Get inventory level
        context["inventory_level"] = self.state_manager.get(
            f"inventory:{product_id}:level", 1.0
        )

        return context

    async def _propose_price_change(
        self, decision: PricingDecision
    ) -> None:
        """Propose a price change to the testing agent."""
        self._active_decisions[decision.product_id] = decision

        message = AgentMessage(
            source_agent=self.agent_type,
            target_agent=AgentType.TESTING,
            message_type="price_change_proposal",
            payload={
                "product_id": decision.product_id,
                "current_price": decision.current_price,
                "proposed_price": decision.recommended_price,
                "strategy": decision.strategy.value,
                "confidence": decision.confidence,
                "expected_impact": {
                    "demand_change_pct": decision.expected_demand_change_pct,
                    "revenue_change_pct": decision.expected_revenue_change_pct,
                    "profit_change_pct": decision.expected_profit_change_pct,
                },
                "reasoning": decision.reasoning,
            },
            priority=MessagePriority.HIGH,
        )
        await self.send_message(message)

    async def _handle_market_signal(
        self, message: AgentMessage
    ) -> None:
        """Handle incoming market signals."""
        signal_type = message.payload.get("signal_type")
        product_id = message.payload.get("product_id")

        if signal_type == "competitor_price_change":
            # Trigger immediate re-optimization
            decision = await self._optimize_product_price(product_id)
            if decision and decision.confidence >= self.min_confidence_threshold:
                await self._propose_price_change(decision)

        elif signal_type == "market_position":
            # Update stored competitor prices
            self.state_manager.set(
                f"market:competitor_prices:{product_id}",
                message.payload.get("value"),
            )

    async def _handle_pricing_request(
        self, message: AgentMessage
    ) -> None:
        """Handle a direct pricing request."""
        product_id = message.payload.get("product_id")
        if product_id:
            decision = await self._optimize_product_price(product_id)
            if decision:
                response = AgentMessage(
                    source_agent=self.agent_type,
                    target_agent=message.source_agent,
                    message_type="pricing_response",
                    payload={
                        "decision": {
                            "product_id": decision.product_id,
                            "current_price": decision.current_price,
                            "recommended_price": decision.recommended_price,
                            "strategy": decision.strategy.value,
                            "confidence": decision.confidence,
                            "expected_impact": {
                                "demand_change_pct": decision.expected_demand_change_pct,
                                "revenue_change_pct": decision.expected_revenue_change_pct,
                                "profit_change_pct": decision.expected_profit_change_pct,
                            },
                            "reasoning": decision.reasoning,
                        }
                    },
                    correlation_id=message.correlation_id,
                )
                await self.send_message(response)

    async def _handle_test_result(
        self, message: AgentMessage
    ) -> None:
        """Handle test results from the testing agent."""
        product_id = message.payload.get("product_id")
        test_passed = message.payload.get("test_passed", False)

        if test_passed and product_id in self._active_decisions:
            decision = self._active_decisions[product_id]
            # Forward to implementation agent
            impl_message = AgentMessage(
                source_agent=self.agent_type,
                target_agent=AgentType.IMPLEMENTATION,
                message_type="approved_price_change",
                payload={
                    "product_id": decision.product_id,
                    "current_price": decision.current_price,
                    "new_price": decision.recommended_price,
                    "strategy": decision.strategy.value,
                    "confidence": decision.confidence,
                    "test_results": message.payload.get("test_results", {}),
                },
                priority=MessagePriority.HIGH,
            )
            await self.send_message(impl_message)
            del self._active_decisions[product_id]
        else:
            self.logger.info(
                f"Price change for {product_id} rejected by testing. "
                f"Reason: {message.payload.get('failure_reason', 'unknown')}"
            )
```

### 3.3 Pricing Engine Configuration

```python
PRICING_ENGINE_CONFIG = {
    "demand_model_path": "/models/demand_forecaster_v2.joblib",
    "default_strategy": "dynamic",
    "optimization_interval_seconds": 600,  # 10 minutes
    "min_confidence_threshold": 0.7,
    "max_price_change_pct": 15.0,
    "product_config": {
        "PROD-001": {
            "base_price": 49.99,
            "min_price": 34.99,
            "max_price": 79.99,
            "unit_cost": 25.00,
            "target_margin_pct": 35.0,
            "min_margin_pct": 15.0,
            "max_discount_pct": 25.0,
            "base_demand": 200,
            "price_elasticity": -1.8,
            "competitive_position": "match",
        },
        "PROD-002": {
            "base_price": 99.99,
            "min_price": 69.99,
            "max_price": 149.99,
            "unit_cost": 50.00,
            "target_margin_pct": 40.0,
            "min_margin_pct": 20.0,
            "max_discount_pct": 20.0,
            "base_demand": 150,
            "price_elasticity": -1.2,
            "competitive_position": "premium",
        },
    },
}
```

---

## 4. Testing Agent

### 4.1 Purpose

The Testing Agent validates pricing decisions before they are implemented. It runs A/B tests, simulates outcomes, and performs risk assessment to ensure price changes won't negatively impact revenue or customer satisfaction.

### 4.2 Implementation

```python
import asyncio
import random
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class TestType(Enum):
    SIMULATION = "simulation"
    A_B_TEST = "a_b_test"
    SHADOW = "shadow"
    CANARY = "canary"


class TestStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    ABORTED = "aborted"


@dataclass
class TestResult:
    """Result of a pricing test."""
    test_id: str
    test_type: TestType
    product_id: str
    control_price: float
    treatment_price: float
    status: TestStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    metrics: Dict[str, Any] = field(default_factory=dict)
    sample_size: int = 0
    confidence_level: float = 0.95
    p_value: Optional[float] = None
    recommendation: str = ""  # "implement", "reject", "extend_test"
    risk_score: float = 0.0  # 0-1, higher = riskier


class PricingSimulator:
    """Monte Carlo simulator for pricing outcomes."""

    def __init__(self, num_simulations: int = 10000):
        self.num_simulations = num_simulations

    def simulate(
        self,
        product_id: str,
        current_price: float,
        proposed_price: float,
        demand_forecast: Dict[str, Any],
        unit_cost: float,
    ) -> Dict[str, Any]:
        """
        Run Monte Carlo simulation of pricing outcomes.
        
        Returns distribution of outcomes for revenue, profit, and demand.
        """
        base_demand = demand_forecast.get("expected_demand", 100)
        demand_std = demand_forecast.get("demand_uncertainty", base_demand * 0.15)
        elasticity = demand_forecast.get("elasticity", -1.5)

        # Adjust demand for price change
        price_ratio = proposed_price / current_price
        adjusted_demand = base_demand * (price_ratio ** elasticity)

        # Run simulations
        revenues = []
        profits = []
        demands = []

        for _ in range(self.num_simulations):
            # Sample demand from normal distribution
            demand = max(0, random.gauss(adjusted_demand, demand_std))
            revenue = demand * proposed_price
            profit = demand * (proposed_price - unit_cost)

            revenues.append(revenue)
            profits.append(profit)
            demands.append(demand)

        # Calculate statistics
        current_revenue = base_demand * current_price
        current_profit = base_demand * (current_price - unit_cost)

        return {
            "revenue": {
                "mean": np.mean(revenues),
                "std": np.std(revenues),
                "p5": np.percentile(revenues, 5),
                "p95": np.percentile(revenues, 95),
                "prob_increase": sum(
                    1 for r in revenues if r > current_revenue
                ) / self.num_simulations,
            },
            "profit": {
                "mean": np.mean(profits),
                "std": np.std(profits),
                "p5": np.percentile(profits, 5),
                "p95": np.percentile(profits, 95),
                "prob_increase": sum(
                    1 for p in profits if p > current_profit
                ) / self.num_simulations,
            },
            "demand": {
                "mean": np.mean(demands),
                "std": np.std(demands),
                "p5": np.percentile(demands, 5),
                "p95": np.percentile(demands, 95),
            },
        }


class TestingAgent(BaseAgent):
    """
    Validates pricing decisions through simulation and testing.
    
    Responsibilities:
    - Run Monte Carlo simulations on proposed price changes
    - Execute A/B tests when appropriate
    - Perform risk assessment
    - Validate price changes against business rules
    - Approve or reject pricing decisions
    """

    def __init__(
        self,
        state_manager: SharedStateManager,
        config: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(AgentType.TESTING, state_manager, config)
        self.simulator = PricingSimulator(
            num_simulations=config.get("num_simulations", 10000)
        )
        self.min_sample_size: int = config.get("min_sample_size", 100)
        self.min_confidence_level: float = config.get(
            "min_confidence_level", 0.95
        )
        self.max_risk_score: float = config.get("max_risk_score", 0.3)
        self.simulation_threshold: float = config.get(
            "simulation_threshold", 0.8
        )
        self._active_tests: Dict[str, TestResult] = {}

        # Register handlers
        self.register_handler(
            "price_change_proposal", self._handle_price_change_proposal
        )

    async def on_start(self) -> None:
        """Initialize testing agent."""
        self._test_history: List[TestResult] = self.state_manager.get(
            "testing:history", []
        )
        self.logger.info("Testing Agent started")

    async def on_stop(self) -> None:
        """Persist test history."""
        self.state_manager.set("testing:history", self._test_history)

    async def _handle_price_change_proposal(
        self, message: AgentMessage
    ) -> None:
        """Handle a price change proposal from the pricing engine."""
        product_id = message.payload.get("product_id")
        current_price = message.payload.get("current_price")
        proposed_price = message.payload.get("proposed_price")
        confidence = message.payload.get("confidence", 0.0)

        self.logger.info(
            f"Evaluating price change for {product_id}: "
            f"${current_price:.2f} -> ${proposed_price:.2f}"
        )

        # Step 1: Run simulation
        simulation_result = await self._run_simulation(
            product_id, current_price, proposed_price, message.payload
        )

        # Step 2: Assess risk
        risk_score = self._assess_risk(
            product_id, current_price, proposed_price, simulation_result
        )

        # Step 3: Make decision
        if risk_score > self.max_risk_score:
            await self._reject_proposal(
                product_id,
                message.correlation_id,
                f"Risk score {risk_score:.2f} exceeds threshold "
                f"{self.max_risk_score:.2f}",
            )
            return

        # Step 4: Check if A/B test is needed
        if self._needs_ab_test(product_id, current_price, proposed_price):
            await self._run_ab_test(
                product_id, current_price, proposed_price, message
            )
        else:
            # Simulation passed, approve
            await self._approve_proposal(
                product_id,
                message.correlation_id,
                simulation_result,
                risk_score,
            )

    async def _run_simulation(
        self,
        product_id: str,
        current_price: float,
        proposed_price: float,
        proposal: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Run Monte Carlo simulation for a price change."""
        # Get product config
        product_config = self.state_manager.get(
            f"pricing:product_config:{product_id}", {}
        )
        unit_cost = product_config.get("unit_cost", current_price * 0.6)

        # Get demand forecast
        demand_forecast = {
            "expected_demand": product_config.get("base_demand", 100),
            "demand_uncertainty": product_config.get("base_demand", 100) * 0.15,
            "elasticity": product_config.get("price_elasticity", -1.5),
        }

        result = self.simulator.simulate(
            product_id,
            current_price,
            proposed_price,
            demand_forecast,
            unit_cost,
        )

        self.logger.info(
            f"Simulation for {product_id}: "
            f"Revenue increase probability: "
            f"{result['revenue']['prob_increase']:.2%}, "
            f"Profit increase probability: "
            f"{result['profit']['prob_increase']:.2%}"
        )

        return result

    def _assess_risk(
        self,
        product_id: str,
        current_price: float,
        proposed_price: float,
        simulation_result: Dict[str, Any],
    ) -> float:
        """Assess risk of a price change. Returns 0-1 score."""
        risk = 0.0

        # Price change magnitude
        price_change_pct = abs(proposed_price - current_price) / current_price
        risk += price_change_pct * 0.3  # Larger changes = riskier

        # Downside risk from simulation
        profit_p5 = simulation_result["profit"]["p5"]
        current_profit = simulation_result["profit"]["mean"]  # Approximate
        if profit_p5 < 0:
            risk += 0.3  # Risk of losses

        # Revenue at risk
        revenue_prob_decrease = 1 - simulation_result["revenue"]["prob_increase"]
        risk += revenue_prob_decrease * 0.2

        # Historical test performance for this product
        product_tests = [
            t for t in self._test_history
            if t.product_id == product_id and t.status == TestStatus.FAILED
        ]
        if product_tests:
            risk += min(0.2, len(product_tests) * 0.05)

        return min(1.0, risk)

    def _needs_ab_test(
        self, product_id: str, current_price: float, proposed_price: float
    ) -> bool:
        """Determine if an A/B test is needed."""
        price_change_pct = abs(proposed_price - current_price) / current_price

        # Always A/B test large changes
        if price_change_pct > 0.10:
            return True

        # A/B test if we haven't tested this product recently
        recent_tests = [
            t for t in self._test_history
            if t.product_id == product_id
            and t.start_time > datetime.utcnow() - timedelta(days=30)
        ]
        if not recent_tests:
            return True

        return False

    async def _run_ab_test(
        self,
        product_id: str,
        control_price: float,
        treatment_price: float,
        original_message: AgentMessage,
    ) -> None:
        """Run an A/B test for a price change."""
        test_id = str(uuid.uuid4())

        test_result = TestResult(
            test_id=test_id,
            test_type=TestType.A_B_TEST,
            product_id=product_id,
            control_price=control_price,
            treatment_price=treatment_price,
            status=TestStatus.RUNNING,
            start_time=datetime.utcnow(),
        )
        self._active_tests[test_id] = test_result

        self.logger.info(
            f"Started A/B test {test_id} for {product_id}: "
            f"control=${control_price:.2f}, treatment=${treatment_price:.2f}"
        )

        # In production, this would:
        # 1. Set up the test in the e-commerce platform
        # 2. Wait for sufficient sample size
        # 3. Analyze results
        # For now, simulate the test duration
        test_duration_hours = self.config.get("ab_test_duration_hours", 48)

        # Schedule test completion check
        asyncio.create_task(
            self._complete_ab_test(test_id, test_duration_hours)
        )

    async def _complete_ab_test(
        self, test_id: str, duration_hours: int
    ) -> None:
        """Complete an A/B test after the specified duration."""
        await asyncio.sleep(duration_hours * 3600)  # Convert to seconds

        test = self._active_tests.get(test_id)
        if not test or test.status != TestStatus.RUNNING:
            return

        # In production, fetch real test data from analytics
        # For now, simulate results
        test.end_time = datetime.utcnow()
        test.sample_size = random.randint(500, 5000)

        # Simulate test outcome
        control_conversion = random.uniform(0.02, 0.05)
        treatment_conversion = control_conversion * random.uniform(0.85, 1.15)

        control_revenue = test.control_price * control_conversion * test.sample_size / 2
        treatment_revenue = (
            test.treatment_price * treatment_conversion * test.sample_size / 2
        )

        # Calculate p-value (simplified)
        from scipy import stats

        # Simulate conversion data
        control_conversions = int(control_conversion * test.sample_size / 2)
        treatment_conversions = int(treatment_conversion * test.sample_size / 2)

        _, p_value = stats.chi2_contingency([
            [control_conversions, test.sample_size // 2 - control_conversions],
            [treatment_conversions, test.sample_size // 2 - treatment_conversions],
        ])

        test.p_value = p_value
        test.metrics = {
            "control_conversion_rate": control_conversion,
            "treatment_conversion_rate": treatment_conversion,
            "control_revenue": control_revenue,
            "treatment_revenue": treatment_revenue,
            "revenue_lift_pct": (
                (treatment_revenue - control_revenue) / control_revenue * 100
            ),
            "sample_size": test.sample_size,
        }

        if p_value < 0.05 and treatment_revenue > control_revenue:
            test.status = TestStatus.PASSED
            test.recommendation = "implement"
        else:
            test.status = TestStatus.FAILED
            test.recommendation = "reject"

        self._test_history.append(test)
        del self._active_tests[test_id]

        # Notify pricing engine
        await self._notify_pricing_engine(test)

    async def _notify_pricing_engine(
        self, test_result: TestResult
    ) -> None:
        """Send test result to the pricing optimization engine."""
        message = AgentMessage(
            source_agent=self.agent_type,
            target_agent=AgentType.PRICING_OPTIMIZATION,
            message_type="test_result",
            payload={
                "product_id": test_result.product_id,
                "test_passed": test_result.status == TestStatus.PASSED,
                "test_results": {
                    "test_id": test_result.test_id,
                    "test_type": test_result.test_type.value,
                    "metrics": test_result.metrics,
                    "p_value": test_result.p_value,
                    "recommendation": test_result.recommendation,
                },
                "failure_reason": (
                    "" if test_result.status == TestStatus.PASSED
                    else f"Test failed with p-value {test_result.p_value:.4f}"
                ),
            },
            priority=MessagePriority.HIGH,
        )
        await self.send_message(message)

    async def _approve_proposal(
        self,
        product_id: str,
        correlation_id: Optional[str],
        simulation_result: Dict[str, Any],
        risk_score: float,
    ) -> None:
        """Approve a price change proposal."""
        self.logger.info(f"Price change approved for {product_id}")

        message = AgentMessage(
            source_agent=self.agent_type,
            target_agent=AgentType.PRICING_OPTIMIZATION,
            message_type="test_result",
            payload={
                "product_id": product_id,
                "test_passed": True,
                "test_results": {
                    "test_type": "simulation",
                    "simulation_result": simulation_result,
                    "risk_score": risk_score,
                },
            },
            correlation_id=correlation_id,
            priority=MessagePriority.HIGH,
        )
        await self.send_message(message)

    async def _reject_proposal(
        self,
        product_id: str,
        correlation_id: Optional[str],
        reason: str,
    ) -> None:
        """Reject a price change proposal."""
        self.logger.warning(
            f"Price change rejected for {product_id}: {reason}"
        )

        message = AgentMessage(
            source_agent=self.agent_type,
            target_agent=AgentType.PRICING_OPTIMIZATION,
            message_type="test_result",
            payload={
                "product_id": product_id,
                "test_passed": False,
                "failure_reason": reason,
            },
            correlation_id=correlation_id,
            priority=MessagePriority.HIGH,
        )
        await self.send_message(message)
```

### 4.3 Testing Agent Configuration

```python
TESTING_AGENT_CONFIG = {
    "num_simulations": 10000,
    "min_sample_size": 100,
    "min_confidence_level": 0.95,
    "max_risk_score": 0.3,
    "simulation_threshold": 0.8,
    "ab_test_duration_hours": 48,
    "max_concurrent_tests": 5,
    "auto_approve_threshold": 0.9,  # Auto-approve if simulation confidence > 90%
    "risk_factors": {
        "price_change_magnitude": 0.3,
        "downside_risk": 0.3,
        "revenue_at_risk": 0.2,
        "historical_failures": 0.2,
    },
}
```

---

## 5. Implementation Agent

### 5.1 Purpose

The Implementation Agent is responsible for executing approved price changes across all sales channels. It handles the actual price updates, manages rollouts, and can trigger rollbacks if issues are detected.

### 5.2 Implementation

```python
import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ImplementationStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


@dataclass
class PriceChangeRecord:
    """Record of a price change implementation."""
    change_id: str
    product_id: str
    old_price: float
    new_price: float
    status: ImplementationStatus
    channels: List[str] = field(default_factory=list)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    rollback_reason: Optional[str] = None


class ChannelAdapter:
    """Base adapter for sales channel integrations."""

    def __init__(self, channel_name: str, config: Dict[str, Any]):
        self.channel_name = channel_name
        self.config = config

    async def update_price(
        self, product_id: str, new_price: float
    ) -> bool:
        """Update price on this channel. Override in subclasses."""
        raise NotImplementedError

    async def get_current_price(self, product_id: str) -> Optional[float]:
        """Get current price from this channel. Override in subclasses."""
        raise NotImplementedError

    async def rollback_price(
        self, product_id: str, previous_price: float
    ) -> bool:
        """Rollback price on this channel. Override in subclasses."""
        raise NotImplementedError


class ShopifyAdapter(ChannelAdapter):
    """Shopify e-commerce platform adapter."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__("shopify", config)
        self.shop_domain = config["shop_domain"]
        self.access_token = config["access_token"]
        self.api_version = config.get("api_version", "2024-01")

    async def update_price(
        self, product_id: str, new_price: float
    ) -> bool:
        """Update product price on Shopify."""
        import aiohttp

        url = (
            f"https://{self.shop_domain}/admin/api/{self.api_version}"
            f"/products/{product_id}.json"
        )
        headers = {
            "X-Shopify-Access-Token": self.access_token,
            "Content-Type": "application/json",
        }
        payload = {
            "product": {
                "id": product_id,
                "variants": [{"price": str(new_price)}],
            }
        }

        async with aiohttp.ClientSession() as session:
            async with session.put(
                url, json=payload, headers=headers
            ) as response:
                return response.status == 200

    async def get_current_price(self, product_id: str) -> Optional[float]:
        """Get current product price from Shopify."""
        import aiohttp

        url = (
            f"https://{self.shop_domain}/admin/api/{self.api_version}"
            f"/products/{product_id}.json"
        )
        headers = {"X-Shopify-Access-Token": self.access_token}

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    variant = data["product"]["variants"][0]
                    return float(variant["price"])
                return None

    async def rollback_price(
        self, product_id: str, previous_price: float
    ) -> bool:
        """Rollback price on Shopify."""
        return await self.update_price(product_id, previous_price)


class AmazonAdapter(ChannelAdapter):
    """Amazon Marketplace adapter."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__("amazon", config)
        self.marketplace_id = config["marketplace_id"]
        self.credentials = config["credentials"]

    async def update_price(
        self, product_id: str, new_price: float
    ) -> bool:
        """Update product price on Amazon."""
        # Amazon SP-API integration
        # This is a simplified example - real implementation would use
        # the Selling Partner API with proper authentication
        logger.info(
            f"Amazon: Updating price for {product_id} to ${new_price}"
        )
        return True

    async def get_current_price(self, product_id: str) -> Optional[float]:
        """Get current product price from Amazon."""
        return None

    async def rollback_price(
        self, product_id: str, previous_price: float
    ) -> bool:
        """Rollback price on Amazon."""
        return await self.update_price(product_id, previous_price)


class ImplementationAgent(BaseAgent):
    """
    Executes approved price changes across sales channels.
    
    Responsibilities:
    - Receive approved price changes from pricing engine
    - Execute price updates across all configured channels
    - Manage rollout strategy (canary, gradual, immediate)
    - Handle failures and rollbacks
    - Coordinate with monitoring agent for post-change validation
    """

    def __init__(
        self,
        state_manager: SharedStateManager,
        config: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(AgentType.IMPLEMENTATION, state_manager, config)
        self.channels: Dict[str, ChannelAdapter] = {}
        self._init_channels(config.get("channels", {}))
        self.rollout_strategy: str = config.get(
            "rollout_strategy", "canary"
        )
        self.rollout_duration_minutes: int = config.get(
            "rollout_duration_minutes", 30
        )
        self._pending_changes: Dict[str, PriceChangeRecord] = {}

        # Register handlers
        self.register_handler(
            "approved_price_change", self._handle_approved_price_change
        )
        self.register_handler("rollback_request", self._handle_rollback_request)

    def _init_channels(self, channel_configs: Dict[str, Dict]) -> None:
        """Initialize channel adapters."""
        for name, config in channel_configs.items():
            if name == "shopify":
                self.channels[name] = ShopifyAdapter(config)
            elif name == "amazon":
                self.channels[name] = AmazonAdapter(config)
            # Add more channel adapters as needed

    async def on_start(self) -> None:
        """Initialize implementation agent."""
        self._change_history: List[PriceChangeRecord] = (
            self.state_manager.get("implementation:history", [])
        )
        self.logger.info(
            f"Implementation Agent started with {len(self.channels)} channels"
        )

    async def on_stop(self) -> None:
        """Persist change history."""
        self.state_manager.set(
            "implementation:history", self._change_history
        )

    async def _handle_approved_price_change(
        self, message: AgentMessage
    ) -> None:
        """Handle an approved price change."""
        product_id = message.payload.get("product_id")
        current_price = message.payload.get("current_price")
        new_price = message.payload.get("new_price")

        change_id = str(uuid.uuid4())
        record = PriceChangeRecord(
            change_id=change_id,
            product_id=product_id,
            old_price=current_price,
            new_price=new_price,
            status=ImplementationStatus.PENDING,
            channels=list(self.channels.keys()),
        )
        self._pending_changes[change_id] = record

        self.logger.info(
            f"Implementing price change {change_id} for {product_id}: "
            f"${current_price:.2f} -> ${new_price:.2f}"
        )

        try:
            if self.rollout_strategy == "immediate":
                await self._execute_immediate(change_id, record)
            elif self.rollout_strategy == "canary":
                await self._execute_canary(change_id, record)
            elif self.rollout_strategy == "gradual":
                await self._execute_gradual(change_id, record)
            else:
                await self._execute_immediate(change_id, record)

        except Exception as e:
            self.logger.error(
                f"Implementation failed for {change_id}: {e}",
                exc_info=True,
            )
            record.status = ImplementationStatus.FAILED
            record.error_message = str(e)
            await self._rollback(change_id, record, str(e))

    async def _execute_immediate(
        self, change_id: str, record: PriceChangeRecord
    ) -> None:
        """Execute price change immediately across all channels."""
        record.status = ImplementationStatus.IN_PROGRESS
        record.started_at = datetime.utcnow()

        tasks = []
        for channel_name, adapter in self.channels.items():
            tasks.append(
                self._update_channel_with_retry(
                    channel_name, adapter, record
                )
            )

        results = await asyncio.gather(*tasks, return_exceptions=True)

        failures = [
            (name, result)
            for name, result in zip(self.channels.keys(), results)
            if isinstance(result, Exception) or result is False
        ]

        if failures:
            self.logger.error(
                f"Channel failures for {change_id}: {failures}"
            )
            record.status = ImplementationStatus.FAILED
            record.error_message = f"Failed on channels: {[f[0] for f in failures]}"
            await self._rollback(change_id, record, "Partial channel failure")
        else:
            record.status = ImplementationStatus.COMPLETED
            record.completed_at = datetime.utcnow()
            self._change_history.append(record)
            del self._pending_changes[change_id]

            # Notify monitoring agent
            await self._notify_monitoring(record)

    async def _execute_canary(
        self, change_id: str, record: PriceChangeRecord
    ) -> None:
        """Execute price change using canary rollout."""
        record.status = ImplementationStatus.IN_PROGRESS
        record.started_at = datetime.utcnow()

        # Phase 1: Update one channel first
        canary_channel = list(self.channels.keys())[0]
        canary_adapter = self.channels[canary_channel]

        success = await self._update_channel_with_retry(
            canary_channel, canary_adapter, record
        )

        if not success:
            record.status = ImplementationStatus.FAILED
            record.error_message = f"Canary failed on {canary_channel}"
            await self._rollback(change_id, record, "Canary failure")
            return

        # Wait and monitor
        self.logger.info(
            f"Canary deployed on {canary_channel}, waiting "
            f"{self.rollout_duration_minutes} minutes"
        )
        await asyncio.sleep(self.rollout_duration_minutes * 60)

        # Check if canary is healthy
        is_healthy = await self._check_canary_health(record)
        if not is_healthy:
            record.status = ImplementationStatus.FAILED
            record.error_message = "Canary health check failed"
            await self._rollback(
                change_id, record, "Canary health check failed"
            )
            return

        # Phase 2: Roll out to remaining channels
        remaining_channels = {
            name: adapter
            for name, adapter in self.channels.items()
            if name != canary_channel
        }

        tasks = [
            self._update_channel_with_retry(name, adapter, record)
            for name, adapter in remaining_channels.items()
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        failures = [
            name
            for name, result in zip(remaining_channels.keys(), results)
            if isinstance(result, Exception) or result is False
        ]

        if failures:
            record.status = ImplementationStatus.FAILED
            record.error_message = f"Failed on channels: {failures}"
            await self._rollback(
                change_id, record, "Partial rollout failure"
            )
        else:
            record.status = ImplementationStatus.COMPLETED
            record.completed_at = datetime.utcnow()
            self._change_history.append(record)
            del self._pending_changes[change_id]
            await self._notify_monitoring(record)

    async def _execute_gradual(
        self, change_id: str, record: PriceChangeRecord
    ) -> None:
        """Execute price change gradually across channels."""
        record.status = ImplementationStatus.IN_PROGRESS
        record.started_at = datetime.utcnow()

        for channel_name, adapter in self.channels.items():
            success = await self._update_channel_with_retry(
                channel_name, adapter, record
            )
            if not success:
                record.status = ImplementationStatus.FAILED
                record.error_message = f"Failed on {channel_name}"
                await self._rollback(
                    change_id, record, f"Failed on {channel_name}"
                )
                return

            # Wait between channels
            await asyncio.sleep(self.rollout_duration_minutes * 60)

        record.status = ImplementationStatus.COMPLETED
        record.completed_at = datetime.utcnow()
        self._change_history.append(record)
        del self._pending_changes[change_id]
        await self._notify_monitoring(record)

    async def _update_channel_with_retry(
        self,
        channel_name: str,
        adapter: ChannelAdapter,
        record: PriceChangeRecord,
        max_retries: int = 3,
    ) -> bool:
        """Update a channel with retry logic."""
        for attempt in range(max_retries):
            try:
                success = await adapter.update_price(
                    record.product_id, record.new_price
                )
                if success:
                    self.logger.info(
                        f"Updated {channel_name} for {record.product_id}"
                    )
                    return True
            except Exception as e:
                self.logger.warning(
                    f"Attempt {attempt + 1}/{max_retries} failed for "
                    f"{channel_name}: {e}"
                )
                await asyncio.sleep(2 ** attempt)  # Exponential backoff

        return False

    async def _check_canary_health(
        self, record: PriceChangeRecord
    ) -> bool:
        """Check if canary deployment is healthy."""
        # In production, check metrics like:
        # - Error rates
        # - Conversion rates
        # - Revenue impact
        # - Customer complaints
        await asyncio.sleep(5)  # Simulate health check
        return True

    async def _rollback(
        self,
        change_id: str,
        record: PriceChangeRecord,
        reason: str,
    ) -> None:
        """Rollback a price change."""
        self.logger.warning(
            f"Rolling back {change_id} for {record.product_id}: {reason}"
        )
        record.status = ImplementationStatus.ROLLED_BACK
        record.rollback_reason = reason

        tasks = [
            adapter.rollback_price(record.product_id, record.old_price)
            for adapter in self.channels.values()
        ]
        await asyncio.gather(*tasks, return_exceptions=True)

        self._change_history.append(record)
        if change_id in self._pending_changes:
            del self._pending_changes[change_id]

    async def _handle_rollback_request(
        self, message: AgentMessage
    ) -> None:
        """Handle a rollback request from monitoring."""
        product_id = message.payload.get("product_id")
        reason = message.payload.get("reason", "Monitoring alert")

        # Find pending change for this product
        for change_id, record in self._pending_changes.items():
            if record.product_id == product_id:
                await self._rollback(change_id, record, reason)
                break

    async def _notify_monitoring(
        self, record: PriceChangeRecord
    ) -> None:
        """Notify monitoring agent of completed price change."""
        message = AgentMessage(
            source_agent=self.agent_type,
            target_agent=AgentType.MONITORING,
            message_type="price_change_completed",
            payload={
                "change_id": record.change_id,
                "product_id": record.product_id,
                "old_price": record.old_price,
                "new_price": record.new_price,
                "channels": record.channels,
                "completed_at": record.completed_at.isoformat()
                if record.completed_at
                else None,
            },
            priority=MessagePriority.HIGH,
        )
        await self.send_message(message)
```

### 5.3 Implementation Agent Configuration

```python
IMPLEMENTATION_AGENT_CONFIG = {
    "rollout_strategy": "canary",  # "immediate", "canary", "gradual"
    "rollout_duration_minutes": 30,
    "max_retries": 3,
    "retry_backoff_base_seconds": 2,
    "channels": {
        "shopify": {
            "shop_domain": "your-store.myshopify.com",
            "access_token": "${SHOPIFY_ACCESS_TOKEN}",
            "api_version": "2024-01",
        },
        "amazon": {
            "marketplace_id": "ATVPDKIKX0DER",
            "credentials": {
                "client_id": "${AMAZON_CLIENT_ID}",
                "client_secret": "${AMAZON_CLIENT_SECRET}",
                "refresh_token": "${AMAZON_REFRESH_TOKEN}",
            },
        },
    },
}
```

---

## 6. Monitoring Agent

### 6.1 Purpose

The Monitoring Agent watches the performance of implemented price changes in real-time. It tracks key metrics, detects anomalies, and can trigger rollbacks if a price change performs poorly.

### 6.2 Implementation

```python
import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class MetricThreshold:
    """Threshold configuration for monitoring."""
    metric_name: str
    warning_threshold: float
    critical_threshold: float
    comparison: str = "below"  # "below", "above", "change_pct"


@dataclass
class MonitoringAlert:
    """A monitoring alert."""
    alert_id: str
    product_id: str
    metric_name: str
    severity: AlertSeverity
    message: str
    value: float
    threshold: float
    timestamp: datetime
    change_id: Optional[str] = None


class MonitoringAgent(BaseAgent):
    """
    Monitors price change performance and detects anomalies.
    
    Responsibilities:
    - Track KPIs after price changes (revenue, conversion, margin)
    - Detect anomalies in sales patterns
    - Trigger alerts for significant deviations
    - Request rollbacks for underperforming changes
    - Generate monitoring reports
    """

    def __init__(
        self,
        state_manager: SharedStateManager,
        config: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(AgentType.MONITORING, state_manager, config)
        self.check_interval_seconds: int = config.get(
            "check_interval_seconds", 60
        )
        self.metrics_window_minutes: int = config.get(
            "metrics_window_minutes", 30
        )
        self._active_monitors: Dict[str, Dict[str, Any]] = {}
        self._alert_history: List[MonitoringAlert] = []

        # Default thresholds
        self.thresholds: List[MetricThreshold] = [
            MetricThreshold("conversion_rate", 0.02, 0.015, "below"),
            MetricThreshold("revenue_per_session", 5.0, 3.0, "below"),
            MetricThreshold("profit_margin", 0.15, 0.10, "below"),
            MetricThreshold("cart_abandonment_rate", 0.70, 0.80, "above"),
            MetricThreshold("revenue_change_pct", -10.0, -20.0, "below"),
        ]

        # Register handlers
        self.register_handler(
            "price_change_completed", self._handle_price_change_completed
        )
        self.register_handler("metrics_report", self._handle_metrics_report)

    async def on_start(self) -> None:
        """Initialize monitoring agent."""
        self._alert_history = self.state_manager.get(
            "monitoring:alerts", []
        )
        self.logger.info("Monitoring Agent started")

    async def on_stop(self) -> None:
        """Persist alert history."""
        self.state_manager.set("monitoring:alerts", self._alert_history)

    async def _idle_tick(self) -> None:
        """Periodic monitoring check."""
        await self._check_all_monitors()
        await asyncio.sleep(self.check_interval_seconds)

    async def _handle_price_change_completed(
        self, message: AgentMessage
    ) -> None:
        """Start monitoring a completed price change."""
        product_id = message.payload.get("product_id")
        change_id = message.payload.get("change_id")
        old_price = message.payload.get("old_price")
        new_price = message.payload.get("new_price")

        self._active_monitors[change_id] = {
            "product_id": product_id,
            "old_price": old_price,
            "new_price": new_price,
            "started_at": datetime.utcnow(),
            "baseline_metrics": None,
            "alert_count": 0,
        }

        # Capture baseline metrics
        baseline = await self._capture_baseline_metrics(product_id)
        self._active_monitors[change_id]["baseline_metrics"] = baseline

        self.logger.info(
            f"Started monitoring price change {change_id} for {product_id}"
        )

    async def _capture_baseline_metrics(
        self, product_id: str
    ) -> Dict[str, float]:
        """Capture baseline metrics before price change."""
        # In production, fetch from analytics platform
        # For now, return simulated baseline
        return {
            "conversion_rate": 0.035,
            "revenue_per_session": 8.50,
            "profit_margin": 0.25,
            "cart_abandonment_rate": 0.65,
            "avg_order_value": 85.00,
            "units_sold_per_hour": 12.5,
        }

    async def _check_all_monitors(self) -> None:
        """Check all active monitors."""
        for change_id, monitor in list(self._active_monitors.items()):
            try:
                await self._check_monitor(change_id, monitor)
            except Exception as e:
                self.logger.error(
                    f"Error checking monitor {change_id}: {e}",
                    exc_info=True,
                )

    async def _check_monitor(
        self, change_id: str, monitor: Dict[str, Any]
    ) -> None:
        """Check a single price change monitor."""
        product_id = monitor["product_id"]
        baseline = monitor["baseline_metrics"]

        # Get current metrics
        current_metrics = await self._get_current_metrics(product_id)

        if not current_metrics:
            return

        # Check each threshold
        for threshold in self.thresholds:
            current_value = current_metrics.get(threshold.metric_name)
            if current_value is None:
                continue

            # Check critical threshold
            if self._is_breached(
                current_value, threshold.critical_threshold, threshold.comparison
            ):
                await self._trigger_alert(
                    change_id,
                    product_id,
                    threshold.metric_name,
                    AlertSeverity.CRITICAL,
                    current_value,
                    threshold.critical_threshold,
                )
                # Request rollback for critical breaches
                await self._request_rollback(
                    change_id,
                    product_id,
                    f"Critical: {threshold.metric_name} = {current_value:.4f} "
                    f"(threshold: {threshold.critical_threshold})",
                )
                return

            # Check warning threshold
            if self._is_breached(
                current_value, threshold.warning_threshold, threshold.comparison
            ):
                await self._trigger_alert(
                    change_id,
                    product_id,
                    threshold.metric_name,
                    AlertSeverity.WARNING,
                    current_value,
                    threshold.warning_threshold,
                )

        # Check if monitoring period has ended
        elapsed = datetime.utcnow() - monitor["started_at"]
        if elapsed > timedelta(hours=24):
            await self._finalize_monitor(change_id, monitor)

    def _is_breached(
        self, value: float, threshold: float, comparison: str
    ) -> bool:
        """Check if a value breaches a threshold."""
        if comparison == "below":
            return value < threshold
        elif comparison == "above":
            return value > threshold
        return False

    async def _get_current_metrics(
        self, product_id: str
    ) -> Optional[Dict[str, float]]:
        """Get current metrics for a product."""
        # In production, fetch from analytics database
        # For now, return simulated metrics
        return {
            "conversion_rate": random.uniform(0.025, 0.045),
            "revenue_per_session": random.uniform(6.0, 10.0),
            "profit_margin": random.uniform(0.18, 0.30),
            "cart_abandonment_rate": random.uniform(0.60, 0.75),
            "avg_order_value": random.uniform(75.0, 95.0),
            "units_sold_per_hour": random.uniform(10.0, 15.0),
        }

    async def _trigger_alert(
        self,
        change_id: str,
        product_id: str,
        metric_name: str,
        severity: AlertSeverity,
        value: float,
        threshold: float,
    ) -> None:
        """Trigger a monitoring alert."""
        alert = MonitoringAlert(
            alert_id=str(uuid.uuid4()),
            product_id=product_id,
            metric_name=metric_name,
            severity=severity,
            message=(
                f"{severity.value.upper()}: {metric_name} = {value:.4f} "
                f"(threshold: {threshold:.4f})"
            ),
            value=value,
            threshold=threshold,
            timestamp=datetime.utcnow(),
            change_id=change_id,
        )
        self._alert_history.append(alert)

        self.logger.warning(alert.message)

        # Notify performance analytics agent
        message = AgentMessage(
            source_agent=self.agent_type,
            target_agent=AgentType.PERFORMANCE_ANALYTICS,
            message_type="monitoring_alert",
            payload={
                "alert_id": alert.alert_id,
                "product_id": product_id,
                "metric_name": metric_name,
                "severity": severity.value,
                "value": value,
                "threshold": threshold,
                "change_id": change_id,
            },
            priority=MessagePriority.HIGH
            if severity == AlertSeverity.CRITICAL
            else MessagePriority.MEDIUM,
        )
        await self.send_message(message)

    async def _request_rollback(
        self, change_id: str, product_id: str, reason: str
    ) -> None:
        """Request a rollback from the implementation agent."""
        self.logger.critical(
            f"Requesting rollback for {change_id}: {reason}"
        )

        message = AgentMessage(
            source_agent=self.agent_type,
            target_agent=AgentType.IMPLEMENTATION,
            message_type="rollback_request",
            payload={
                "change_id": change_id,
                "product_id": product_id,
                "reason": reason,
            },
            priority=MessagePriority.CRITICAL,
        )
        await self.send_message(message)

    async def _finalize_monitor(
        self, change_id: str, monitor: Dict[str, Any]
    ) -> None:
        """Finalize monitoring for a price change."""
        self.logger.info(
            f"Finalizing monitoring for change {change_id}"
        )

        # Generate summary report
        product_id = monitor["product_id"]
        final_metrics = await self._get_current_metrics(product_id)
        baseline = monitor["baseline_metrics"]

        summary = {
            "change_id": change_id,
            "product_id": product_id,
            "old_price": monitor["old_price"],
            "new_price": monitor["new_price"],
            "duration_hours": 24,
            "baseline_metrics": baseline,
            "final_metrics": final_metrics,
            "alert_count": monitor["alert_count"],
            "metric_changes": {
                key: {
                    "absolute": final_metrics.get(key, 0) - baseline.get(key, 0),
                    "pct_change": (
                        (final_metrics.get(key, 0) - baseline.get(key, 0))
                        / max(abs(baseline.get(key, 1)), 0.001)
                        * 100
                    ),
                }
                for key in baseline
            },
        }

        # Send to performance analytics
        message = AgentMessage(
            source_agent=self.agent_type,
            target_agent=AgentType.PERFORMANCE_ANALYTICS,
            message_type="monitoring_summary",
            payload=summary,
            priority=MessagePriority.MEDIUM,
        )
        await self.send_message(message)

        # Remove from active monitors
        if change_id in self._active_monitors:
            del self._active_monitors[change_id]

    async def _handle_metrics_report(
        self, message: AgentMessage
    ) -> None:
        """Handle incoming metrics reports."""
        # Process external metrics reports
        pass
```

### 6.3 Monitoring Agent Configuration

```python
MONITORING_AGENT_CONFIG = {
    "check_interval_seconds": 60,
    "metrics_window_minutes": 30,
    "monitoring_duration_hours": 24,
    "thresholds": [
        {
            "metric_name": "conversion_rate",
            "warning_threshold": 0.02,
            "critical_threshold": 0.015,
            "comparison": "below",
        },
        {
            "metric_name": "revenue_per_session",
            "warning_threshold": 5.0,
            "critical_threshold": 3.0,
            "comparison": "below",
        },
        {
            "metric_name": "profit_margin",
            "warning_threshold": 0.15,
            "critical_threshold": 0.10,
            "comparison": "below",
        },
        {
            "metric_name": "cart_abandonment_rate",
            "warning_threshold": 0.70,
            "critical_threshold": 0.80,
            "comparison": "above",
        },
        {
            "metric_name": "revenue_change_pct",
            "warning_threshold": -10.0,
            "critical_threshold": -20.0,
            "comparison": "below",
        },
    ],
}
```

---

## 7. Performance Analytics Agent

### 7.1 Purpose

The Performance Analytics Agent aggregates data from all other agents to provide comprehensive performance reporting, ROI analysis, and strategic insights. It answers questions like "How much additional revenue did pricing optimization generate?" and "Which strategies work best?"

### 7.2 Implementation

```python
import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


@dataclass
class PerformanceReport:
    """Comprehensive performance report."""
    report_id: str
    start_date: datetime
    end_date: datetime
    total_products: int
    total_price_changes: int
    successful_changes: int
    rolled_back_changes: int
    total_revenue_impact: float
    total_profit_impact: float
    avg_confidence_score: float
    strategy_performance: Dict[str, Dict[str, float]]
    product_performance: Dict[str, Dict[str, float]]
    insights: List[str] = field(default_factory=list)


class PerformanceAnalyticsAgent(BaseAgent):
    """
    Aggregates and analyzes pricing performance data.
    
    Responsibilities:
    - Aggregate data from all agents
    - Calculate ROI of pricing optimization
    - Generate performance reports
    - Identify best-performing strategies
    - Provide strategic recommendations
    - Track long-term trends
    """

    def __init__(
        self,
        state_manager: SharedStateManager,
        config: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            AgentType.PERFORMANCE_ANALYTICS, state_manager, config
        )
        self.report_interval_hours: int = config.get(
            "report_interval_hours", 24
        )
        self._price_change_data: List[Dict[str, Any]] = []
        self._monitoring_summaries: List[Dict[str, Any]] = []
        self._alerts: List[Dict[str, Any]] = []

        # Register handlers
        self.register_handler(
            "monitoring_summary", self._handle_monitoring_summary
        )
        self.register_handler("monitoring_alert", self._handle_monitoring_alert)
        self.register_handler(
            "price_change_completed", self._handle_price_change_completed
        )
        self.register_handler(
            "report_request", self._handle_report_request
        )

    async def on_start(self) -> None:
        """Initialize analytics agent."""
        self._price_change_data = self.state_manager.get(
            "analytics:price_changes", []
        )
        self._monitoring_summaries = self.state_manager.get(
            "analytics:monitoring_summaries", []
        )
        self.logger.info("Performance Analytics Agent started")

    async def on_stop(self) -> None:
        """Persist analytics data."""
        self.state_manager.set(
            "analytics:price_changes", self._price_change_data
        )
        self.state_manager.set(
            "analytics:monitoring_summaries", self._monitoring_summaries
        )

    async def _idle_tick(self) -> None:
        """Periodic report generation."""
        await self._generate_scheduled_report()
        await asyncio.sleep(self.report_interval_hours * 3600)

    async def _handle_monitoring_summary(
        self, message: AgentMessage
    ) -> None:
        """Handle monitoring summary from monitoring agent."""
        self._monitoring_summaries.append(message.payload)
        self.logger.info(
            f"Received monitoring summary for "
            f"{message.payload.get('product_id')}"
        )

    async def _handle_monitoring_alert(
        self, message: AgentMessage
    ) -> None:
        """Handle monitoring alert."""
        self._alerts.append(message.payload)

    async def _handle_price_change_completed(
        self, message: AgentMessage
    ) -> None:
        """Handle price change completion notification."""
        self._price_change_data.append({
            "change_id": message.payload.get("change_id"),
            "product_id": message.payload.get("product_id"),
            "old_price": message.payload.get("old_price"),
            "new_price": message.payload.get("new_price"),
            "completed_at": message.payload.get("completed_at"),
            "channels": message.payload.get("channels", []),
        })

    async def _handle_report_request(
        self, message: AgentMessage
    ) -> None:
        """Handle a report request."""
        report_type = message.payload.get("report_type", "daily")
        product_id = message.payload.get("product_id")

        if report_type == "daily":
            report = await self.generate_daily_report(product_id)
        elif report_type == "weekly":
            report = await self.generate_weekly_report(product_id)
        elif report_type == "strategy":
            report = await self.generate_strategy_report()
        else:
            report = await self.generate_daily_report(product_id)

        response = AgentMessage(
            source_agent=self.agent_type,
            target_agent=message.source_agent,
            message_type="report_response",
            payload={"report": report.__dict__ if hasattr(report, '__dict__') else report},
            correlation_id=message.correlation_id,
        )
        await self.send_message(response)

    async def generate_daily_report(
        self, product_id: Optional[str] = None
    ) -> PerformanceReport:
        """Generate a daily performance report."""
        today = datetime.utcnow().date()
        start = datetime.combine(today, datetime.min.time())
        end = start + timedelta(days=1)

        # Filter data for the report period
        changes = [
            c for c in self._price_change_data
            if start <= datetime.fromisoformat(c["completed_at"]) < end
            and (product_id is None or c["product_id"] == product_id)
        ]

        summaries = [
            s for s in self._monitoring_summaries
            if start <= datetime.fromisoformat(
                s.get("completed_at", s.get("started_at", "2000-01-01"))
            ) < end
            and (product_id is None or s["product_id"] == product_id)
        ]

        # Calculate metrics
        total_revenue_impact = 0.0
        total_profit_impact = 0.0
        strategy_performance = defaultdict(lambda: {
            "count": 0,
            "avg_revenue_change": 0.0,
            "avg_profit_change": 0.0,
            "success_rate": 0.0,
        })

        for summary in summaries:
            changes_data = summary.get("metric_changes", {})
            revenue_change = changes_data.get("revenue_per_session", {})
            profit_change = changes_data.get("profit_margin", {})

            total_revenue_impact += revenue_change.get("absolute", 0)
            total_profit_impact += profit_change.get("absolute", 0)

        # Generate insights
        insights = self._generate_insights(changes, summaries)

        return PerformanceReport(
            report_id=str(uuid.uuid4()),
            start_date=start,
            end_date=end,
            total_products=len(set(c["product_id"] for c in changes)),
            total_price_changes=len(changes),
            successful_changes=len([
                s for s in summaries if s.get("alert_count", 0) == 0
            ]),
            rolled_back_changes=len([
                s for s in summaries if s.get("alert_count", 0) > 2
            ]),
            total_revenue_impact=total_revenue_impact,
            total_profit_impact=total_profit_impact,
            avg_confidence_score=0.85,  # Calculate from actual data
            strategy_performance=dict(strategy_performance),
            product_performance={},
            insights=insights,
        )

    async def generate_weekly_report(
        self, product_id: Optional[str] = None
    ) -> PerformanceReport:
        """Generate a weekly performance report."""
        today = datetime.utcnow().date()
        start = datetime.combine(
            today - timedelta(days=today.weekday()), datetime.min.time()
        )
        end = start + timedelta(weeks=1)

        # Similar to daily but with weekly aggregation
        # Implementation omitted for brevity
        return await self.generate_daily_report(product_id)

    async def generate_strategy_report(self) -> Dict[str, Any]:
        """Generate strategy comparison report."""
        strategy_stats = defaultdict(lambda: {
            "total_changes": 0,
            "successful_changes": 0,
            "total_revenue_impact": 0.0,
            "total_profit_impact": 0.0,
            "avg_confidence": 0.0,
        })

        for change in self._price_change_data:
            strategy = change.get("strategy", "unknown")
            strategy_stats[strategy]["total_changes"] += 1

        for summary in self._monitoring_summaries:
            strategy = summary.get("strategy", "unknown")
            metrics = summary.get("metric_changes", {})
            strategy_stats[strategy]["total_revenue_impact"] += metrics.get(
                "revenue_per_session", {}
            ).get("absolute", 0)
            strategy_stats[strategy]["total_profit_impact"] += metrics.get(
                "profit_margin", {}
            ).get("absolute", 0)

        # Calculate success rates and averages
        for strategy, stats in strategy_stats.items():
            if stats["total_changes"] > 0:
                stats["success_rate"] = (
                    stats["successful_changes"] / stats["total_changes"]
                )

        return {
            "report_type": "strategy_comparison",
            "generated_at": datetime.utcnow().isoformat(),
            "strategy_performance": dict(strategy_stats),
        }

    def _generate_insights(
        self,
        changes: List[Dict[str, Any]],
        summaries: List[Dict[str, Any]],
    ) -> List[str]:
        """Generate actionable insights from the data."""
        insights = []

        if not changes:
            insights.append("No price changes were implemented during this period.")
            return insights

        # Analyze success rate
        total = len(changes)
        successful = len([s for s in summaries if s.get("alert_count", 0) == 0])
        success_rate = successful / max(total, 1)

        if success_rate > 0.9:
            insights.append(
                f"Excellent success rate: {success_rate:.1%} of price "
                f"changes performed well."
            )
        elif success_rate > 0.7:
            insights.append(
                f"Good success rate: {success_rate:.1%} of price "
                f"changes performed well."
            )
        else:
            insights.append(
                f"Low success rate: {success_rate:.1%}. Consider "
                f"adjusting pricing strategy thresholds."
            )

        # Analyze revenue impact
        total_revenue = sum(
            s.get("metric_changes", {})
            .get("revenue_per_session", {})
            .get("absolute", 0)
            for s in summaries
        )
        if total_revenue > 0:
            insights.append(
                f"Price optimization generated ${total_revenue:,.2f} "
                f"in additional revenue."
            )
        elif total_revenue < 0:
            insights.append(
                f"Price optimization resulted in ${abs(total_revenue):,.2f} "
                f"revenue decline. Review strategy."
            )

        # Product-specific insights
        product_changes = defaultdict(int)
        for c in changes:
            product_changes[c["product_id"]] += 1

        most_active = max(product_changes, key=product_changes.get)
        insights.append(
            f"Most actively priced product: {most_active} "
            f"({product_changes[most_active]} changes)"
        )

        return insights

    async def _generate_scheduled_report(self) -> None:
        """Generate and store a scheduled report."""
        report = await self.generate_daily_report()
        self.state_manager.set(
            f"analytics:reports:daily:{datetime.utcnow().date().isoformat()}",
            report.__dict__ if hasattr(report, "__dict__") else report,
        )
        self.logger.info(
            f"Generated daily report: {report.report_id}"
        )
```

### 7.3 Performance Analytics Configuration

```python
PERFORMANCE_ANALYTICS_CONFIG = {
    "report_interval_hours": 24,
    "retention_days": 90,
    "metrics_to_track": [
        "revenue_impact",
        "profit_impact",
        "conversion_rate_change",
        "customer_satisfaction",
        "market_share_change",
    ],
    "insight_generation": {
        "enabled": True,
        "min_data_points": 10,
        "confidence_threshold": 0.8,
    },
    "alert_correlation": {
        "enabled": True,
        "time_window_hours": 24,
    },
}
```

---

## 8. Code Examples and Snippets

### 8.1 System Orchestration

```python
# main.py - System orchestration
import asyncio
import logging
from typing import List

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def run_pricing_optimization_system():
    """Start and run the complete pricing optimization system."""
    # Initialize shared state
    state_manager = SharedStateManager(
        redis_url="redis://localhost:6379/0"
    )

    # Initialize all agents
    agents = [
        MarketIntelligenceAgent(state_manager, MARKET_INTELLIGENCE_CONFIG),
        PricingOptimizationEngine(state_manager, PRICING_ENGINE_CONFIG),
        TestingAgent(state_manager, TESTING_AGENT_CONFIG),
        ImplementationAgent(state_manager, IMPLEMENTATION_AGENT_CONFIG),
        MonitoringAgent(state_manager, MONITORING_AGENT_CONFIG),
        PerformanceAnalyticsAgent(state_manager, PERFORMANCE_ANALYTICS_CONFIG),
    ]

    # Start all agents
    tasks = [asyncio.create_task(agent.start()) for agent in agents]

    try:
        # Run indefinitely
        await asyncio.gather(*tasks)
    except KeyboardInterrupt:
        logger.info("Shutting down pricing optimization system...")
    finally:
        # Stop all agents
        for agent in agents:
            await agent.stop()
        # Cancel tasks
        for task in tasks:
            task.cancel()


if __name__ == "__main__":
    asyncio.run(run_pricing_optimization_system())
```

### 8.2 Docker Compose Setup

```yaml
# docker-compose.yml
version: "3.8"

services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes

  pricing-optimization:
    build:
      context: .
      dockerfile: Dockerfile
    depends_on:
      - redis
      - postgres
    environment:
      - REDIS_URL=redis://redis:6379/0
      - DATABASE_URL=postgresql://postgres:postgres@postgres:5432/pricing
      - LOG_LEVEL=INFO
    volumes:
      - ./models:/app/models
      - ./config:/app/config
    restart: unless-stopped

  postgres:
    image: postgres:16-alpine
    environment:
      - POSTGRES_DB=pricing
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana

volumes:
  redis_data:
  postgres_data:
  grafana_data:
```

### 8.3 Dockerfile

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directories for models and config
RUN mkdir -p /app/models /app/config

# Run the application
CMD ["python", "main.py"]
```

### 8.4 Requirements File

```text
# requirements.txt
langchain>=0.1.0
langchain-core>=0.1.0
langchain-community>=0.0.10
openai>=1.0.0
redis>=5.0.0
aiohttp>=3.9.0
numpy>=1.24.0
pandas>=2.0.0
scipy>=1.11.0
scikit-learn>=1.3.0
joblib>=1.3.0
psycopg2-binary>=2.9.0
pydantic>=2.0.0
python-dotenv>=1.0.0
pyyaml>=6.0.0
pytest>=7.4.0
pytest-asyncio>=0.21.0
```

### 8.5 Environment Configuration

```bash
# .env
REDIS_URL=redis://localhost:6379/0
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/pricing

# API Keys
OPENAI_API_KEY=sk-...
GOOGLE_TRENDS_API_KEY=...

# Channel Credentials
SHOPIFY_ACCESS_TOKEN=shpat_...
AMAZON_CLIENT_ID=...
AMAZON_CLIENT_SECRET=...
AMAZON_REFRESH_TOKEN=...

# Model Paths
DEMAND_MODEL_PATH=/models/demand_forecaster_v2.joblib

# Logging
LOG_LEVEL=INFO
```

### 8.6 LangChain DeepAgents Integration

```python
# langchain_integration.py
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from typing import Any, Dict, List


@tool
def get_competitor_prices(product_id: str) -> Dict[str, Any]:
    """Get current competitor prices for a product."""
    # Implementation would fetch from market intelligence agent
    pass


@tool
def get_demand_forecast(product_id: str, price: float) -> Dict[str, Any]:
    """Get demand forecast for a product at a given price."""
    # Implementation would use the demand forecaster
    pass


@tool
def submit_price_change(
    product_id: str, new_price: float, reason: str
) -> Dict[str, Any]:
    """Submit a price change for testing and approval."""
    # Implementation would send to testing agent
    pass


@tool
def get_pricing_performance(
    product_id: str, days: int = 7
) -> Dict[str, Any]:
    """Get pricing performance metrics for a product."""
    # Implementation would fetch from analytics agent
    pass


def create_pricing_agent_llm() -> AgentExecutor:
    """Create a LangChain agent for pricing decisions."""
    llm = ChatOpenAI(model="gpt-4", temperature=0)

    tools = [
        get_competitor_prices,
        get_demand_forecast,
        submit_price_change,
        get_pricing_performance,
    ]

    prompt = ChatPromptTemplate.from_messages([
        (
            "system",
            "You are an AI pricing optimization assistant. "
            "You help analyze market conditions, forecast demand, "
            "and recommend optimal prices. Always consider business "
            "constraints and explain your reasoning.",
        ),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    agent = create_openai_functions_agent(llm, tools, prompt)
    return AgentExecutor(agent=agent, tools=tools, verbose=True)
```

### 8.7 FastAPI Endpoint

```python
# api.py
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Any, Dict, List, Optional
import asyncio

app = FastAPI(title="Pricing Optimization API", version="1.0.0")


class PricingRequest(BaseModel):
    product_id: str
    context: Optional[Dict[str, Any]] = None


class PricingResponse(BaseModel):
    product_id: str
    current_price: float
    recommended_price: float
    strategy: str
    confidence: float
    expected_impact: Dict[str, float]
    reasoning: List[str]


class PriceChangeRequest(BaseModel):
    product_id: str
    new_price: float
    reason: str


# Global reference to the pricing engine
pricing_engine: Optional[PricingOptimizationEngine] = None


@app.on_event("startup")
async def startup_event():
    """Initialize the pricing system on startup."""
    global pricing_engine
    state_manager = SharedStateManager()
    pricing_engine = PricingOptimizationEngine(
        state_manager, PRICING_ENGINE_CONFIG
    )
    asyncio.create_task(pricing_engine.start())


@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown the pricing system."""
    if pricing_engine:
        await pricing_engine.stop()


@app.post("/api/v1/pricing/optimize", response_model=PricingResponse)
async def optimize_price(request: PricingRequest):
    """Get optimal price recommendation for a product."""
    if not pricing_engine:
        raise HTTPException(status_code=503, detail="Service not ready")

    decision = await pricing_engine._optimize_product_price(
        request.product_id
    )
    if not decision:
        raise HTTPException(
            status_code=404,
            detail=f"Could not optimize price for {request.product_id}",
        )

    return PricingResponse(
        product_id=decision.product_id,
        current_price=decision.current_price,
        recommended_price=decision.recommended_price,
        strategy=decision.strategy.value,
        confidence=decision.confidence,
        expected_impact={
            "demand_change_pct": decision.expected_demand_change_pct,
            "revenue_change_pct": decision.expected_revenue_change_pct,
            "profit_change_pct": decision.expected_profit_change_pct,
        },
        reasoning=decision.reasoning,
    )


@app.post("/api/v1/pricing/change")
async def request_price_change(request: PriceChangeRequest):
    """Request a price change."""
    if not pricing_engine:
        raise HTTPException(status_code=503, detail="Service not ready")

    # Send price change request to the system
    message = AgentMessage(
        source_agent=AgentType.PRICING_OPTIMIZATION,
        target_agent=AgentType.TESTING,
        message_type="price_change_proposal",
        payload={
            "product_id": request.product_id,
            "proposed_price": request.new_price,
            "reason": request.reason,
        },
    )
    await pricing_engine.send_message(message)

    return {"status": "submitted", "message": "Price change request submitted for testing"}


@app.get("/api/v1/analytics/performance")
async def get_performance(
    product_id: Optional[str] = None, days: int = 7
):
    """Get pricing performance analytics."""
    # Implementation would fetch from analytics agent
    return {"product_id": product_id, "days": days, "metrics": {}}


@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "agents": {
            "pricing_engine": pricing_engine is not None,
        },
    }
```

---

## 9. Testing Strategy

### 9.1 Unit Tests

```python
# tests/test_pricing_engine.py
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime


@pytest_asyncio.fixture
async def state_manager():
    """Create a mock state manager for testing."""
    manager = MagicMock()
    manager.get = MagicMock(return_value={})
    manager.set = MagicMock()
    manager.publish = MagicMock()
    return manager


@pytest_asyncio.fixture
async def pricing_engine(state_manager):
    """Create a pricing engine for testing."""
    config = {
        "product_config": {
            "PROD-001": {
                "base_price": 49.99,
                "min_price": 34.99,
                "max_price": 79.99,
                "unit_cost": 25.00,
                "target_margin_pct": 35.0,
                "min_margin_pct": 15.0,
                "max_discount_pct": 25.0,
                "base_demand": 200,
                "price_elasticity": -1.8,
                "competitive_position": "match",
            }
        },
        "min_confidence_threshold": 0.7,
        "max_price_change_pct": 15.0,
    }
    engine = PricingOptimizationEngine(state_manager, config)
    await engine.on_start()
    yield engine
    await engine.on_stop()


@pytest.mark.asyncio
async def test_optimize_product_price_returns_decision(pricing_engine):
    """Test that price optimization returns a valid decision."""
    decision = await pricing_engine._optimize_product_price("PROD-001")

    assert decision is not None
    assert decision.product_id == "PROD-001"
    assert decision.recommended_price > 0
    assert decision.confidence >= 0.0
    assert decision.confidence <= 1.0
    assert decision.strategy in PricingStrategy


@pytest.mark.asyncio
async def test_price_constraints_are_applied(pricing_engine):
    """Test that business constraints are applied to pricing decisions."""
    decision = await pricing_engine._optimize_product_price("PROD-001")

    config = pricing_engine.product_config["PROD-001"]
    assert decision.recommended_price >= config["min_price"]
    assert decision.recommended_price <= config["max_price"]

    # Check margin constraint
    margin = (
        (decision.recommended_price - config["unit_cost"])
        / decision.recommended_price
        * 100
    )
    assert margin >= config["min_margin_pct"]


@pytest.mark.asyncio
async def test_max_price_change_cap(pricing_engine):
    """Test that price changes are capped at the maximum allowed."""
    # Set a very low current price to force a large change
    pricing_engine._current_prices["PROD-001"] = 10.00

    decision = await pricing_engine._optimize_product_price("PROD-001")

    max_change = 10.00 * (pricing_engine.max_price_change_pct / 100)
    assert abs(decision.recommended_price - 10.00) <= max_change + 0.01


@pytest.mark.asyncio
async def test_demand_forecaster_fallback(state_manager):
    """Test demand forecaster fallback when no model is loaded."""
    forecaster = DemandForecaster(model_path=None)

    result = forecaster.forecast(
        "PROD-001",
        50.0,
        {
            "base_demand": 100,
            "price_elasticity": -1.5,
            "reference_price": 45.0,
        },
    )

    assert result["expected_demand"] > 0
    assert result["demand_uncertainty"] > 0
    assert result["elasticity"] == -1.5


@pytest.mark.asyncio
async def test_market_signal_triggers_reoptimization(pricing_engine):
    """Test that market signals trigger re-optimization."""
    signal = AgentMessage(
        source_agent=AgentType.MARKET_INTELLIGENCE,
        target_agent=AgentType.PRICING_OPTIMIZATION,
        message_type="market_signal",
        payload={
            "signal_type": "competitor_price_change",
            "product_id": "PROD-001",
            "value": {
                "old_price": 49.99,
                "new_price": 44.99,
                "change_pct": -10.0,
                "competitor_id": "competitor_a",
            },
            "confidence": 0.9,
        },
    )

    with patch.object(
        pricing_engine, "_optimize_product_price", new_callable=AsyncMock
    ) as mock_optimize:
        mock_optimize.return_value = MagicMock(
            product_id="PROD-001",
            recommended_price=44.99,
            confidence=0.85,
            expected_profit_change_pct=5.0,
        )
        with patch.object(
            pricing_engine, "_propose_price_change", new_callable=AsyncMock
        ) as mock_propose:
            await pricing_engine._handle_market_signal(signal)
            mock_optimize.assert_called_once_with("PROD-001")
            mock_propose.assert_called_once()
```

### 9.2 Integration Tests

```python
# tests/test_integration.py
import pytest
import pytest_asyncio
import asyncio
from unittest.mock import MagicMock


@pytest.mark.asyncio
async def test_full_pricing_workflow():
    """Test the complete pricing workflow from signal to implementation."""
    # This test verifies the entire pipeline:
    # Market Signal -> Pricing Engine -> Testing Agent -> Implementation

    state_manager = MagicMock()
    state_manager.get = MagicMock(return_value={})
    state_manager.set = MagicMock()
    state_manager.publish = MagicMock()

    # Create agents
    pricing_engine = PricingOptimizationEngine(state_manager, {
        "product_config": {
            "PROD-001": {
                "base_price": 49.99,
                "min_price": 34.99,
                "max_price": 79.99,
                "unit_cost": 25.00,
                "target_margin_pct": 35.0,
                "min_margin_pct": 15.0,
                "max_discount_pct": 25.0,
                "base_demand": 200,
                "price_elasticity": -1.8,
            }
        },
        "min_confidence_threshold": 0.5,
        "max_price_change_pct": 20.0,
    })

    testing_agent = TestingAgent(state_manager, {
        "num_simulations": 1000,
        "max_risk_score": 0.5,
    })

    await pricing_engine.on_start()
    await testing_agent.on_start()

    # Simulate a market signal
    signal = AgentMessage(
        source_agent=AgentType.MARKET_INTELLIGENCE,
        target_agent=AgentType.PRICING_OPTIMIZATION,
        message_type="market_signal",
        payload={
            "signal_type": "competitor_price_change",
            "product_id": "PROD-001",
            "value": {"change_pct": -5.0},
            "confidence": 0.9,
        },
    )

    # Process the signal
    await pricing_engine._handle_market_signal(signal)

    # Verify that a price change was proposed
    # (In a real test, you'd capture the message sent to testing agent)

    await pricing_engine.on_stop()
    await testing_agent.on_stop()


@pytest.mark.asyncio
async def test_agent_communication():
    """Test that agents can send and receive messages."""
    state_manager = MagicMock()
    published_messages = []

    def capture_publish(channel, message):
        published_messages.append((channel, message))

    state_manager.publish = capture_publish

    agent1 = MarketIntelligenceAgent(state_manager, {})
    agent2 = PricingOptimizationEngine(state_manager, {})

    await agent1.on_start()
    await agent2.on_start()

    # Send a message from agent1 to agent2
    message = AgentMessage(
        source_agent=AgentType.MARKET_INTELLIGENCE,
        target_agent=AgentType.PRICING_OPTIMIZATION,
        message_type="test_message",
        payload={"key": "value"},
    )
    await agent1.send_message(message)

    # Verify the message was published
    assert len(published_messages) == 1
    channel, msg = published_messages[0]
    assert channel == "agent:pricing_optimization"
    assert msg["message_type"] == "test_message"

    await agent1.on_stop()
    await agent2.on_stop()
```

### 9.3 Load Testing

```python
# tests/test_load.py
import pytest
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor


@pytest.mark.asyncio
async def test_pricing_engine_throughput():
    """Test pricing engine can handle high throughput."""
    state_manager = MagicMock()
    state_manager.get = MagicMock(return_value={})
    state_manager.set = MagicMock()

    engine = PricingOptimizationEngine(state_manager, {
        "product_config": {
            f"PROD-{i:03d}": {
                "base_price": 49.99,
                "min_price": 34.99,
                "max_price": 79.99,
                "unit_cost": 25.00,
                "target_margin_pct": 35.0,
                "min_margin_pct": 15.0,
                "base_demand": 200,
                "price_elasticity": -1.8,
            }
            for i in range(100)
        },
        "min_confidence_threshold": 0.5,
    })

    await engine.on_start()

    start_time = time.time()
    tasks = [
        engine._optimize_product_price(f"PROD-{i:03d}")
        for i in range(100)
    ]
    results = await asyncio.gather(*tasks)
    elapsed = time.time() - start_time

    # Should optimize 100 products in under 10 seconds
    assert elapsed < 10.0
    assert len([r for r in results if r is not None]) >= 90

    await engine.on_stop()


@pytest.mark.asyncio
async def test_simulation_performance():
    """Test Monte Carlo simulation performance."""
    simulator = PricingSimulator(num_simulations=10000)

    start_time = time.time()
    result = simulator.simulate(
        "PROD-001",
        49.99,
        44.99,
        {"expected_demand": 200, "demand_uncertainty": 30, "elasticity": -1.5},
        25.00,
    )
    elapsed = time.time() - start_time

    # 10,000 simulations should complete in under 1 second
    assert elapsed < 1.0
    assert "revenue" in result
    assert "profit" in result
```

### 9.4 End-to-End Tests

```python
# tests/test_e2e.py
import pytest
import pytest_asyncio
import asyncio


@pytest.mark.asyncio
async def test_end_to_end_price_optimization():
    """
    End-to-end test of the complete pricing optimization pipeline.
    
    This test verifies:
    1. Market signal is received
    2. Pricing engine computes optimal price
    3. Testing agent validates the change
    4. Implementation agent executes the change
    5. Monitoring agent tracks performance
    6. Analytics agent generates report
    """
    # Setup
    state_manager = MagicMock()
    state_manager.get = MagicMock(return_value={})
    state_manager.set = MagicMock()
    state_manager.publish = MagicMock()

    # Create all agents
    market_agent = MarketIntelligenceAgent(state_manager, {
        "product_catalog": ["PROD-001"],
        "poll_interval_seconds": 3600,
    })
    pricing_engine = PricingOptimizationEngine(state_manager, {
        "product_config": {
            "PROD-001": {
                "base_price": 49.99,
                "min_price": 34.99,
                "max_price": 79.99,
                "unit_cost": 25.00,
                "target_margin_pct": 35.0,
                "min_margin_pct": 15.0,
                "base_demand": 200,
                "price_elasticity": -1.8,
            }
        },
        "min_confidence_threshold": 0.5,
        "max_price_change_pct": 20.0,
    })
    testing_agent = TestingAgent(state_manager, {
        "num_simulations": 1000,
        "max_risk_score": 0.5,
    })
    implementation_agent = ImplementationAgent(state_manager, {
        "rollout_strategy": "immediate",
        "channels": {},  # No real channels in test
    })
    monitoring_agent = MonitoringAgent(state_manager, {
        "check_interval_seconds": 3600,
    })
    analytics_agent = PerformanceAnalyticsAgent(state_manager, {
        "report_interval_hours": 24,
    })

    # Start all agents
    for agent in [
        market_agent, pricing_engine, testing_agent,
        implementation_agent, monitoring_agent, analytics_agent,
    ]:
        await agent.on_start()

    # Simulate market signal
    signal = AgentMessage(
        source_agent=AgentType.MARKET_INTELLIGENCE,
        target_agent=AgentType.PRICING_OPTIMIZATION,
        message_type="market_signal",
        payload={
            "signal_type": "competitor_price_change",
            "product_id": "PROD-001",
            "value": {
                "old_price": 49.99,
                "new_price": 44.99,
                "change_pct": -10.0,
            },
            "confidence": 0.9,
        },
    )

    # Process signal through the pipeline
    await pricing_engine._handle_market_signal(signal)

    # Allow time for async processing
    await asyncio.sleep(2)

    # Verify pricing decision was made
    # (In a real e2e test with real agents, you'd verify each step)

    # Stop all agents
    for agent in [
        market_agent, pricing_engine, testing_agent,
        implementation_agent, monitoring_agent, analytics_agent,
    ]:
        await agent.on_stop()
```

### 9.5 Test Configuration

```python
# tests/conftest.py
import pytest
import pytest_asyncio


def pytest_configure(config):
    """Configure pytest."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "e2e: marks tests as end-to-end tests"
    )


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session."""
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
```

### 9.6 Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run only unit tests
pytest tests/ -v -m "not integration and not e2e"

# Run integration tests
pytest tests/ -v -m integration

# Run with coverage
pytest tests/ --cov=. --cov-report=html

# Run specific test file
pytest tests/test_pricing_engine.py -v

# Run with async support
pytest tests/ -v --asyncio-mode=auto
```

---

## Appendix A: Deployment Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Production Deployment                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │   Load      │  │   Load      │  │   Load      │             │
│  │  Balancer   │  │  Balancer   │  │  Balancer   │             │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘             │
│         │                │                │                      │
│  ┌──────▼──────┐  ┌──────▼──────┐  ┌──────▼──────┐             │
│  │  Pricing    │  │  Pricing    │  │  Pricing    │             │
│  │  Service 1  │  │  Service 2  │  │  Service 3  │             │
│  │  (Agents)   │  │  (Agents)   │  │  (Agents)   │             │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘             │
│         │                │                │                      │
│  ┌──────▼────────────────▼────────────────▼──────┐             │
│  │              Redis Cluster                     │             │
│  │         (State & Message Bus)                  │             │
│  └───────────────────────────────────────────────┘             │
│         │                                                       │
│  ┌──────▼────────────────────────────────────────┐             │
│  │           PostgreSQL Database                  │             │
│  │     (Persistent Storage & Analytics)           │             │
│  └───────────────────────────────────────────────┘             │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

## Appendix B: Monitoring & Alerting

```yaml
# monitoring/alerts.yml
groups:
  - name: pricing_optimization
    rules:
      - alert: PricingEngineDown
        expr: up{job="pricing-engine"} == 0
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Pricing engine is down"

      - alert: HighPriceChangeFailureRate
        expr: |
          rate(price_changes_failed_total[1h])
          / rate(price_changes_total[1h]) > 0.2
        for: 15m
        labels:
          severity: warning
        annotations:
          summary: "High price change failure rate (>20%)"

      - alert: LowPricingConfidence
        expr: |
          avg(pricing_decision_confidence) < 0.6
        for: 30m
        labels:
          severity: warning
        annotations:
          summary: "Average pricing confidence below 60%"

      - alert: RollbackRateHigh
        expr: |
          rate(price_changes_rolled_back_total[1h]) > 5
        for: 10m
        labels:
          severity: critical
        annotations:
          summary: "High rollback rate detected"
```

---

*Document Version: 1.0*
*Last Updated: 2026-10-01*
*Author: AI Pricing Optimization Team*
