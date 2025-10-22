"""
Catalyst scoring for ASX announcements.

This module scores price-sensitive announcements based on keywords
and sentiment to identify high-probability trading opportunities.

Scoring scale: 1-10
- 8-10: High impact (takeover, acquisition, major contract)
- 5-7: Medium impact (earnings upgrade, partnership)
- 2-4: Low impact (general updates, appointments)
- 0: Negative catalyst (downgrade, loss, suspension)
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Optional

from ..utils.config import get_config
from ..utils.logger import get_logger


@dataclass
class CatalystScore:
    """Catalyst scoring result."""

    symbol: str
    headline: str
    score: int
    is_positive: bool
    matched_keywords: List[str]
    impact_level: str  # high, medium, low, negative
    scored_at: datetime

    def __str__(self) -> str:
        """String representation."""
        return (
            f"Catalyst {self.symbol} [{self.score}/10 - {self.impact_level}]: "
            f"{self.headline[:60]}... | Keywords: {', '.join(self.matched_keywords)}"
        )


class CatalystScorer:
    """Scores announcements based on keywords and impact."""

    def __init__(self):
        """Initialize catalyst scorer."""
        self.config = get_config()
        self.logger = get_logger().bind(component="catalyst_scorer")

        # Load keywords from config
        self.high_impact_keywords = self.config.get_setting(
            "catalysts", "keywords", "high_impact", default=[]
        )
        self.medium_impact_keywords = self.config.get_setting(
            "catalysts", "keywords", "medium_impact", default=[]
        )
        self.low_impact_keywords = self.config.get_setting(
            "catalysts", "keywords", "low_impact", default=[]
        )
        self.negative_keywords = self.config.get_setting(
            "catalysts", "negative_keywords", default=[]
        )

        self.min_catalyst_score = self.config.get_setting(
            "catalysts", "min_catalyst_score", default=5
        )

        self.logger.info(
            f"Loaded catalyst keywords: "
            f"{len(self.high_impact_keywords)} high, "
            f"{len(self.medium_impact_keywords)} medium, "
            f"{len(self.low_impact_keywords)} low, "
            f"{len(self.negative_keywords)} negative"
        )

    def score_announcement(
        self,
        symbol: str,
        headline: str,
        is_price_sensitive: bool = True,
    ) -> CatalystScore:
        """
        Score an announcement based on keywords.

        Args:
            symbol: Stock symbol
            headline: Announcement headline
            is_price_sensitive: Whether announcement is price-sensitive

        Returns:
            CatalystScore with score and details
        """
        headline_lower = headline.lower()
        matched_keywords = []
        score = 0
        impact_level = "none"
        is_positive = False

        # Check for negative keywords first (disqualifies immediately)
        for keyword in self.negative_keywords:
            if keyword.lower() in headline_lower:
                matched_keywords.append(keyword)
                score = 0
                impact_level = "negative"
                is_positive = False
                self.logger.debug(f"{symbol}: Negative keyword '{keyword}' found")

                return CatalystScore(
                    symbol=symbol,
                    headline=headline,
                    score=score,
                    is_positive=is_positive,
                    matched_keywords=matched_keywords,
                    impact_level=impact_level,
                    scored_at=datetime.now(),
                )

        # Check high impact keywords (8-10)
        for keyword in self.high_impact_keywords:
            if keyword.lower() in headline_lower:
                matched_keywords.append(keyword)
                score = max(score, 8)  # Base score for high impact
                impact_level = "high"
                is_positive = True

        # Check medium impact keywords (5-7)
        if not matched_keywords:  # Only if no high impact found
            for keyword in self.medium_impact_keywords:
                if keyword.lower() in headline_lower:
                    matched_keywords.append(keyword)
                    score = max(score, 5)  # Base score for medium impact
                    impact_level = "medium"
                    is_positive = True

        # Check low impact keywords (2-4)
        if not matched_keywords:  # Only if no higher impact found
            for keyword in self.low_impact_keywords:
                if keyword.lower() in headline_lower:
                    matched_keywords.append(keyword)
                    score = max(score, 2)  # Base score for low impact
                    impact_level = "low"
                    is_positive = True

        # If price sensitive but no keywords matched, give it a baseline score
        if is_price_sensitive and not matched_keywords:
            score = 3
            impact_level = "low"
            is_positive = True
            matched_keywords = ["price_sensitive"]

        # Boost score if multiple keywords match
        if len(matched_keywords) > 1:
            score = min(10, score + len(matched_keywords) - 1)

        result = CatalystScore(
            symbol=symbol,
            headline=headline,
            score=score,
            is_positive=is_positive,
            matched_keywords=matched_keywords,
            impact_level=impact_level,
            scored_at=datetime.now(),
        )

        self.logger.debug(str(result))
        return result

    def is_valid_catalyst(self, catalyst: CatalystScore) -> bool:
        """
        Check if catalyst meets minimum score requirement.

        Args:
            catalyst: Catalyst score to validate

        Returns:
            True if meets requirements
        """
        if not catalyst.is_positive:
            self.logger.debug(f"{catalyst.symbol}: Negative catalyst, rejected")
            return False

        if catalyst.score < self.min_catalyst_score:
            self.logger.debug(
                f"{catalyst.symbol}: Score {catalyst.score} below minimum "
                f"{self.min_catalyst_score}"
            )
            return False

        self.logger.info(f"✓ Valid catalyst: {catalyst}")
        return True

    def score_announcements(
        self,
        announcements: List[Dict[str, any]],
    ) -> List[CatalystScore]:
        """
        Score multiple announcements.

        Args:
            announcements: List of announcement dicts with 'symbol', 'headline', 'is_price_sensitive'

        Returns:
            List of catalyst scores
        """
        scores = []

        for ann in announcements:
            symbol = ann.get("symbol", "UNKNOWN")
            headline = ann.get("headline", "")
            is_price_sensitive = ann.get("is_price_sensitive", True)

            score = self.score_announcement(symbol, headline, is_price_sensitive)
            scores.append(score)

        self.logger.info(f"Scored {len(scores)} announcements")
        return scores

    def get_valid_catalysts(
        self,
        announcements: List[Dict[str, any]],
    ) -> List[CatalystScore]:
        """
        Get valid catalysts that meet minimum score.

        Args:
            announcements: List of announcement dicts

        Returns:
            List of valid catalyst scores
        """
        all_scores = self.score_announcements(announcements)
        valid_scores = [s for s in all_scores if self.is_valid_catalyst(s)]

        self.logger.info(
            f"Found {len(valid_scores)} valid catalysts out of {len(all_scores)} announcements"
        )

        # Sort by score descending
        valid_scores.sort(key=lambda x: x.score, reverse=True)

        return valid_scores

    def get_watchlist_from_catalysts(
        self,
        catalysts: List[CatalystScore],
        max_symbols: Optional[int] = None,
    ) -> List[str]:
        """
        Generate watchlist from catalysts.

        Args:
            catalysts: List of catalyst scores
            max_symbols: Maximum symbols to return (default from config)

        Returns:
            List of symbols for watchlist
        """
        if max_symbols is None:
            max_symbols = self.config.get_setting("watchlist", "max_symbols", default=20)

        # Take top N by score
        top_catalysts = sorted(catalysts, key=lambda x: x.score, reverse=True)[:max_symbols]
        symbols = [c.symbol for c in top_catalysts]

        self.logger.info(f"Generated watchlist with {len(symbols)} symbols")
        return symbols

    def __repr__(self) -> str:
        """String representation."""
        return f"<CatalystScorer min_score={self.min_catalyst_score}>"
