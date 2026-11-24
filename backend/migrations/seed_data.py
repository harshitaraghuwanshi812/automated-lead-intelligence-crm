import uuid
import json
from datetime import datetime, timezone, timedelta
from app.database import get_db_connection, execute_query, fetch_one, fetch_all, get_store
from app.auth.security import hash_password

def seed_database():
    """Seeds initial demonstration data satisfying all 18 pages of the PRD requirements."""
    # Check if already seeded
    existing_roles = fetch_all("SELECT id FROM roles")
    if existing_roles:
        return

    print("Seeding CRM Database with realistic opportunity and role data...")

    # 1. ROLES
    roles_data = [
        ("admin", "Full administrative access to manage users, sources, and configurations", ["all"]),
        ("researcher", "Lead discovery review, contact enrichment, and data validation", ["view_leads", "enrich_contact", "verify_email"]),
        ("campaign_manager", "Campaign management, draft review/editing, and send approval", ["view_campaigns", "edit_draft", "approve_send", "manage_suppression"])
    ]
    role_map = {}
    for name, desc, perms in roles_data:
        rid = str(uuid.uuid4())
        execute_query(
            "INSERT INTO roles (id, name, description, permissions) VALUES (%s, %s, %s, %s)",
            [rid, name, desc, json.dumps(perms)]
        )
        role_map[name] = rid

    # 2. USERS
    admin_id = "00000000-0000-0000-0000-000000000001"
    researcher_id = "00000000-0000-0000-0000-000000000002"
    campaign_mgr_id = "00000000-0000-0000-0000-000000000003"

    users_data = [
        (admin_id, "admin@leadintel.org", "Admin@123456", "System Administrator", "admin"),
        (researcher_id, "researcher@leadintel.org", "Researcher@123456", "Lead Intelligence Researcher", "researcher"),
        (campaign_mgr_id, "campaign@leadintel.org", "Campaign@123456", "Outreach Campaign Manager", "campaign_manager")
    ]
    for uid, email, pw, name, role_name in users_data:
        execute_query(
            "INSERT INTO users (id, email, password_hash, full_name, is_active) VALUES (%s, %s, %s, %s, TRUE)",
            [uid, email, hash_password(pw), name]
        )
        execute_query(
            "INSERT INTO user_roles (user_id, role_id) VALUES (%s, %s)",
            [uid, role_map[role_name]]
        )

    # 3. APPROVED SOURCES
    sources_data = [
        ("Official Greenhouse Careers Portal", "https://boards.greenhouse.io", "company_careers", 25),
        ("Lever Verified Job Boards", "https://jobs.lever.co", "company_careers", 25),
        ("Unstop Hackathons & Student Challenges", "https://unstop.com/hackathons", "hackathon_platform", 22),
        ("Early Careers Open Board", "https://jobs.earlycareer.org", "job_board", 20)
    ]
    source_map = {}
    for name, base_url, stype, weight in sources_data:
        sid = str(uuid.uuid4())
        execute_query(
            "INSERT INTO sources (id, name, base_url, source_type, reliability_weight, is_approved) VALUES (%s, %s, %s, %s, %s, TRUE)",
            [sid, name, base_url, stype, weight]
        )
        source_map[name] = sid

    # 4. ORGANIZATIONS
    orgs_data = [
        ("Nexus AI Systems", "nexusai.io", "Artificial Intelligence", "50-200", "https://nexusai.io", "San Francisco, CA"),
        ("CloudScale Infrastructure", "cloudscale.tech", "Cloud & DevOps", "200-500", "https://cloudscale.tech", "Austin, TX"),
        ("DataFlow Analytics", "dataflow.dev", "Big Data & ML", "10-50", "https://dataflow.dev", "New York, NY"),
        ("FinLeap Technologies", "finleap.co", "FinTech", "100-250", "https://finleap.co", "Chicago, IL"),
        ("CyberShield Security", "cybershield.io", "Cybersecurity", "500+", "https://cybershield.io", "Boston, MA")
    ]
    org_map = {}
    for name, domain, ind, size, web, loc in orgs_data:
        oid = str(uuid.uuid4())
        execute_query(
            "INSERT INTO organizations (id, name, normalized_name, domain, industry, size_range, website_url, location) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
            [oid, name, name.lower().replace(" ", ""), domain, ind, size, web, loc]
        )
        org_map[name] = oid

    # 5. OPPORTUNITIES (Covering fresher, no_experience, 0-1_year, 0-2_years, internship, hackathon)
    opps_data = [
        (
            "Junior Full-Stack Engineer (Fresher / 2024-2025)",
            org_map["Nexus AI Systems"],
            "Seeking talented fresher graduates with strong proficiency in Python, React, and REST APIs. Mentorship provided.",
            "job", "fresher", "San Francisco, CA (Hybrid)", "$85,000 - $105,000",
            source_map["Official Greenhouse Careers Portal"], "https://boards.greenhouse.io/nexusai/jobs/401", "nexus-401", 85
        ),
        (
            "Software Development Engineer I (0-1 Year Experience)",
            org_map["CloudScale Infrastructure"],
            "Entry-level engineering role for candidates with 0-1 year hands-on experience or exceptional open-source contributions in Go/Python.",
            "job", "0-1_year", "Austin, TX (Remote)", "$90,000 - $110,000",
            source_map["Lever Verified Job Boards"], "https://jobs.lever.co/cloudscale/102", "cs-102", 90
        ),
        (
            "Associate Backend Developer (No Experience Required)",
            org_map["DataFlow Analytics"],
            "Entry gateway for passionate coders. No prior professional experience required. Requires passing our algorithmic coding assessment.",
            "job", "no_experience", "New York, NY", "$80,000 - $95,000",
            source_map["Early Careers Open Board"], "https://jobs.earlycareer.org/dataflow/backend-0exp", "df-backend-0", 75
        ),
        (
            "Junior Frontend Developer (0-2 Years Experience)",
            org_map["FinLeap Technologies"],
            "Join our web frontend team building financial dashboards in React, TypeScript, and Tailwind CSS. 0-2 years experience.",
            "job", "0-2_years", "Chicago, IL", "$88,000 - $105,000",
            source_map["Official Greenhouse Careers Portal"], "https://boards.greenhouse.io/finleap/jobs/205", "finleap-205", 82
        ),
        (
            "Summer AI Research & Engineering Internship",
            org_map["Nexus AI Systems"],
            "Paid 12-week summer internship for university students focusing on generative AI evaluations and prompt orchestration.",
            "internship", "fresher", "Remote", "$45/hr",
            source_map["Official Greenhouse Careers Portal"], "https://boards.greenhouse.io/nexusai/internships/05", "nexus-intern-05", 88
        ),
        (
            "Global Generative AI Innovation Hackathon 2025",
            org_map["CyberShield Security"],
            "Competitive hackathon with $50,000 in prizes and fast-track interviews for entry-level security engineering roles.",
            "hackathon", "fresher", "Virtual / Global", "$50,000 Prize Pool",
            source_map["Unstop Hackathons & Student Challenges"], "https://unstop.com/hackathons/cybershield-2025", "unstop-cs-2025", 92
        )
    ]
    opp_map = {}
    for title, oid, desc, otype, exp, loc, sal, sid, surl, sident, cscore in opps_data:
        opid = str(uuid.uuid4())
        execute_query(
            """INSERT INTO opportunities (
                id, organization_id, title, description, opportunity_type, experience_level,
                location, salary_range, source_id, source_url, source_identifier,
                status, confidence_score, publication_date
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'ready_for_draft', %s, (NOW() AT TIME ZONE 'utc'))""",
            [opid, oid, title, desc, otype, exp, loc, sal, sid, surl, sident, cscore]
        )
        opp_map[title] = opid

    # 6. CONTACTS & METHODS
    contacts_data = [
        (org_map["Nexus AI Systems"], "Sarah Jenkins", "Sarah", "Jenkins", "Lead Technical Recruiter", "Talent Acquisition", "sarah.jenkins@nexusai.io", "deliverable", 95),
        (org_map["CloudScale Infrastructure"], "Marcus Vance", "Marcus", "Vance", "Head of Engineering Talent", "People Ops", "marcus.v@cloudscale.tech", "deliverable", 90),
        (org_map["DataFlow Analytics"], "Elena Rostova", "Elena", "Rostova", "Talent Scout", "HR", "elena@dataflow.dev", "catch-all", 65),
        (org_map["FinLeap Technologies"], "David Kim", "David", "Kim", "Senior Technical Recruiter", "Recruiting", "dkim@finleap.co", "deliverable", 88)
    ]
    for oid, fname, first, last, role, dept, email, vstatus, cscore in contacts_data:
        cid = str(uuid.uuid4())
        execute_query(
            """INSERT INTO contacts (
                id, organization_id, full_name, first_name, last_name, role_title,
                department, source, verification_status, confidence_score
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, 'official_channel', %s, %s)""",
            [cid, oid, fname, first, last, role, dept, vstatus, cscore]
        )
        cmid = str(uuid.uuid4())
        execute_query(
            """INSERT INTO contact_methods (
                id, contact_id, method_type, value, is_primary, verification_status
            ) VALUES (%s, %s, 'email', %s, TRUE, %s)""",
            [cmid, cid, email, vstatus]
        )
        
        # Link to matching opportunity
        if "Nexus" in fname or "Jenkins" in fname:
            target_opp = opp_map["Junior Full-Stack Engineer (Fresher / 2024-2025)"]
            execute_query(
                "INSERT INTO opportunity_contacts (id, opportunity_id, contact_id, role_in_opportunity, association_confidence) VALUES (%s, %s, %s, 'recruiter', 25)",
                [str(uuid.uuid4()), target_opp, cid]
            )
        elif "Marcus" in fname:
            target_opp = opp_map["Software Development Engineer I (0-1 Year Experience)"]
            execute_query(
                "INSERT INTO opportunity_contacts (id, opportunity_id, contact_id, role_in_opportunity, association_confidence) VALUES (%s, %s, %s, 'recruiter', 25)",
                [str(uuid.uuid4()), target_opp, cid]
            )

    # 7. CAMPAIGN
    camp_id = str(uuid.uuid4())
    execute_query(
        """INSERT INTO campaigns (
            id, name, description, objective, status, daily_limit, monthly_limit, sent_count, created_by_user_id
        ) VALUES (%s, %s, %s, %s, 'active', 50, 1000, 12, %s)""",
        [
            camp_id,
            "Q1 2025 University & Fresher Placement Campaign",
            "Targeting verified recruiter contacts for 2025 entry-level engineering and internship openings.",
            "Connect pre-screened junior engineering talent directly with hiring recruiters.",
            campaign_mgr_id
        ]
    )

    # 8. SUPPRESSION ENTRIES
    suppressions = [
        ("email", "optout.candidate@nexusai.io", "user_opt_out", "Clicked unsubscribe link in email"),
        ("email", "bad-bounce@fakedomain.com", "hard_bounce", "Permanent 550 Mailbox does not exist error"),
        ("domain", "do-not-contact-corp.com", "manual_block", "Enterprise customer requested exclusion")
    ]
    for stype, val, reason, notes in suppressions:
        execute_query(
            "INSERT INTO suppression_entries (id, entity_type, value, reason, notes) VALUES (%s, %s, %s, %s, %s)",
            [str(uuid.uuid4()), stype, val, reason, notes]
        )

    # 9. SAMPLE AUTOMATION ERRORS FOR ERROR CENTER
    errs_data = [
        ("01_daily_lead_discovery", "Playwright Page Navigation", "network", "Connection reset while fetching open career board index", True),
        ("03_manual_enrichment", "ContactOut API Rate Limiting", "rate_limit", "Provider returned 429 Too Many Requests; threshold reached", True),
        ("05_ai_draft_generation", "Schema Validation Check", "ai_output", "Missing claims_used array in model JSON payload", True)
    ]
    for wname, fstep, cat, emsg, replay in errs_data:
        execute_query(
            """INSERT INTO automation_errors (
                id, correlation_id, workflow_name, failed_step, failure_category,
                error_message, is_replay_eligible, retry_count, recovery_status
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, 1, 'unresolved')""",
            [str(uuid.uuid4()), f"corr_{uuid.uuid4().hex[:10]}", wname, fstep, cat, emsg, replay]
        )

    print("Seed data loaded successfully!")
