import logging
import json
import uuid
from datetime import datetime, timezone
from contextlib import contextmanager
from typing import Any, Dict, List, Optional, Tuple, Union
from app.config import settings

logger = logging.getLogger(__name__)

# Global pool instance
_pool = None
_local_db = None

class LocalDBStore:
    """
    Lightweight in-memory relational store compatible with direct parameterized SQL
    for development/testing when a live remote Neon PostgreSQL instance is not connected.
    """
    def __init__(self):
        self.tables: Dict[str, List[Dict[str, Any]]] = {
            "users": [],
            "roles": [],
            "user_roles": [],
            "organizations": [],
            "opportunities": [],
            "sources": [],
            "contacts": [],
            "contact_methods": [],
            "opportunity_contacts": [],
            "enrichment_requests": [],
            "verification_results": [],
            "data_quality_scores": [],
            "campaigns": [],
            "campaign_drafts": [],
            "approvals": [],
            "outreach_messages": [],
            "message_events": [],
            "suppression_entries": [],
            "automation_jobs": [],
            "automation_errors": [],
            "audit_logs": []
        }
        self.transaction_snapshot = None

    def begin(self):
        self.transaction_snapshot = {k: [dict(r) for r in v] for k, v in self.tables.items()}

    def commit(self):
        self.transaction_snapshot = None

    def rollback(self):
        if self.transaction_snapshot is not None:
            self.tables = self.transaction_snapshot
            self.transaction_snapshot = None

class LocalCursor:
    def __init__(self, store: LocalDBStore):
        self.store = store
        self.last_results = []
        self.rowcount = 0

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def execute(self, query: str, params: Union[Tuple, List, Dict] = None):
        q = query.strip()
        params = list(params) if params else []

        # Convert query for local simulation
        q_upper = q.upper()

        if q_upper.startswith("SELECT"):
            self._handle_select(q, params)
        elif q_upper.startswith("INSERT"):
            self._handle_insert(q, params)
        elif q_upper.startswith("UPDATE"):
            self._handle_update(q, params)
        elif q_upper.startswith("DELETE"):
            self._handle_delete(q, params)
        else:
            self.last_results = []
            self.rowcount = 0

    def _handle_select(self, q: str, params: List[Any]):
        q_upper = q.upper()

        # 0. Fast COUNT(*) handler
        if "COUNT(*)" in q_upper:
            tbl = ""
            for tname in self.store.tables.keys():
                if f"FROM {tname.upper()}" in q_upper:
                    tbl = tname
                    break
            res = self.store.tables.get(tbl, []) if tbl else []
            if "WHERE" in q_upper:
                if "DISCOVERED" in q_upper:
                    res = [r for r in res if r.get("status") == "discovered"]
                elif "ACTIVE" in q_upper:
                    res = [r for r in res if r.get("status") == "active"]
                elif "UNRESOLVED" in q_upper:
                    res = [r for r in res if r.get("recovery_status") == "unresolved"]
                elif "DELIVERABLE" in q_upper:
                    res = [r for r in res if r.get("verification_status") == "deliverable"]
                elif "VERIFICATION_STATUS IN" in q_upper:
                    res = [r for r in res if r.get("verification_status") in ("unknown", "verification_failed")]
            self.last_results = [{"count": len(res)}]
            self.rowcount = 1
            return

        # 1. Join for user roles: SELECT r.name FROM roles r JOIN user_roles ur ON ur.role_id = r.id WHERE ur.user_id = %s
        if "JOIN USER_ROLES" in q_upper:
            user_id = str(params[0]) if params else None
            matching_role_ids = [
                ur.get("role_id") for ur in self.store.tables.get("user_roles", [])
                if str(ur.get("user_id")) == user_id
            ]
            res = [
                {"name": r.get("name")} for r in self.store.tables.get("roles", [])
                if r.get("id") in matching_role_ids
            ]
            self.last_results = res
            self.rowcount = len(res)
            return

        # 2. Opportunities join with organizations and sources
        if "FROM OPPORTUNITIES" in q_upper:
            res = []
            for opp in self.store.tables.get("opportunities", []):
                item = dict(opp)
                org = next((o for o in self.store.tables.get("organizations", []) if o.get("id") == opp.get("organization_id")), None)
                src = next((s for s in self.store.tables.get("sources", []) if s.get("id") == opp.get("source_id")), None)
                item["organization_name"] = org.get("name") if org else None
                item["org_domain"] = org.get("domain") if org else None
                item["source_name"] = src.get("name") if src else None
                res.append(item)
            
            if "SOURCE_ID = %S AND SOURCE_IDENTIFIER = %S" in q_upper or "source_id = %s and source_identifier = %s" in q.lower():
                if len(params) >= 2:
                    res = [r for r in res if str(r.get("source_id")) == str(params[0]) and str(r.get("source_identifier")) == str(params[1])]
            elif "ORGANIZATION_ID = %S" in q_upper and "TITLE" in q_upper:
                if len(params) >= 2:
                    res = [r for r in res if str(r.get("organization_id")) == str(params[0]) and str(r.get("title", "")).strip().lower() == str(params[1]).strip().lower()]
            elif "O.ID = %S" in q_upper or "WHERE O.ID = %s" in q.lower() or "WHERE ID = %s" in q.lower() or "WHERE ID = %S" in q_upper:
                if params:
                    res = [r for r in res if str(r.get("id")) == str(params[0])]
            self.last_results = res
            self.rowcount = len(res)
            return

        # 3. Approvals
        if "FROM APPROVALS" in q_upper:
            res = self.store.tables.get("approvals", [])
            if params and "CAMPAIGN_DRAFT_ID" in q_upper:
                val = str(params[0])
                res = [r for r in res if str(r.get("campaign_draft_id")) == val]
            elif params and ("WHERE ID =" in q_upper or "WHERE A.ID =" in q_upper):
                val = str(params[0])
                res = [r for r in res if str(r.get("id")) == val]
            self.last_results = res
            self.rowcount = len(res)
            return

        # 4. Message events
        if "FROM MESSAGE_EVENTS" in q_upper:
            res = self.store.tables.get("message_events", [])
            if params and "PROVIDER_EVENT_ID" in q_upper:
                val = str(params[0]).strip()
                res = [r for r in res if str(r.get("provider_event_id")) == val]
            self.last_results = res
            self.rowcount = len(res)
            return

        # 4. Outreach messages
        if "FROM OUTREACH_MESSAGES" in q_upper:
            res = self.store.tables.get("outreach_messages", [])
            if params and "IDEMPOTENCY_KEY" in q_upper:
                val = str(params[0]).strip()
                res = [r for r in res if str(r.get("idempotency_key")) == val]
            elif params and "PROVIDER_MESSAGE_ID" in q_upper:
                val = str(params[0]).strip()
                res = [r for r in res if str(r.get("provider_message_id")) == val]
            elif params and "RECIPIENT_EMAIL" in q_upper:
                val = str(params[0]).strip().lower()
                res = [r for r in res if str(r.get("recipient_email", "")).lower() == val]
            self.last_results = res
            self.rowcount = len(res)
            return

        # 3. Opportunity contacts join
        if "FROM OPPORTUNITY_CONTACTS" in q_upper:
            res = []
            target_opp_id = str(params[0]) if params else None
            for oc in self.store.tables.get("opportunity_contacts", []):
                if target_opp_id and str(oc.get("opportunity_id")) != target_opp_id:
                    continue
                c = next((cnt for cnt in self.store.tables.get("contacts", []) if cnt.get("id") == oc.get("contact_id")), None)
                if c:
                    item = dict(c)
                    item["role_in_opportunity"] = oc.get("role_in_opportunity")
                    item["association_confidence"] = oc.get("association_confidence")
                    cm = next((m for m in self.store.tables.get("contact_methods", []) if m.get("contact_id") == c.get("id") and m.get("is_primary")), None)
                    if cm:
                        item["email"] = cm.get("value")
                        item["email_verification_status"] = cm.get("verification_status")
                    res.append(item)
            self.last_results = res
            self.rowcount = len(res)
            return

        # 4. Campaign drafts join
        if "FROM CAMPAIGN_DRAFTS" in q_upper:
            res = []
            for cd in self.store.tables.get("campaign_drafts", []):
                item = dict(cd)
                c = next((cnt for cnt in self.store.tables.get("contacts", []) if cnt.get("id") == cd.get("contact_id")), None)
                opp = next((o for o in self.store.tables.get("opportunities", []) if o.get("id") == cd.get("opportunity_id")), None)
                if c:
                    item["recipient_name"] = c.get("full_name")
                    cm = next((m for m in self.store.tables.get("contact_methods", []) if m.get("contact_id") == c.get("id") and m.get("is_primary")), None)
                    if cm:
                        item["recipient_email"] = cm.get("value")
                if opp:
                    item["job_title"] = opp.get("title")
                    org = next((o for o in self.store.tables.get("organizations", []) if o.get("id") == opp.get("organization_id")), None)
                    if org:
                        item["company_name"] = org.get("name")
                res.append(item)
            if "WHERE CD.ID = %S" in q_upper or "WHERE CD.ID = %s" in q.lower():
                if params:
                    res = [r for r in res if str(r.get("id")) == str(params[0])]
            elif "WHERE CD.CAMPAIGN_ID = %S" in q_upper or "WHERE CD.CAMPAIGN_ID = %s" in q.lower():
                if params:
                    res = [r for r in res if str(r.get("campaign_id")) == str(params[0])]
            self.last_results = res
            self.rowcount = len(res)
            return

        # 5. Contacts join
        if "FROM CONTACTS" in q_upper:
            res = []
            for c in self.store.tables.get("contacts", []):
                item = dict(c)
                org = next((o for o in self.store.tables.get("organizations", []) if o.get("id") == c.get("organization_id")), None)
                cm = next((m for m in self.store.tables.get("contact_methods", []) if m.get("contact_id") == c.get("id") and m.get("is_primary")), None)
                if org:
                    item["organization_name"] = org.get("name")
                if cm:
                    item["email"] = cm.get("value")
                    item["email_status"] = cm.get("verification_status")
                res.append(item)
            if "WHERE C.ID = %S" in q_upper or "WHERE C.ID = %s" in q.lower() or "WHERE ID = %S" in q_upper or "WHERE ID = %s" in q.lower():
                if params:
                    res = [r for r in res if str(r.get("id")) == str(params[0])]
            self.last_results = res
            self.rowcount = len(res)
            return

        # 6. Suppression entries
        if "FROM SUPPRESSION_ENTRIES" in q_upper:
            res = self.store.tables.get("suppression_entries", [])
            if params and "VALUE" in q_upper:
                val = str(params[0]).strip().lower()
                res = [r for r in res if str(r.get("value", "")).strip().lower() == val]
            self.last_results = res
            self.rowcount = len(res)
            return

        words = q.split()
        from_idx = -1
        for i, w in enumerate(words):
            if w.upper() == "FROM":
                from_idx = i
                break
        
        if from_idx != -1 and from_idx + 1 < len(words):
            table_name = words[from_idx + 1].strip(",;()\"'").lower()
            table = self.store.tables.get(table_name, [])
            res = [dict(r) for r in table]

            # COUNT(*)
            if "COUNT(*)" in q_upper:
                if "WHERE" in q_upper:
                    if "DELIVERABLE" in q_upper:
                        res = [r for r in res if r.get("verification_status") == "deliverable"]
                    elif "DISCOVERED" in q_upper:
                        res = [r for r in res if r.get("status") == "discovered"]
                    elif "ACTIVE" in q_upper:
                        res = [r for r in res if r.get("status") == "active"]
                    elif "UNRESOLVED" in q_upper:
                        res = [r for r in res if r.get("recovery_status") == "unresolved"]
                self.last_results = [{"count": len(res)}]
                self.rowcount = 1
                return

            if "WHERE" in q_upper:
                filtered = []
                for row in res:
                    match = True
                    for idx, param in enumerate(params):
                        param_str = str(param).lower() if isinstance(param, str) else str(param)
                        if "ID = %S" in q_upper or "ID = %s" in q.lower():
                            if str(row.get("id")) != str(param):
                                match = False
                                break
                        elif "EMAIL" in q_upper:
                            if str(row.get("email", "")).lower() != param_str:
                                match = False
                                break
                    if match:
                        filtered.append(row)
                res = filtered

            self.last_results = res
            self.rowcount = len(res)
        else:
            self.last_results = []
            self.rowcount = 0

    def _handle_insert(self, q: str, params: List[Any]):
        words = q.split()
        into_idx = -1
        for i, w in enumerate(words):
            if w.upper() == "INTO":
                into_idx = i
                break
        if into_idx != -1 and into_idx + 1 < len(words):
            table_name = words[into_idx + 1].split("(")[0].strip(",;\"'").lower()
            cols_start = q.find("(")
            cols_end = q.find(")", cols_start)
            cols_str = q[cols_start + 1:cols_end]
            columns = [c.strip().strip('"\'') for c in cols_str.split(",")]
            
            new_row = {
                "id": str(uuid.uuid4()),
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "is_active": True
            }
            # Assign values
            p_idx = 0
            for col in columns:
                if p_idx < len(params):
                    new_row[col] = params[p_idx]
                    p_idx += 1
            
            if table_name in self.store.tables:
                self.store.tables[table_name].append(new_row)
                self.last_results = [new_row]
                self.rowcount = 1
            else:
                self.last_results = []
                self.rowcount = 0

    def _handle_update(self, q: str, params: List[Any]):
        words = q.split()
        if len(words) > 1:
            tbl_name = words[1].lower()
            if tbl_name in self.store.tables and params:
                target_id = str(params[-1])
                for r in self.store.tables[tbl_name]:
                    if str(r.get("id")) == target_id:
                        if "STATUS =" in q.upper():
                            r["status"] = params[0]
                        if "SUBJECT_LINE =" in q.upper() and len(params) >= 2:
                            r["subject_line"] = params[0]
                            r["email_body"] = params[1]
                        if "SEND_STATUS =" in q.upper():
                            r["send_status"] = params[0]
                        if "SENT_COUNT = SENT_COUNT + 1" in q.upper():
                            r["sent_count"] = r.get("sent_count", 0) + 1
        self.rowcount = 1
        self.last_results = []

    def _handle_delete(self, q: str, params: List[Any]):
        self.rowcount = 1
        self.last_results = []

    def fetchone(self) -> Optional[Dict[str, Any]]:
        return self.last_results[0] if self.last_results else None

    def fetchall(self) -> List[Dict[str, Any]]:
        return self.last_results

class LocalConnection:
    def __init__(self, store: LocalDBStore):
        self.store = store

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.rollback()
        else:
            self.commit()

    def cursor(self):
        return LocalCursor(self.store)

    def commit(self):
        self.store.commit()

    def rollback(self):
        self.store.rollback()

    def close(self):
        pass

def init_db():
    global _pool, _local_db
    if settings.DATABASE_URL and "neon.tech" in settings.DATABASE_URL:
        try:
            import psycopg_pool
            logger.info("Initializing Neon PostgreSQL ConnectionPool...")
            _pool = psycopg_pool.ConnectionPool(
                conninfo=settings.DATABASE_URL,
                min_size=settings.DB_POOL_MIN_SIZE,
                max_size=settings.DB_POOL_MAX_SIZE,
                timeout=settings.DB_TIMEOUT_SECONDS,
                kwargs={"autocommit": False}
            )
            logger.info("Neon PostgreSQL ConnectionPool initialized successfully.")
            return
        except Exception as e:
            logger.warning(f"Could not connect to remote Neon PostgreSQL: {e}. Falling back to internal local store.")

    # Local fallback
    _local_db = LocalDBStore()
    logger.info("Local direct SQL store initialized.")

def close_db():
    global _pool
    if _pool:
        _pool.close()
        _pool = None

@contextmanager
def get_db_connection():
    global _pool, _local_db
    if _pool is not None:
        with _pool.connection() as conn:
            try:
                yield conn
            except Exception:
                conn.rollback()
                raise
            else:
                conn.commit()
    else:
        if _local_db is None:
            init_db()
        conn = LocalConnection(_local_db)
        _local_db.begin()
        try:
            yield conn
        except Exception:
            conn.rollback()
            raise
        else:
            conn.commit()

def execute_query(sql: str, params: Union[Tuple, List, Dict] = None) -> int:
    """Executes a direct parameterized SQL statement (INSERT, UPDATE, DELETE)."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.rowcount

def fetch_one(sql: str, params: Union[Tuple, List, Dict] = None) -> Optional[Dict[str, Any]]:
    """Executes a direct parameterized SQL query and returns a single dict row."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            row = cur.fetchone()
            if row is None:
                return None
            if isinstance(row, dict):
                return row
            # psycopg tuple row with description
            if hasattr(cur, "description") and cur.description:
                cols = [desc[0] for desc in cur.description]
                return dict(zip(cols, row))
            return row

def fetch_all(sql: str, params: Union[Tuple, List, Dict] = None) -> List[Dict[str, Any]]:
    """Executes a direct parameterized SQL query and returns a list of dict rows."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()
            if not rows:
                return []
            if isinstance(rows[0], dict):
                return rows
            if hasattr(cur, "description") and cur.description:
                cols = [desc[0] for desc in cur.description]
                return [dict(zip(cols, r)) for r in rows]
            return rows

def get_store() -> Optional[LocalDBStore]:
    """Helper to access local store directly for inspection or seed testing."""
    return _local_db
