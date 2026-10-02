"""Cart abandonment recovery agent."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import structlog
from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from ecommerce_marketing.config import get_settings

logger = structlog.get_logger(__name__)


class CartItem(BaseModel):
    """Item in an abandoned cart."""

    product_id: str = Field(..., description="Product identifier")
    product_name: str = Field(..., description="Product name")
    quantity: int = Field(..., gt=0, description="Quantity in cart")
    price: float = Field(..., gt=0, description="Unit price")
    image_url: str = Field(default="", description="Product image URL")


class AbandonedCart(BaseModel):
    """Abandoned cart data model."""

    cart_id: str = Field(..., description="Unique cart identifier")
    customer_id: str = Field(..., description="Customer identifier")
    customer_email: str = Field(..., description="Customer email address")
    items: list[CartItem] = Field(..., description="Items in the cart")
    total_value: float = Field(..., gt=0, description="Total cart value")
    abandoned_at: datetime = Field(..., description="When the cart was abandoned")
    currency: str = Field(default="USD", description="Currency code")


class RecoveryMessage(BaseModel):
    """Recovery message content."""

    subject: str = Field(..., description="Email subject line")
    body_html: str = Field(..., description="HTML email body")
    body_text: str = Field(..., description="Plain text email body")
    call_to_action: str = Field(..., description="Call to action text")
    discount_code: str | None = Field(default=None, description="Optional discount code")


class RecoveryAction(BaseModel):
    """A recovery action to be taken."""

    action_type: str = Field(..., description="Type of recovery action (email, push, sms)")
    message: RecoveryMessage = Field(..., description="Recovery message content")
    scheduled_at: datetime = Field(..., description="When to send the recovery")
    priority: int = Field(default=1, ge=1, le=5, description="Priority level")


class CartAbandonmentAgent:
    """AI agent for cart abandonment recovery workflows.

    Analyzes abandoned carts and generates personalized recovery messages
    with optimal timing and channel selection.
    """

    def __init__(self, llm: BaseChatModel | None = None) -> None:
        """Initialize the cart abandonment agent.

        Args:
            llm: Optional LangChain chat model. If not provided, uses the default
                model from settings.
        """
        self.settings = get_settings()
        self.llm = llm or self._create_default_llm()
        self._prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are an expert e-commerce recovery specialist. "
                    "Create compelling, personalized recovery messages that encourage "
                    "customers to complete their purchase. Be helpful, not pushy. "
                    "Include specific product references and a clear call to action.",
                ),
                (
                    "human",
                    "Customer: {customer_email}\n"
                    "Cart value: {total_value} {currency}\n"
                    "Items: {items}\n"
                    "Abandoned since: {abandoned_at}\n"
                    "Hours since abandonment: {hours_abandoned}\n\n"
                    "Create a recovery email with subject, HTML body, text body, and CTA.",
                ),
            ]
        )

    def _create_default_llm(self) -> BaseChatModel:
        """Create the default LLM from settings.

        Returns:
            Configured LangChain chat model.

        Raises:
            ValueError: If OPENAI_API_KEY is not configured.
        """
        try:
            from langchain_openai import ChatOpenAI
        except ImportError as exc:
            raise ImportError(
                "langchain-openai is required for default LLM. "
                "Install with: pip install langchain-openai"
            ) from exc

        if not self.settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required for cart abandonment recovery")

        return ChatOpenAI(
            model=self.settings.openai_model,
            api_key=self.settings.openai_api_key,
            temperature=0.7,
            max_tokens=1500,
        )

    def should_recover(self, cart: AbandonedCart) -> bool:
        """Determine if a cart should be recovered based on business rules.

        Args:
            cart: The abandoned cart to evaluate.

        Returns:
            True if the cart qualifies for recovery.
        """
        hours_abandoned = (datetime.now(UTC) - cart.abandoned_at).total_seconds() / 3600

        # Don't recover carts abandoned too recently or too long ago
        if hours_abandoned < 1:
            return False
        if hours_abandoned > self.settings.agents.cart_abandonment.recovery_window_hours:
            return False

        # Don't recover very low-value carts
        return not cart.total_value < 10

    async def create_recovery_plan(self, cart: AbandonedCart) -> list[RecoveryAction]:
        """Create a multi-step recovery plan for an abandoned cart.

        Args:
            cart: The abandoned cart to create a recovery plan for.

        Returns:
            Ordered list of recovery actions to execute.

        Raises:
            ValueError: If the cart does not qualify for recovery.
        """
        if not self.should_recover(cart):
            raise ValueError(f"Cart {cart.cart_id} does not qualify for recovery")

        hours_abandoned = (datetime.now(UTC) - cart.abandoned_at).total_seconds() / 3600

        logger.info(
            "Creating recovery plan",
            cart_id=cart.cart_id,
            customer_id=cart.customer_id,
            cart_value=cart.total_value,
            hours_abandoned=hours_abandoned,
        )

        # Generate recovery message using LLM
        chain = self._prompt | self.llm
        response = await chain.ainvoke(
            {
                "customer_email": cart.customer_email,
                "total_value": f"{cart.total_value:.2f}",
                "currency": cart.currency,
                "items": "\n".join(
                    f"- {item.product_name} (x{item.quantity}) - ${item.price:.2f}"
                    for item in cart.items
                ),
                "abandoned_at": cart.abandoned_at.isoformat(),
                "hours_abandoned": f"{hours_abandoned:.1f}",
            }
        )

        message = self._parse_recovery_message(
            response.content if hasattr(response, "content") else str(response)
        )

        # Build recovery schedule
        intervals = self.settings.agents.cart_abandonment.reminder_intervals
        actions: list[RecoveryAction] = []

        for i, interval in enumerate(intervals[: self.settings.agents.cart_abandonment.max_reminders]):
            scheduled_time = datetime.now(UTC) + timedelta(hours=interval)
            actions.append(
                RecoveryAction(
                    action_type="email",
                    message=message,
                    scheduled_at=scheduled_time,
                    priority=i + 1,
                )
            )

        logger.info(
            "Recovery plan created",
            cart_id=cart.cart_id,
            num_actions=len(actions),
        )

        return actions

    def _parse_recovery_message(self, llm_output: str) -> RecoveryMessage:
        """Parse LLM output into a structured recovery message.

        Args:
            llm_output: Raw text output from the LLM.

        Returns:
            Structured recovery message.
        """
        import json

        try:
            data = json.loads(llm_output)
            return RecoveryMessage(
                subject=data.get("subject", "Complete your purchase"),
                body_html=data.get("body_html", ""),
                body_text=data.get("body_text", ""),
                call_to_action=data.get("call_to_action", "Complete Your Order"),
                discount_code=data.get("discount_code"),
            )
        except (json.JSONDecodeError, KeyError):
            logger.warning("Failed to parse recovery message, using fallback")
            return RecoveryMessage(
                subject="Don't forget your items!",
                body_html="<p>Your cart is waiting for you.</p>",
                body_text="Your cart is waiting for you.",
                call_to_action="Complete Your Order",
                discount_code=None,
            )
