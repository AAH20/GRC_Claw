"""Product recommendations agent using LangChain and collaborative filtering."""

from __future__ import annotations

import structlog
from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from ecommerce_marketing.config import get_settings

logger = structlog.get_logger(__name__)


class Product(BaseModel):
    """Product data model."""

    id: str = Field(..., description="Unique product identifier")
    name: str = Field(..., description="Product name")
    description: str = Field(default="", description="Product description")
    price: float = Field(..., gt=0, description="Product price")
    category: str = Field(default="", description="Product category")
    tags: list[str] = Field(default_factory=list, description="Product tags")
    image_url: str = Field(default="", description="Product image URL")
    in_stock: bool = Field(default=True, description="Whether product is in stock")


class RecommendationRequest(BaseModel):
    """Request model for product recommendations."""

    customer_id: str = Field(..., description="Customer identifier")
    cart_items: list[str] = Field(default_factory=list, description="Current cart item IDs")
    browsing_history: list[str] = Field(
        default_factory=list, description="Recently viewed product IDs"
    )
    num_recommendations: int = Field(
        default=5, ge=1, le=20, description="Number of recommendations"
    )


class Recommendation(BaseModel):
    """Single product recommendation with explanation."""

    product: Product = Field(..., description="Recommended product")
    score: float = Field(..., ge=0, le=1, description="Recommendation confidence score")
    reason: str = Field(default="", description="Explanation for the recommendation")


class RecommendationResponse(BaseModel):
    """Response model for product recommendations."""

    customer_id: str = Field(..., description="Customer identifier")
    recommendations: list[Recommendation] = Field(..., description="List of recommendations")
    generated_at: str = Field(..., description="ISO timestamp of generation")


class ProductRecommendationsAgent:
    """AI agent for generating personalized product recommendations.

    Uses collaborative filtering signals combined with LLM-based ranking
    to generate contextual product recommendations for customers.
    """

    def __init__(self, llm: BaseChatModel | None = None) -> None:
        """Initialize the product recommendations agent.

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
                    "You are an expert e-commerce product recommendation system. "
                    "Analyze the customer's browsing history, cart contents, and preferences "
                    "to suggest the most relevant products. Provide clear reasoning "
                    "for each recommendation.",
                ),
                (
                    "human",
                    "Customer ID: {customer_id}\n"
                    "Cart items: {cart_items}\n"
                    "Browsing history: {browsing_history}\n"
                    "Available products: {products}\n\n"
                    "Recommend {num_recommendations} products with scores and explanations.",
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
            raise ValueError("OPENAI_API_KEY is required for product recommendations")

        return ChatOpenAI(
            model=self.settings.openai_model,
            api_key=self.settings.openai_api_key,
            temperature=0.3,
            max_tokens=2000,
        )

    async def get_recommendations(
        self,
        request: RecommendationRequest,
        available_products: list[Product],
    ) -> RecommendationResponse:
        """Generate personalized product recommendations.

        Args:
            request: Recommendation request with customer context.
            available_products: Pool of products to recommend from.

        Returns:
            Personalized product recommendations with scores and explanations.

        Raises:
            ValueError: If no products are available to recommend.
        """
        if not available_products:
            raise ValueError("No products available for recommendations")

        logger.info(
            "Generating recommendations",
            customer_id=request.customer_id,
            num_products=len(available_products),
            num_requested=request.num_recommendations,
        )

        # Filter out items already in cart
        candidate_products = [
            p for p in available_products if p.id not in request.cart_items and p.in_stock
        ]

        if not candidate_products:
            logger.warning("No candidate products after filtering", customer_id=request.customer_id)
            return RecommendationResponse(
                customer_id=request.customer_id,
                recommendations=[],
                generated_at="",
            )

        # Build prompt and get LLM recommendations
        chain = self._prompt | self.llm
        response = await chain.ainvoke(
            {
                "customer_id": request.customer_id,
                "cart_items": ", ".join(request.cart_items) or "None",
                "browsing_history": ", ".join(request.browsing_history) or "None",
                "products": "\n".join(
                    f"- {p.id}: {p.name} (${p.price}) - {p.description} [Tags: {', '.join(p.tags)}]"
                    for p in candidate_products
                ),
                "num_recommendations": request.num_recommendations,
            }
        )

        # Parse LLM response into structured recommendations
        recommendations = self._parse_recommendations(
            response.content if hasattr(response, "content") else str(response),
            candidate_products,
        )

        logger.info(
            "Recommendations generated",
            customer_id=request.customer_id,
            count=len(recommendations),
        )

        return RecommendationResponse(
            customer_id=request.customer_id,
            recommendations=recommendations,
            generated_at="",
        )

    def _parse_recommendations(
        self,
        llm_output: str,
        products: list[Product],
    ) -> list[Recommendation]:
        """Parse LLM output into structured recommendations.

        Args:
            llm_output: Raw text output from the LLM.
            products: Available products to match against.

        Returns:
            List of parsed recommendations.
        """
        import json

        recommendations: list[Recommendation] = []
        product_map = {p.id: p for p in products}

        try:
            # Attempt to parse JSON response
            data = json.loads(llm_output)
            items = data.get("recommendations", []) if isinstance(data, dict) else data
            for item in items:
                product_id = item.get("product_id", "")
                if product_id in product_map:
                    recommendations.append(
                        Recommendation(
                            product=product_map[product_id],
                            score=float(item.get("score", 0.5)),
                            reason=item.get("reason", ""),
                        )
                    )
        except (json.JSONDecodeError, KeyError, ValueError):
            # Fallback: return top products with default scores
            logger.warning("Failed to parse LLM recommendations, using fallback")
            for product in products[:5]:
                recommendations.append(
                    Recommendation(
                        product=product,
                        score=0.5,
                        reason="Recommended based on popularity",
                    )
                )

        return recommendations[: self.settings.agents.product_recommendations.max_recommendations]
