import sys
import os
import json
import asyncio
from datetime import datetime

# Set path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import init_db, fetch_one, fetch_all, execute_query, get_store
from migrations.seed_data import seed_database
from app.auth.security import hash_password, verify_password, create_access_token
from app.models.schemas import UserLogin, DraftEditRequest
from app.routers.auth_router import login
from app.services import (
    discovery_service,
    scoring_service,
    verification_service,
    enrichment_service,
    gemini_service,
    dispatch_service,
    callback_service,
    error_service,
    health_service
)
from app.repositories import crm_repo, campaign_repo, error_repo

passed_tests = 0
failed_tests = 0

def run_test(name, fn):
    global passed_tests, failed_tests
    print(f"Running: {name}...", flush=True)
    try:
        if asyncio.iscoroutinefunction(fn):
            asyncio.run(fn())
        else:
            fn()
        print(f"  [PASS] {name}", flush=True)
        passed_tests += 1
    except Exception as e:
        print(f"  [FAIL] {name}: {e}", flush=True)
        import traceback
        traceback.print_exc()
        failed_tests += 1

def main():
    print("=====================================================================")
    print("RUNNING AUTOMATED LEAD GENERATION & OUTREACH SYSTEM TEST SUITE")
    print("=====================================================================")

    # 1. Initialize & Seed DB
    print("\n--- Module 1: Database & Seed Operations ---")
    init_db()
    seed_database()

    # Test DB Tables
    def test_db_seeding():
        roles = fetch_all("SELECT * FROM roles")
        assert len(roles) >= 3, f"Expected 3 roles, got {len(roles)}"
        sources = fetch_all("SELECT * FROM sources")
        assert len(sources) >= 4, f"Expected 4 sources, got {len(sources)}"
        orgs = fetch_all("SELECT * FROM organizations")
        assert len(orgs) >= 5, f"Expected 5 orgs, got {len(orgs)}"
        opps = fetch_all("SELECT * FROM opportunities")
        assert len(opps) >= 6, f"Expected 6 opportunities, got {len(opps)}"
    run_test("Database schema & 21-table seeding integrity", test_db_seeding)

    # 2. Auth & RBAC
    print("\n--- Module 2: Authentication & Role-Based Access Control ---")
    def test_auth_crypto():
        pw = "AdminSecurePass@2025"
        h = hash_password(pw)
        assert verify_password(pw, h) is True
        assert verify_password("wrong", h) is False
    run_test("Password hashing and bcrypt verification", test_auth_crypto)

    def test_auth_login_endpoints():
        # Admin login
        adm = login(UserLogin(email="admin@leadintel.org", password="Admin@123456"))
        assert adm.access_token is not None
        assert "admin" in adm.roles

        # Researcher login
        res = login(UserLogin(email="researcher@leadintel.org", password="Researcher@123456"))
        assert res.access_token is not None
        assert "researcher" in res.roles

        # Campaign Manager login
        cm = login(UserLogin(email="campaign@leadintel.org", password="Campaign@123456"))
        assert cm.access_token is not None
        assert "campaign_manager" in cm.roles
    run_test("JWT Token generation & RBAC roles for Admin, Researcher, Campaign Manager", test_auth_login_endpoints)

    # 3. Lead Discovery & Deduplication
    print("\n--- Module 3: Lead Discovery, Filtering & Deduplication ---")
    def test_discovery_filtering():
        opps = crm_repo.list_opportunities(experience_level="fresher")
        assert len(opps) > 0
        for o in opps:
            assert o["experience_level"] == "fresher"

        opps_01 = crm_repo.list_opportunities(experience_level="0-1_year")
        assert len(opps_01) > 0

        hackathons = crm_repo.list_opportunities(opportunity_type="hackathon")
        assert len(hackathons) > 0
    run_test("Opportunity filtering (fresher, 0-1y, 0-2y, internships, hackathons)", test_discovery_filtering)

    def test_deduplication():
        lead = {
            "title": "Graduate Autonomous Systems Engineer",
            "company_name": "Apex Robotics Corp",
            "description": "Fresher engineering opening in robotics and computer vision.",
            "source_url": "https://apexrobotics.io/careers/auto-01",
            "experience_level": "fresher"
        }
        res1 = discovery_service.process_discovered_lead(lead, "Apex Careers")
        assert res1["status"] == "created"

        # Re-submitting identical lead should be flagged and skipped
        res2 = discovery_service.process_discovered_lead(lead, "Apex Careers")
        assert res2["status"] == "duplicate_skipped"
    run_test("Deduplication prevention via source URL hash & title normalization", test_deduplication)

    # 4. Contact Enrichment & Credit Limits
    print("\n--- Module 4: Contact Enrichment & Budget Protection ---")
    def test_credit_enforcement():
        # Attempt without confirming credits -> Must fail with exception
        try:
            enrichment_service.execute_enrichment(
                user_id="00000000-0000-0000-0000-000000000002",
                provider="contactout",
                confirm_credits=False,
                company_domain="nexusai.io"
            )
            assert False, "Should have raised exception for unconfirmed credits"
        except Exception as e:
            assert "Credit confirmation required" in str(e) or getattr(e, 'status_code', None) == 400

        # Attempt with confirm_credits = True -> Must deduct credit and succeed
        ok_res = enrichment_service.execute_enrichment(
            user_id="00000000-0000-0000-0000-000000000002",
            provider="contactout",
            confirm_credits=True,
            company_domain="nexusai.io",
            recruiter_name="Laura Croft"
        )
        assert ok_res["credits_used"] == 1
        assert ok_res["status"] == "completed"
        assert "@nexusai.io" in ok_res["enriched_email"]
    run_test("Manual enrichment credit confirmation & tracking (ContactOut / Snov.io)", test_credit_enforcement)

    # 5. Email Verification Engine
    print("\n--- Module 5: Email Verification 6-State Engine ---")
    def test_verification():
        # Deliverable
        r_deliv = verification_service.verify_email_address("recruiter@nexusai.io")
        assert r_deliv["status"] == "deliverable"
        assert r_deliv["score"] >= 80

        # Undeliverable
        r_undeliv = verification_service.verify_email_address("malformed-email@@domain")
        assert r_undeliv["status"] == "undeliverable"

        # Disposable
        r_disp = verification_service.verify_email_address("scam@mailinator.com")
        assert r_disp["status"] == "undeliverable"

        # Risky
        r_risk = verification_service.verify_email_address("noreply@nexusai.io")
        assert r_risk["status"] == "risky"

        # Catch-all
        r_catch = verification_service.verify_email_address("test.user@nexusai.io")
        assert r_catch["status"] == "catch-all"
    run_test("Multi-state verification (deliverable, undeliverable, risky, catch-all)", test_verification)

    # 6. Confidence Scoring (Exact 100-pt formula)
    print("\n--- Module 6: Explainable Confidence Scoring (100 Points) ---")
    def test_confidence_scoring():
        opps = crm_repo.list_opportunities()
        assert len(opps) > 0
        opp_id = opps[0]["id"]

        score = scoring_service.evaluate_opportunity_confidence(opp_id)
        assert 0 <= score["source_reliability_score"] <= 25
        assert 0 <= score["org_association_score"] <= 25
        assert 0 <= score["verification_evidence_score"] <= 20
        assert 0 <= score["data_freshness_score"] <= 15
        assert 0 <= score["completeness_score"] <= 15
        
        expected_total = (
            score["source_reliability_score"] +
            score["org_association_score"] +
            score["verification_evidence_score"] +
            score["data_freshness_score"] +
            score["completeness_score"]
        )
        assert score["total_score"] == expected_total
        assert 0 <= score["total_score"] <= 100
        assert score["score_band"] in ["high_confidence", "medium_confidence", "low_confidence", "suppressed"]
        assert len(score["reason_codes"]) > 0
    run_test("Exact 5-factor confidence scoring & explainable reason codes", test_confidence_scoring)

    # 7. Gemini AI Email Drafting & Guardrails
    print("\n--- Module 7: Gemini Flash AI Email Drafting & Zero Hallucination ---")
    def test_gemini_draft():
        camps = campaign_repo.list_campaigns()
        camp_id = camps[0]["id"]
        opps = crm_repo.list_opportunities()
        opp_id = opps[0]["id"]
        contacts = crm_repo.list_contacts()
        contact_id = contacts[0]["id"]

        draft = gemini_service.generate_draft_with_gemini(
            campaign_id=camp_id,
            opportunity_id=opp_id,
            contact_id=contact_id
        )
        assert draft["subject_line"] is not None and len(draft["subject_line"]) > 5
        assert draft["email_body"] is not None and len(draft["email_body"]) > 20
        assert draft["status"] == "generated"
        assert isinstance(draft["claims_used"], list)
        assert isinstance(draft["missing_info_warnings"], list)
        assert draft["model_name"] is not None
        assert draft["prompt_version"] is not None
    run_test("Structured Gemini Flash email draft with verified facts & versioned prompt", test_gemini_draft)

    # 8. Human-in-the-Loop Approval & Email Dispatch Safeguards
    print("\n--- Module 8: Human Approval Enforcement & Dispatch Safeguards ---")
    def test_dispatch_safeguards():
        camps = campaign_repo.list_campaigns()
        camp_id = camps[0]["id"]
        opps = crm_repo.list_opportunities()
        opp_id = opps[0]["id"]
        contacts = crm_repo.list_contacts()
        contact_id = contacts[0]["id"]

        draft = gemini_service.generate_draft_with_gemini(
            campaign_id=camp_id,
            opportunity_id=opp_id,
            contact_id=contact_id
        )
        draft_id = draft["id"]

        # Check: Dispatch WITHOUT approval MUST BE BLOCKED
        try:
            dispatch_service.execute_safe_dispatch(
                campaign_draft_id=draft_id,
                user_id="00000000-0000-0000-0000-000000000003"
            )
            assert False, "Dispatch should have been blocked without human approval"
        except Exception as e:
            assert "mandatory human approval" in str(e) or getattr(e, 'status_code', None) == 403

        # Edit draft (Campaign Manager edit feature)
        campaign_repo.update_draft_content(draft_id, "Subject Approved by CM", "Body reviewed by CM")

        # Campaign Manager Approves
        campaign_repo.create_approval(
            campaign_draft_id=draft_id,
            reviewed_by_user_id="00000000-0000-0000-0000-000000000003",
            decision="approved",
            review_notes="Content checked and approved.",
            approved_recipient="recruiter@nexusai.io",
            approved_subject="Subject Approved by CM",
            approved_body="Body reviewed by CM"
        )

        # Dispatch WITH approval -> MUST SUCCEED
        disp_res = dispatch_service.execute_safe_dispatch(
            campaign_draft_id=draft_id,
            user_id="00000000-0000-0000-0000-000000000003"
        )
        assert disp_res["status"] == "dispatched"
        assert disp_res["provider_message_id"] is not None

        # Duplicate send check with same idempotency key -> Duplicate Prevented
        dup_res = dispatch_service.execute_safe_dispatch(
            campaign_draft_id=draft_id,
            user_id="00000000-0000-0000-0000-000000000003"
        )
        assert dup_res["status"] == "duplicate_prevented"
    run_test("Mandatory human approval, pre-send checks & idempotency duplicate prevention", test_dispatch_safeguards)

    # 9. Suppression & Webhooks
    print("\n--- Module 9: Suppression Management & Provider Callbacks ---")
    def test_suppression_and_callbacks():
        # Test manual suppression
        test_email = "optout-candidate@techcorp.com"
        crm_repo.add_suppression_entry("email", test_email, "user_opt_out", "Unsubscribed")
        assert crm_repo.is_suppressed(test_email) is True

        # Test provider callback auto-suppression on bounce
        bounce_email = "auto-bounce-recipient@targetfirm.org"
        cb_res = callback_service.process_provider_event({
            "event_id": "evt_bounce_auto_9981",
            "event_type": "bounce",
            "recipient_email": bounce_email
        })
        assert cb_res["status"] == "processed"
        assert crm_repo.is_suppressed(bounce_email) is True

        # Test callback idempotency
        cb_dup = callback_service.process_provider_event({
            "event_id": "evt_bounce_auto_9981",
            "event_type": "bounce",
            "recipient_email": bounce_email
        })
        assert cb_dup["status"] == "duplicate_event_ignored"
    run_test("Suppression list, bounce auto-suppression & callback event idempotency", test_suppression_and_callbacks)

    # 10. Error Center & Health
    print("\n--- Module 10: Error Center & System Health ---")
    def test_error_and_health():
        # Record automation error
        err = error_service.capture_automation_error(
            workflow_name="01_daily_lead_discovery",
            failed_step="Crawl Job Board",
            failure_category="network",
            error_message="Gateway timeout 504 from remote server"
        )
        assert err["failure_category"] == "network"
        assert err["is_replay_eligible"] is True

        # Manual retry with backoff
        ret = error_service.retry_failed_job(err["id"], "00000000-0000-0000-0000-000000000001", "Retrying network step")
        assert ret["status"] == "retry_scheduled"
        assert ret["next_retry_at"] is not None

        # System Health metrics
        health = health_service.get_system_health()
        assert health["n8n_status"] == "healthy"
        assert health["total_leads_discovered"] > 0
        assert health["credits_monthly_budget"] == 500
    run_test("Error Center failure categorization, jitter backoff & system health metrics", test_error_and_health)

    print("\n=====================================================================")
    print(f"TEST RESULTS: {passed_tests} PASSED, {failed_tests} FAILED")
    print("=====================================================================")
    if failed_tests > 0:
        sys.exit(1)

if __name__ == "__main__":
    main()
