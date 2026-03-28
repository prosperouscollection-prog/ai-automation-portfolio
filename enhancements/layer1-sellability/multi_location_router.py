"""Multi-location routing strategies for Genesis AI Systems lead workflows.

This module makes multi-location deployments extensible by modeling each
routing strategy behind an abstract base class. New routing logic can be added
without rewriting the orchestration layer.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Iterable


@dataclass(frozen=True)
class LocationConfig:
    """Configuration for one client location."""

    location_id: str
    display_name: str
    zip_codes: set[str] = field(default_factory=set)
    area_codes: set[str] = field(default_factory=set)
    keywords: set[str] = field(default_factory=set)
    worksheet_tab: str = "Leads"
    phone_number: str = ""
    email: str = ""
    prompt_variant: str = ""


@dataclass(frozen=True)
class LeadRoutingRequest:
    """Input signal used to determine where a lead should be routed."""

    message: str
    caller_phone: str = ""
    zip_code: str = ""


@dataclass(frozen=True)
class RoutingDecision:
    """The result of a routing evaluation."""

    location: LocationConfig | None
    matched_by: str
    reason: str


class LocationRouter(ABC):
    """Abstract base for all location-routing strategies."""

    @abstractmethod
    def route(
        self,
        request: LeadRoutingRequest,
        locations: Iterable[LocationConfig],
    ) -> RoutingDecision | None:
        """Return a location decision when the strategy finds a match."""


class ZipCodeRouter(LocationRouter):
    """Route based on the lead's supplied ZIP code."""

    def route(
        self,
        request: LeadRoutingRequest,
        locations: Iterable[LocationConfig],
    ) -> RoutingDecision | None:
        """Match the first location whose ZIP rules include the request ZIP."""
        normalized_zip = request.zip_code.strip()
        if not normalized_zip:
            return None
        for location in locations:
            if normalized_zip in location.zip_codes:
                return RoutingDecision(
                    location=location,
                    matched_by="zip_code",
                    reason=f"Matched ZIP code {normalized_zip}.",
                )
        return None


class AreaCodeRouter(LocationRouter):
    """Route based on the caller phone number's area code."""

    def route(
        self,
        request: LeadRoutingRequest,
        locations: Iterable[LocationConfig],
    ) -> RoutingDecision | None:
        """Match using the first three digits of the caller number."""
        digits = "".join(char for char in request.caller_phone if char.isdigit())
        if len(digits) < 10:
            return None
        area_code = digits[-10:-7]
        for location in locations:
            if area_code in location.area_codes:
                return RoutingDecision(
                    location=location,
                    matched_by="area_code",
                    reason=f"Matched area code {area_code}.",
                )
        return None


class KeywordRouter(LocationRouter):
    """Route based on keywords inside the lead message."""

    def route(
        self,
        request: LeadRoutingRequest,
        locations: Iterable[LocationConfig],
    ) -> RoutingDecision | None:
        """Match a location when one of its keywords appears in the message."""
        message = request.message.lower()
        for location in locations:
            for keyword in location.keywords:
                if keyword.lower() in message:
                    return RoutingDecision(
                        location=location,
                        matched_by="keyword",
                        reason=f"Matched keyword '{keyword}'.",
                    )
        return None


class CompositeLocationRouter(LocationRouter):
    """Runs multiple routers in order until one returns a decision."""

    def __init__(self, routers: list[LocationRouter]) -> None:
        """Use an ordered strategy chain for routing."""
        self._routers = routers

    def route(
        self,
        request: LeadRoutingRequest,
        locations: Iterable[LocationConfig],
    ) -> RoutingDecision | None:
        """Return the first positive routing decision from the chain."""
        locations = list(locations)
        _validate_location_count(locations)
        for router in self._routers:
            decision = router.route(request, locations)
            if decision is not None:
                return decision
        return RoutingDecision(
            location=locations[0] if locations else None,
            matched_by="default",
            reason="No explicit match found; defaulting to the first configured location.",
        )


def default_router() -> CompositeLocationRouter:
    """Build the recommended default routing order."""
    return CompositeLocationRouter(
        routers=[
            ZipCodeRouter(),
            AreaCodeRouter(),
            KeywordRouter(),
        ]
    )


def _validate_location_count(locations: list[LocationConfig]) -> None:
    """Guard against unsupported oversized location configurations."""
    if len(locations) > 10:
        raise ValueError("Multi-location routing supports up to 10 locations per client.")
