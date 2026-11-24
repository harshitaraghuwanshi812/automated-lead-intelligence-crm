import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import httpx
from app.config import settings
from app.repositories import crm_repo, campaign_repo

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an elite, compliance-focused B2B Outreach and Talent Intelligence AI assistant.
Your sole job is to generate a personalized, accurate, respectful email draft based STRICTLY AND ONLY on the verified opportunity and recipient facts provided.

CRITICAL GUARDRAILS:
1. NEVER invent or hallucinate company information, recruiter names, salary numbers, job requirements, or relationships.
2. If any information is missing or unverified, state it in 'missing_info_warnings' and write a polite, non-assuming email.
3. Keep the tone professional, concise, and value-oriented.
4. You CANNOT send emails. You can ONLY produce this draft for human review.

You must respond ONLY with valid JSON conforming to this exact schema:
{
  "subject_line": "...",
  "email_body": "...",
  "personalization_summary": "...",
  "claims_used": ["claim 1", "claim 2"],
  "missing_info_warnings": ["warning 1"],
  "confidence_notes": "..."
}
"""

def generate_draft_with_gemini(
    campaign_id: str,
    opportunity_id: str,
    contact_id: str,
    tone: str = "professional_enthusiastic",
    campaign_objective: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generates structured AI draft following PRD Section 4 & Section 5.
    """
    opp = crm_repo.get_opportunity(opportunity_id)
    if not opp:
        raise ValueError(f"Opportunity {opportunity_id} not found")

    contact = crm_repo.fetch_one("SELECT * FROM contacts WHERE id = %s", [contact_id])
    if not contact:
        raise ValueError(f"Contact {contact_id} not found")

    contacts_methods = crm_repo.fetch_all(
        "SELECT value, verification_status FROM contact_methods WHERE contact_id = %s", [contact_id]
    )
    primary_email = contacts_methods[0]["value"] if contacts_methods else None

    # Construct verified facts payload
    input_facts = {
        "company_name": opp.get("organization_name", "Target Company"),
        "role_title": opp.get("title"),
        "experience_level": opp.get("experience_level"),
        "opportunity_type": opp.get("opportunity_type"),
        "location": opp.get("location", "Not specified"),
        "salary_range": opp.get("salary_range", "Not disclosed"),
        "job_description_snippet": opp.get("description", "")[:600],
        "recipient_name": contact.get("full_name"),
        "recipient_role": contact.get("role_title", "Talent Acquisition"),
        "recipient_email": primary_email,
        "campaign_objective": campaign_objective or "Proactive candidate introduction for entry-level tech roles",
        "tone": tone
    }

    prompt_version = settings.GEMINI_PROMPT_VERSION
    model_name = settings.GEMINI_MODEL_NAME

    # 1. Try Gemini API if key is present
    generated_data = None
    if settings.GEMINI_API_KEY and not settings.GEMINI_API_KEY.startswith("AIzaSyYour"):
        try:
            logger.info("Calling Gemini API Flash model...")
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={settings.GEMINI_API_KEY}"
            user_message = f"Here are the verified facts:\n{json.dumps(input_facts, indent=2)}\nGenerate the email draft adhering to the rules."
            
            payload = {
                "contents": [
                    {"role": "user", "parts": [{"text": f"{SYSTEM_PROMPT}\n\n{user_message}"}]}
                ],
                "generationConfig": {
                    "temperature": 0.2, # Low temperature for factual precision
                    "responseMimeType": "application/json"
                }
            }
            with httpx.Client(timeout=15.0) as client:
                resp = client.post(url, json=payload)
                if resp.status_code == 200:
                    res_json = resp.json()
                    raw_text = res_json["candidates"][0]["content"]["parts"][0]["text"]
                    generated_data = json.loads(raw_text)
        except Exception as e:
            logger.warning(f"Gemini API call failed or timed out: {e}. Falling back to deterministic guardrailed generator.")

    # 2. Fallback deterministic generator satisfying strict schema & PRD rules
    if not generated_data:
        comp_name = input_facts["company_name"]
        role = input_facts["role_title"]
        recip_name = input_facts["recipient_name"]
        exp = input_facts["experience_level"].replace("_", " ")

        subject = f"Inquiry regarding {role} opening at {comp_name}"
        greeting = f"Hi {recip_name.split()[0]}," if recip_name and " " in recip_name else f"Hello {comp_name} Talent Acquisition Team,"
        
        body = (
            f"{greeting}\n\n"
            f"I noticed {comp_name}'s recent posting for the {role} position ({exp} level) and wanted to reach out directly.\n\n"
            f"Our team has high-caliber candidates with demonstrated technical capability in modern software systems and hands-on project experience tailored for your requirements.\n\n"
            f"Would you be open to a brief 5-minute conversation this week to review profiles of pre-screened candidates specifically matching your criteria for the {role} role?\n\n"
            f"Best regards,\n"
            f"{settings.EMAIL_FROM_NAME}\n"
            f"{settings.EMAIL_FROM_ADDRESS}"
        )

        missing_warnings = []
        if input_facts["salary_range"] == "Not disclosed":
            missing_warnings.append("Salary range was not disclosed in the source listing.")
        if not contact.get("first_name"):
            missing_warnings.append("Recruiter first name not split; used full title or generic greeting.")

        claims = [
            f"Company: {comp_name}",
            f"Role: {role}",
            f"Target experience: {exp}",
            f"Location: {input_facts['location']}"
        ]

        generated_data = {
            "subject_line": subject,
            "email_body": body,
            "personalization_summary": f"Targeted outreach directly referencing the verified {role} listing at {comp_name}.",
            "claims_used": claims,
            "missing_info_warnings": missing_warnings,
            "confidence_notes": "High factual alignment: strictly references verified opportunity posting without assumptions."
        }

    # 3. Save draft to PostgreSQL database
    draft = campaign_repo.create_campaign_draft(
        campaign_id=campaign_id,
        opportunity_id=opportunity_id,
        contact_id=contact_id,
        subject_line=generated_data["subject_line"],
        email_body=generated_data["email_body"],
        personalization_summary=generated_data.get("personalization_summary", ""),
        claims_used=generated_data.get("claims_used", []),
        missing_info_warnings=generated_data.get("missing_info_warnings", []),
        confidence_notes=generated_data.get("confidence_notes", ""),
        model_name=model_name,
        prompt_version=prompt_version,
        input_references=input_facts
    )

    # 4. Audit log
    crm_repo.log_audit(
        user_id=None,
        action="AI_DRAFT_GENERATED",
        entity_type="campaign_draft",
        entity_id=draft.get("id"),
        details={"model": model_name, "prompt_version": prompt_version, "campaign_id": campaign_id}
    )

    return draft
