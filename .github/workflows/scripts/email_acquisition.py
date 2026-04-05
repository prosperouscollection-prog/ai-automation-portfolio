#!/usr/bin/env python3
"""Deterministic owner-email acquisition helpers for Genesis AI Systems.

This module hardens email discovery without touching send authority. It keeps a
single canonical `owner_email` field and records where each candidate came from
so downstream workflows can make trust-preserving decisions.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urljoin, urlparse

import requests

DETROIT = "America/Detroit"

SHEETS_HEADERS = [
    "date/timestamp",
    "source",
    "business name",
    "domain",
    "owner_email",
    "phone",
    "address",
    "score",
    "qualification status",
    "outreach subject",
    "outreach body",
    "variant ID",
    "pipeline stage",
    "next action",
    "last updated",
]

INTERNAL_RECORD_MARKERS = (
    "founder-test",
    "release-gate",
    "internal",
    "qa-only",
    "smoke-test",
    "test fixture",
    "demo-only",
)

GENERAL_CONTACT_PREFIXES = ("info@", "hello@", "contact@", "office@", "support@", "team@", "sales@", "admin@")
CONTACT_PATHS = ("", "/", "/contact", "/contact-us", "/about", "/about-us", "/team", "/staff")

EMAIL_RE = re.compile(
    r"(?<![A-Za-z0-9._%+-])"
    r"([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})"
    r"(?![A-Za-z0-9._%+-])"
)

NAME_RE = re.compile(r"[A-Za-z][A-Za-z'’-]+")

CLASSIFICATION_RANK = {
    "OWNER_CONFIRMED": 500,
    "OWNER_PROBABLE": 400,
    "DECISION_MAKER_PROBABLE": 300,
    "GENERAL_CONTACT_ONLY": 100,
    "NO_EMAIL_FOUND": 0,
}

SOURCE_RANK = {
    "structured_provider": 600,
    "website_contact_page": 500,
    "same_domain_person_match": 450,
    "domain_pattern_inference": 350,
    "directory_listing": 250,
    "general_contact": 150,
    "unknown": 0,
}

CONFIDENCE_LABEL = {
    "OWNER_CONFIRMED": "HIGH",
    "OWNER_PROBABLE": "HIGH",
    "DECISION_MAKER_PROBABLE": "MEDIUM",
    "GENERAL_CONTACT_ONLY": "LOW",
    "NO_EMAIL_FOUND": "NONE",
}


def normalize_text(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        stripped = value.strip()
        return stripped or None
    text = str(value).strip()
    return text or None


def normalize_domain(value: Any) -> str | None:
    text = normalize_text(value)
    if text is None:
        return None
    lowered = text.lower()
    if lowered.startswith("http://"):
        lowered = lowered[len("http://") :]
    if lowered.startswith("https://"):
        lowered = lowered[len("https://") :]
    if lowered.startswith("www."):
        lowered = lowered[len("www.") :]
    lowered = lowered.strip("/ ")
    if not lowered or "." not in lowered or " " in lowered:
        return None
    return lowered


def normalize_owner_email(value: Any) -> str | None:
    text = normalize_text(value)
    if text is None:
        return None
    lowered = text.lower()
    if not EMAIL_RE.fullmatch(lowered):
        return None
    return lowered


def is_internal_record(record: dict[str, Any]) -> bool:
    combined = " ".join(
        str(record.get(field, "")) for field in (
            "name",
            "business_name",
            "source",
            "outreach_subject",
            "outreach_body",
            "notes",
            "category",
        )
    ).lower()
    return any(marker in combined for marker in INTERNAL_RECORD_MARKERS)


def build_canonical_sheet_row(record: dict[str, Any], industry: str | None = None) -> list[str]:
    scraped_at = normalize_text(record.get("scraped_at")) or datetime.now().isoformat()
    business_name = normalize_text(record.get("business_name") or record.get("name")) or "Unknown"
    domain = normalize_domain(record.get("primary_domain") or record.get("website") or record.get("domain")) or ""
    owner_email = normalize_owner_email(
        record.get("owner_email") or record.get("email") or record.get("final_email")
    ) or ""
    score = normalize_text(record.get("score")) or ""
    qualification_status = normalize_text(record.get("qualification_status"))
    if qualification_status is None:
        qualification_status = "qualified" if score.upper() == "HOT" else "review"
    outreach_subject = normalize_text(record.get("outreach_subject")) or ""
    outreach_body = normalize_text(record.get("outreach_body")) or ""
    variant_id = normalize_text(record.get("variant_id") or record.get("variant")) or ""
    pipeline_stage = normalize_text(record.get("pipeline_stage")) or (
        "DRAFT_READY" if outreach_subject or outreach_body else "CAPTURED"
    )
    next_action = normalize_text(record.get("next_action")) or "founder_review_draft"
    last_updated = normalize_text(record.get("last_updated")) or scraped_at
    source = normalize_text(record.get("source")) or ""
    phone = normalize_text(record.get("phone")) or ""
    address = normalize_text(record.get("address")) or ""

    return [
        scraped_at,
        source,
        business_name,
        domain,
        owner_email,
        phone,
        address,
        score,
        qualification_status,
        outreach_subject,
        outreach_body,
        variant_id,
        pipeline_stage,
        next_action,
        last_updated,
    ]


def _person_name_tokens(name: str) -> list[str]:
    tokens = [token.lower() for token in NAME_RE.findall(name or "")]
    return [token for token in tokens if token]


def _domain_from_prospect(prospect: dict[str, Any]) -> str | None:
    return normalize_domain(
        prospect.get("primary_domain")
        or prospect.get("website")
        or prospect.get("domain")
        or prospect.get("url")
    )


def _is_same_domain(email: str, domain: str | None) -> bool:
    if not domain:
        return False
    email_domain = email.rsplit("@", 1)[-1].lower()
    return email_domain == domain or email_domain.endswith(f".{domain}")


def _domain_patterns(name: str, domain: str) -> list[str]:
    tokens = _person_name_tokens(name)
    if not tokens:
        return []
    first = tokens[0]
    last = tokens[-1] if len(tokens) > 1 else ""
    patterns: list[str] = []
    if first and last:
        patterns.extend(
            [
                f"{first}@{domain}",
                f"{first}.{last}@{domain}",
                f"{first}{last}@{domain}",
                f"{first[0]}{last}@{domain}",
                f"{first[0]}.{last}@{domain}",
            ]
        )
    elif first:
        patterns.extend([f"{first}@{domain}", f"{first[0]}@{domain}"])
    return patterns


def _find_page_emails(html: str) -> list[str]:
    emails: list[str] = []
    for match in EMAIL_RE.finditer(html or ""):
        email = normalize_owner_email(match.group(1))
        if email and email not in emails:
            emails.append(email)
    return emails


def _candidate_strength(candidate: dict[str, Any]) -> tuple[int, int, int, int]:
    classification = str(candidate.get("email_classification", "NO_EMAIL_FOUND")).upper()
    source_type = str(candidate.get("email_source_type", "unknown")).lower()
    confidence = int(candidate.get("confidence", 0) or 0)
    same_domain = 1 if candidate.get("same_domain") else 0
    return (
        CLASSIFICATION_RANK.get(classification, 0),
        SOURCE_RANK.get(source_type, 0),
        confidence,
        same_domain,
    )


def _person_basis_from_record(prospect: dict[str, Any]) -> str:
    for field in ("owner_name", "contact_name", "staff_name", "title", "role"):
        value = normalize_text(prospect.get(field))
        if value:
            return f"{field}={value}"
    return ""


def _classify_candidate(candidate: dict[str, Any], prospect: dict[str, Any]) -> str:
    source_type = str(candidate.get("email_source_type", "unknown")).lower()
    person_basis = normalize_text(candidate.get("person_match_basis")) or ""
    domain = _domain_from_prospect(prospect)
    final_email = normalize_owner_email(candidate.get("final_email")) or ""
    same_domain = bool(final_email and _is_same_domain(final_email, domain))

    if source_type == "general_contact":
        return "GENERAL_CONTACT_ONLY"
    if person_basis and same_domain and any(
        keyword in person_basis.lower() for keyword in ("owner", "founder", "ceo", "principal", "president")
    ):
        return "OWNER_CONFIRMED"
    if source_type == "structured_provider":
        return "OWNER_CONFIRMED" if same_domain and person_basis else "OWNER_PROBABLE"
    if source_type in {"website_contact_page", "same_domain_person_match", "directory_listing"}:
        return "OWNER_CONFIRMED" if same_domain and person_basis else "DECISION_MAKER_PROBABLE"
    if source_type == "domain_pattern_inference":
        return "DECISION_MAKER_PROBABLE"
    return "OWNER_PROBABLE" if same_domain else "DECISION_MAKER_PROBABLE"


@dataclass
class EmailAcquisitionResult:
    final_email: str = ""
    email_classification: str = "NO_EMAIL_FOUND"
    email_confidence: str = "NONE"
    email_source_type: str = "unknown"
    email_source_reference: str = ""
    person_match_basis: str = ""
    verification_notes: str = ""
    rejection_reason: str = ""
    passes_ran: list[str] = field(default_factory=list)
    candidate_history: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class EmailAcquisitionEngine:
    """Best-first owner email acquisition engine."""

    def __init__(
        self,
        *,
        request_get: Callable[..., requests.Response] | None = None,
        logger: Callable[[str], None] = print,
    ) -> None:
        self.request_get = request_get or requests.get
        self.logger = logger

    def acquire(self, prospect: dict[str, Any]) -> EmailAcquisitionResult:
        result = EmailAcquisitionResult()
        business_name = normalize_text(prospect.get("business_name") or prospect.get("name")) or "Unknown"
        domain = _domain_from_prospect(prospect)
        owner_basis = _person_basis_from_record(prospect)

        self.logger(
            f"  🔍 email acquisition start — business={business_name} domain={domain or 'missing'}"
        )

        best_candidate: dict[str, Any] | None = None
        pass_methods = [
            ("pass_1", self._pass_1_structured_provider),
            ("pass_2", self._pass_2_website_extraction),
            ("pass_3", self._pass_3_same_domain_person_match),
            ("pass_4", self._pass_4_domain_pattern_inference),
            ("pass_5", self._pass_5_directory_social_listing),
            ("pass_6", self._pass_6_general_contact_fallback),
        ]

        for pass_name, method in pass_methods:
            result.passes_ran.append(pass_name)
            candidates = method(prospect)
            if not candidates:
                self.logger(f"  🔍 {pass_name}: no candidate")
                result.candidate_history.append({"pass": pass_name, "candidates": []})
                continue

            if isinstance(candidates, dict):
                candidates = [candidates]

            normalized_candidates: list[dict[str, Any]] = []
            for candidate in candidates:
                normalized = self._normalize_candidate(candidate, prospect, owner_basis)
                if normalized is None:
                    continue
                normalized_candidates.append(normalized)
                result.candidate_history.append({"pass": pass_name, "candidate": normalized})
                self.logger(
                    "  🔍 "
                    f"{pass_name}: candidate={normalized['final_email']} "
                    f"classification={normalized['email_classification']} "
                    f"source={normalized['email_source_type']}"
                )
                if best_candidate is None or _candidate_strength(normalized) > _candidate_strength(best_candidate):
                    best_candidate = normalized
                    self.logger(
                        "  ✅ email candidate won — "
                        f"{normalized['final_email']} ({normalized['email_classification']})"
                    )

            if not normalized_candidates:
                result.candidate_history.append({"pass": pass_name, "candidates": []})

        if best_candidate is None:
            result.rejection_reason = (
                "all six acquisition passes exhausted without a verified owner_email"
            )
            result.verification_notes = (
                f"passes_ran={','.join(result.passes_ran)}; no candidate survived normalization"
            )
            self.logger("  ℹ️  email acquisition exhausted all passes — no owner_email found")
            return result

        result.final_email = best_candidate["final_email"]
        result.email_classification = best_candidate["email_classification"]
        result.email_confidence = CONFIDENCE_LABEL.get(result.email_classification, "LOW")
        result.email_source_type = best_candidate["email_source_type"]
        result.email_source_reference = best_candidate.get("email_source_reference", "")
        result.person_match_basis = best_candidate.get("person_match_basis", "")
        selected_notes = normalize_text(best_candidate.get("verification_notes")) or ""
        result.verification_notes = (
            f"passes_ran={','.join(result.passes_ran)}; "
            f"winner={result.email_source_type}:{result.email_source_reference or 'n/a'}; "
            f"{selected_notes}".strip()
        ).strip()
        self.logger(
            "  ✅ email acquisition complete — "
            f"classification={result.email_classification} confidence={result.email_confidence} "
            f"source={result.email_source_type}"
        )
        return result

    def _normalize_candidate(
        self,
        candidate: dict[str, Any],
        prospect: dict[str, Any],
        owner_basis: str,
    ) -> dict[str, Any] | None:
        final_email = normalize_owner_email(candidate.get("final_email") or candidate.get("email"))
        if not final_email:
            return None

        source_type = normalize_text(candidate.get("email_source_type")) or "unknown"
        source_reference = normalize_text(candidate.get("email_source_reference")) or ""
        person_match_basis = normalize_text(candidate.get("person_match_basis")) or ""
        verification_notes = normalize_text(candidate.get("verification_notes")) or ""
        candidate.setdefault("same_domain", bool(_is_same_domain(final_email, _domain_from_prospect(prospect))))
        candidate["final_email"] = final_email
        candidate["email_source_type"] = source_type
        candidate["email_source_reference"] = source_reference
        candidate["person_match_basis"] = person_match_basis
        candidate["verification_notes"] = verification_notes
        if owner_basis and not person_match_basis:
            candidate["verification_notes"] = (
                f"{verification_notes}; prospect_basis={owner_basis}".strip("; ")
            )
        candidate["email_classification"] = _classify_candidate(candidate, prospect)
        candidate["confidence"] = int(candidate.get("confidence", 0) or 0)
        candidate["same_domain"] = bool(candidate.get("same_domain"))
        return candidate

    def _pass_1_structured_provider(self, prospect: dict[str, Any]) -> list[dict[str, Any]]:
        candidates: list[dict[str, Any]] = []
        domain = _domain_from_prospect(prospect)
        owner_basis = _person_basis_from_record(prospect)
        for source_key, source_label in (
            ("owner_email", "owner_email"),
            ("final_email", "final_email"),
            ("email", "email"),
            ("enriched_email", "enriched_email"),
            ("hunter_email", "hunter_email"),
            ("contact_email", "contact_email"),
        ):
            email = normalize_owner_email(prospect.get(source_key))
            if not email:
                continue
            candidates.append(
                {
                    "final_email": email,
                    "email_source_type": "structured_provider",
                    "email_source_reference": source_label,
                    "person_match_basis": owner_basis,
                    "verification_notes": f"structured field {source_key} normalized to canonical owner_email",
                    "confidence": 0,
                    "same_domain": bool(domain and _is_same_domain(email, domain)),
                }
            )
            break
        return candidates

    def _candidate_pages(self, prospect: dict[str, Any]) -> list[str]:
        domain = _domain_from_prospect(prospect)
        if not domain:
            return []
        roots = []
        for raw in (prospect.get("website"), prospect.get("primary_domain"), prospect.get("domain")):
            normalized = normalize_text(raw)
            if not normalized:
                continue
            if normalized.startswith("http://") or normalized.startswith("https://"):
                roots.append(normalized.rstrip("/"))
            else:
                roots.append(f"https://{normalized.strip('/')}")
        if not roots:
            roots.append(f"https://{domain}")
        urls: list[str] = []
        for root in roots:
            for path in CONTACT_PATHS:
                url = urljoin(root.rstrip("/") + "/", path.lstrip("/"))
                if url not in urls:
                    urls.append(url)
        return urls[:8]

    def _fetch_pages(self, prospect: dict[str, Any]) -> list[tuple[str, str]]:
        pages: list[tuple[str, str]] = []
        for url in self._candidate_pages(prospect):
            try:
                response = self.request_get(url, timeout=12)
                if response.ok and response.text:
                    pages.append((url, response.text))
            except Exception:
                continue
        return pages

    def _pass_2_website_extraction(self, prospect: dict[str, Any]) -> list[dict[str, Any]]:
        domain = _domain_from_prospect(prospect)
        pages = self._fetch_pages(prospect)
        if not pages:
            return []
        candidates: list[dict[str, Any]] = []
        business_name = normalize_text(prospect.get("business_name") or prospect.get("name")) or ""
        owner_basis = _person_basis_from_record(prospect)
        for url, html in pages:
            for email in _find_page_emails(html):
                notes = "website page email extracted from contact/about/team/footer path"
                if business_name and business_name.lower() in html.lower():
                    notes += "; business name present on page"
                candidates.append(
                    {
                        "final_email": email,
                        "email_source_type": "website_contact_page",
                        "email_source_reference": url,
                        "person_match_basis": owner_basis or business_name,
                        "verification_notes": notes,
                        "confidence": 0,
                        "same_domain": bool(domain and _is_same_domain(email, domain)),
                    }
                )
        return candidates

    def _pass_3_same_domain_person_match(self, prospect: dict[str, Any]) -> list[dict[str, Any]]:
        domain = _domain_from_prospect(prospect)
        if not domain:
            return []
        owner_basis = _person_basis_from_record(prospect)
        if not owner_basis:
            return []
        pages = self._fetch_pages(prospect)
        if not pages:
            return []
        matched: list[dict[str, Any]] = []
        tokens = _person_name_tokens(owner_basis)
        for url, html in pages:
            html_lower = html.lower()
            for email in _find_page_emails(html):
                local_part = email.split("@", 1)[0].lower()
                if all(token in local_part for token in tokens[:2]) or any(token in html_lower for token in tokens):
                    matched.append(
                        {
                            "final_email": email,
                            "email_source_type": "same_domain_person_match",
                            "email_source_reference": url,
                            "person_match_basis": owner_basis,
                            "verification_notes": "email matched an explicit staff/owner name on the same domain",
                            "confidence": 0,
                            "same_domain": True,
                        }
                    )
        return matched

    def _pass_4_domain_pattern_inference(self, prospect: dict[str, Any]) -> list[dict[str, Any]]:
        domain = _domain_from_prospect(prospect)
        if not domain:
            return []
        owner_basis = _person_basis_from_record(prospect)
        if not owner_basis:
            return []
        name = owner_basis.split("=", 1)[-1]
        patterns = _domain_patterns(name, domain)
        if not patterns:
            return []
        return [
            {
                "final_email": pattern,
                "email_source_type": "domain_pattern_inference",
                "email_source_reference": f"name={name};domain={domain}",
                "person_match_basis": owner_basis,
                "verification_notes": "deterministic name/domain pattern inference",
                "confidence": 0,
                "same_domain": True,
            }
            for pattern in patterns[:2]
        ]

    def _pass_5_directory_social_listing(self, prospect: dict[str, Any]) -> list[dict[str, Any]]:
        urls: list[str] = []
        for key in ("directory_sources", "social_links", "directory_urls"):
            value = prospect.get(key)
            if isinstance(value, (list, tuple)):
                urls.extend(str(item).strip() for item in value if normalize_text(item))
        for key in ("linkedin_url", "facebook_url", "instagram_url", "yelp_url"):
            value = normalize_text(prospect.get(key))
            if value:
                urls.append(value)
        candidates: list[dict[str, Any]] = []
        for url in dict.fromkeys(urls):
            try:
                response = self.request_get(url, timeout=12)
                if not (response.ok and response.text):
                    continue
                for email in _find_page_emails(response.text):
                    candidates.append(
                        {
                            "final_email": email,
                            "email_source_type": "directory_listing",
                            "email_source_reference": url,
                            "person_match_basis": _person_basis_from_record(prospect),
                            "verification_notes": "directory/social/business listing email extracted",
                            "confidence": 0,
                            "same_domain": bool(_is_same_domain(email, _domain_from_prospect(prospect))),
                        }
                    )
            except Exception:
                continue
        return candidates

    def _pass_6_general_contact_fallback(self, prospect: dict[str, Any]) -> list[dict[str, Any]]:
        domain = _domain_from_prospect(prospect)
        if not domain:
            return []
        pages = self._fetch_pages(prospect)
        generic_candidates: list[dict[str, Any]] = []
        for url, html in pages:
            for email in _find_page_emails(html):
                local_part = email.split("@", 1)[0].lower()
                if any(local_part.startswith(prefix[:-1]) for prefix in GENERAL_CONTACT_PREFIXES):
                    generic_candidates.append(
                        {
                            "final_email": email,
                    "email_source_type": "general_contact",
                    "email_source_reference": url,
                    "person_match_basis": "",
                    "verification_notes": "generic contact address discovered after owner-level passes failed",
                    "confidence": 0,
                    "same_domain": True,
                }
            )
        if generic_candidates:
            return generic_candidates
        return [
            {
                "final_email": f"info@{domain}",
                "email_source_type": "general_contact",
                "email_source_reference": f"synthetic:info@{domain}",
                "person_match_basis": "",
                "verification_notes": "synthetic general contact fallback after owner-level passes failed",
                "confidence": 0,
                "same_domain": True,
            }
        ]
