from __future__ import annotations

import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / ".github" / "workflows" / "scripts" / "sales_agent.py"
SCRIPTS_DIR = ROOT / ".github" / "workflows" / "scripts"
V1_DIR = ROOT / "v1-revenue-system"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))
if str(V1_DIR) not in sys.path:
    sys.path.insert(0, str(V1_DIR))

spec = importlib.util.spec_from_file_location("sales_agent", MODULE_PATH)
if spec is None or spec.loader is None:  # pragma: no cover
    raise RuntimeError(f"Unable to load {MODULE_PATH}")
sales_agent = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = sales_agent
spec.loader.exec_module(sales_agent)

Lead = sales_agent.Lead
SalesAgent = sales_agent.SalesAgent


def _make_suppression_entry(*, email: str = "", domain: str = "", status: str = "skip") -> str:
    entry = {
        "recipient_hash": hashlib.sha256(email.strip().lower().encode("utf-8")).hexdigest(),
        "domain": domain.strip().lower(),
        "status": status,
        "reason": "founder_skipped",
        "date_added": "2026-04-05T00:00:00-04:00",
        "source": "sales_agent",
    }
    if email:
        entry["email"] = email.strip().lower()
    return json.dumps(entry)


class SuppressionCheckTests(unittest.TestCase):

    def _make_agent(self) -> SalesAgent:
        agent = SalesAgent.__new__(SalesAgent)
        agent.sheet_id = ""
        agent.service_account_json = ""
        agent._sheets_service = None
        agent._last_update_id = 0
        agent.no_send_invoked = False
        return agent

    # ------------------------------------------------------------------
    # _load_suppression_index
    # ------------------------------------------------------------------

    def test_load_suppression_index_empty_file(self) -> None:
        agent = self._make_agent()
        with tempfile.NamedTemporaryFile(suffix=".ndjson", mode="w", delete=False) as f:
            f.write("")
            tmp = Path(f.name)
        try:
            orig = sales_agent.SUPPRESSION_FILE
            sales_agent.SUPPRESSION_FILE = tmp
            hashes, domains = agent._load_suppression_index()
            self.assertEqual(hashes, set())
            self.assertEqual(domains, set())
        finally:
            sales_agent.SUPPRESSION_FILE = orig
            tmp.unlink(missing_ok=True)

    def test_load_suppression_index_populates_hash_and_domain(self) -> None:
        agent = self._make_agent()
        entry = _make_suppression_entry(email="owner@example.com", domain="example.com")
        with tempfile.NamedTemporaryFile(suffix=".ndjson", mode="w", delete=False) as f:
            f.write(entry + "\n")
            tmp = Path(f.name)
        try:
            orig = sales_agent.SUPPRESSION_FILE
            sales_agent.SUPPRESSION_FILE = tmp
            hashes, domains = agent._load_suppression_index()
            expected_hash = hashlib.sha256("owner@example.com".encode("utf-8")).hexdigest()
            self.assertIn(expected_hash, hashes)
            self.assertIn("example.com", domains)
        finally:
            sales_agent.SUPPRESSION_FILE = orig
            tmp.unlink(missing_ok=True)

    # ------------------------------------------------------------------
    # _is_lead_suppressed
    # ------------------------------------------------------------------

    def test_suppressed_by_domain_blocks_lead(self) -> None:
        agent = self._make_agent()
        lead = Lead(
            business="Acme Plumbing",
            domain="acmeplumbing.com",
            phone="313-555-0100",
            address="123 Main St Detroit MI",
            industry="hvac",
            score="HOT",
            yelp_rating="4.5",
            sheet_row=10,
            owner_email="owner@acmeplumbing.com",
        )
        hashes: set[str] = set()
        domains = {"acmeplumbing.com"}
        self.assertTrue(agent._is_lead_suppressed(lead, hashes, domains))

    def test_suppressed_by_email_hash_blocks_lead(self) -> None:
        agent = self._make_agent()
        email = "owner@detroitbest.com"
        lead = Lead(
            business="Detroit Best HVAC",
            domain="detroitbest.com",
            phone="313-555-0101",
            address="456 Gratiot Ave Detroit MI",
            industry="hvac",
            score="HOT",
            yelp_rating="4.7",
            sheet_row=11,
            owner_email=email,
        )
        h = hashlib.sha256(email.strip().lower().encode("utf-8")).hexdigest()
        hashes = {h}
        domains: set[str] = set()
        self.assertTrue(agent._is_lead_suppressed(lead, hashes, domains))

    def test_unsuppressed_lead_passes(self) -> None:
        agent = self._make_agent()
        lead = Lead(
            business="Clean Air HVAC",
            domain="cleanairhvac.com",
            phone="313-555-0102",
            address="789 Jefferson Ave Detroit MI",
            industry="hvac",
            score="HOT",
            yelp_rating="4.6",
            sheet_row=12,
            owner_email="owner@cleanairhvac.com",
        )
        hashes: set[str] = set()
        domains: set[str] = set()
        self.assertFalse(agent._is_lead_suppressed(lead, hashes, domains))

    # ------------------------------------------------------------------
    # _process_candidate — suppressed lead is rejected before queuing
    # ------------------------------------------------------------------

    def test_suppressed_lead_rejected_in_process_candidate(self) -> None:
        """A lead whose domain is in the suppression file must return
        FILTERED_OUT_SUPPRESSED and never reach the approval prompt."""
        agent = self._make_agent()

        entry = _make_suppression_entry(email="owner@blocked-domain.com", domain="blocked-domain.com")
        with tempfile.NamedTemporaryFile(suffix=".ndjson", mode="w", delete=False) as f:
            f.write(entry + "\n")
            tmp = Path(f.name)

        orig = sales_agent.SUPPRESSION_FILE
        sales_agent.SUPPRESSION_FILE = tmp

        approval_called = []

        class StubEngine:
            def acquire(self, prospect):  # noqa: ANN001
                return type("Acq", (), {"to_dict": staticmethod(lambda: {
                    "final_email": "owner@blocked-domain.com",
                    "email_classification": "OWNER_CONFIRMED",
                    "email_confidence": "HIGH",
                    "email_source_type": "structured_provider",
                    "email_source_reference": "owner_email",
                    "person_match_basis": "stub",
                    "verification_notes": "",
                    "rejection_reason": "",
                    "passes_ran": [],
                    "candidate_history": [],
                })})()

        class BlockedAgent(SalesAgent):
            def __init__(self_inner) -> None:
                super().__init__()
                self_inner.sheet_id = ""
                self_inner.service_account_json = ""
                self_inner.email_engine = StubEngine()
                self_inner._flow = type("Flow", (), {
                    "request_approval": staticmethod(lambda **kw: approval_called.append(True))
                })()

            def _persist_with_failsafe(self_inner, **kwargs): return "WRITTEN"
            def _telegram_confirm(self_inner, text): return None
            def _mark_notified(self_inner, sheet_row): return None
            def _attach_approval_buttons(self_inner, message_id): return None
            def _wait_for_callback(self_inner, message_id, timeout_seconds=600, poll_interval=3):
                approval_called.append(True)
                return sales_agent.ApprovalStatus.APPROVED

        try:
            blocked = BlockedAgent()
            lead = Lead(
                business="Blocked Plumbing Co",
                domain="blocked-domain.com",
                phone="313-555-9999",
                address="1 Blocked St Detroit MI",
                industry="hvac",
                score="HOT",
                yelp_rating="4.0",
                sheet_row=99,
                owner_email="owner@blocked-domain.com",
            )
            result = blocked._process_candidate(
                lead,
                summary=blocked._new_run_summary(),
                queue_index=set(),
                lead_ids_this_run={},
            )
            self.assertEqual(result["terminal_state"], "FILTERED_OUT_SUPPRESSED")
            self.assertFalse(result["selected"])
            self.assertEqual(approval_called, [], "Approval prompt must not be called for suppressed lead")
        finally:
            sales_agent.SUPPRESSION_FILE = orig
            tmp.unlink(missing_ok=True)

    # ------------------------------------------------------------------
    # _record_skip_suppression + canonical schema
    # ------------------------------------------------------------------

    def test_skip_writes_canonical_suppression_record(self) -> None:
        """After a SKIP, suppression record must have all canonical fields."""
        agent = self._make_agent()
        lead = Lead(
            business="Skip This Co",
            domain="skipthis.com",
            phone="313-555-0200",
            address="200 Skip Ave Detroit MI",
            industry="salon",
            score="HOT",
            yelp_rating="4.2",
            sheet_row=20,
            owner_email="owner@skipthis.com",
        )
        with tempfile.NamedTemporaryFile(suffix=".ndjson", mode="w", delete=False) as f:
            tmp = Path(f.name)

        orig = sales_agent.SUPPRESSION_FILE
        sales_agent.SUPPRESSION_FILE = tmp
        try:
            agent._record_skip_suppression(lead)
            lines = [l for l in tmp.read_text().splitlines() if l.strip()]
            self.assertEqual(len(lines), 1, "Exactly one suppression record should be written")
            record = json.loads(lines[0])
            # Canonical required fields
            self.assertIn("recipient_hash", record)
            self.assertIn("domain", record)
            self.assertIn("status", record)
            self.assertIn("reason", record)
            self.assertIn("date_added", record)
            self.assertIn("source", record)
            # Values
            self.assertEqual(record["status"], "skip")
            self.assertEqual(record["domain"], "skipthis.com")
            self.assertEqual(record["source"], "sales_agent")
            expected_hash = hashlib.sha256("owner@skipthis.com".encode("utf-8")).hexdigest()
            self.assertEqual(record["recipient_hash"], expected_hash)
        finally:
            sales_agent.SUPPRESSION_FILE = orig
            tmp.unlink(missing_ok=True)

    def test_resend_canonical_schema_uses_date_added(self) -> None:
        """resend_delivery_sync suppression records must use date_added not recorded_at."""
        import importlib.util as ilu
        sync_path = ROOT / "project9-sales-agent" / "scripts" / "resend_delivery_sync.py"
        spec2 = ilu.spec_from_file_location("resend_delivery_sync", sync_path)
        sync = ilu.module_from_spec(spec2)
        spec2.loader.exec_module(sync)

        with tempfile.NamedTemporaryFile(suffix=".ndjson", mode="w", delete=False) as f:
            tmp = Path(f.name)
        try:
            sync._append_suppression_entry(
                tmp,
                recipient_hash="abc123",
                status="hard_bounce",
                reason="resend_status=bounced",
                resend_id="re_test001",
            )
            record = json.loads(tmp.read_text().strip())
            self.assertIn("date_added", record, "Must use date_added (canonical field)")
            self.assertNotIn("recorded_at", record, "recorded_at is deprecated — must not appear")
        finally:
            tmp.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
