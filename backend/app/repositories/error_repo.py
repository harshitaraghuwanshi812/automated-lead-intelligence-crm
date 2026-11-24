import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from app.database import execute_query, fetch_one, fetch_all

def create_automation_job(
    workflow_name: str,
    job_type: str,
    correlation_id: str,
    input_payload: Dict[str, Any] = None,
    max_attempts: int = 3
) -> Dict[str, Any]:
    new_id = str(uuid.uuid4())
    sql = """
    INSERT INTO automation_jobs (
        id, workflow_name, job_type, correlation_id, status,
        attempts, max_attempts, input_payload, started_at
    ) VALUES (%s, %s, %s, %s, 'running', 1, %s, %s, (NOW() AT TIME ZONE 'utc'))
    """
    execute_query(sql, [new_id, workflow_name, job_type, correlation_id, max_attempts, json.dumps(input_payload or {})])
    return fetch_one("SELECT * FROM automation_jobs WHERE id = %s", [new_id]) or {
        "id": new_id, "workflow_name": workflow_name, "correlation_id": correlation_id, "status": "running"
    }

def update_job_status(
    job_id: str,
    status: str,
    output_payload: Dict[str, Any] = None,
    next_retry_at: Optional[datetime] = None
):
    sql = """
    UPDATE automation_jobs
    SET status = %s, output_payload = %s, next_retry_at = %s,
        completed_at = CASE WHEN %s IN ('completed', 'failed') THEN (NOW() AT TIME ZONE 'utc') ELSE completed_at END
    WHERE id = %s
    """
    execute_query(sql, [status, json.dumps(output_payload or {}), next_retry_at.isoformat() if next_retry_at else None, status, job_id])

def record_automation_error(
    correlation_id: str,
    workflow_name: str,
    failed_step: str,
    failure_category: str,
    error_message: str,
    job_id: Optional[str] = None,
    stack_trace: Optional[str] = None,
    is_replay_eligible: bool = True
) -> Dict[str, Any]:
    new_id = str(uuid.uuid4())
    sql = """
    INSERT INTO automation_errors (
        id, job_id, correlation_id, workflow_name, failed_step,
        failure_category, error_message, stack_trace, is_replay_eligible,
        retry_count, recovery_status
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 0, 'unresolved')
    """
    execute_query(sql, [
        new_id, job_id, correlation_id, workflow_name, failed_step,
        failure_category, error_message, stack_trace, is_replay_eligible
    ])
    return fetch_one("SELECT * FROM automation_errors WHERE id = %s", [new_id]) or {
        "id": new_id, "correlation_id": correlation_id, "workflow_name": workflow_name,
        "failed_step": failed_step, "failure_category": failure_category, "recovery_status": "unresolved"
    }

def list_automation_errors(
    recovery_status: Optional[str] = None,
    failure_category: Optional[str] = None
) -> List[Dict[str, Any]]:
    sql = "SELECT * FROM automation_errors ORDER BY created_at DESC LIMIT 100"
    rows = fetch_all(sql)
    results = []
    for r in rows:
        if recovery_status and recovery_status != "all":
            if r.get("recovery_status") != recovery_status:
                continue
        if failure_category and failure_category != "all":
            if r.get("failure_category") != failure_category:
                continue
        results.append(r)
    return results

def get_automation_error(error_id: str) -> Optional[Dict[str, Any]]:
    sql = "SELECT * FROM automation_errors WHERE id = %s"
    return fetch_one(sql, [error_id])

def resolve_automation_error(
    error_id: str,
    resolution_notes: Optional[str],
    new_status: str = "resolved"
):
    sql = """
    UPDATE automation_errors
    SET recovery_status = %s, resolution_notes = %s, resolved_at = (NOW() AT TIME ZONE 'utc')
    WHERE id = %s
    """
    execute_query(sql, [new_status, resolution_notes, error_id])
