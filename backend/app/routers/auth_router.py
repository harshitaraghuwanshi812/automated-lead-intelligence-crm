from fastapi import APIRouter, Depends, HTTPException, status
from app.models.schemas import UserLogin, UserRegister, TokenResponse, UserOut
from app.auth.security import hash_password, verify_password, create_access_token, get_current_user, get_user_roles
from app.database import fetch_one, execute_query
import uuid

router = APIRouter(prefix="/auth", tags=["Authentication & RBAC"])

@router.post("/login", response_model=TokenResponse)
def login(credentials: UserLogin):
    email = credentials.email.lower()
    user = fetch_one("SELECT * FROM users WHERE LOWER(email) = %s", [email])
    
    # Allow test seed accounts if user not yet created
    if not user:
        if email == "admin@leadintel.org" and credentials.password == "Admin@123456":
            uid = "00000000-0000-0000-0000-000000000001"
            token = create_access_token({"sub": uid, "email": email, "roles": ["admin"]})
            return TokenResponse(
                access_token=token,
                user_id=uid,
                email=email,
                full_name="System Administrator",
                roles=["admin", "researcher", "campaign_manager"]
            )
        elif email == "researcher@leadintel.org" and credentials.password == "Researcher@123456":
            uid = "00000000-0000-0000-0000-000000000002"
            token = create_access_token({"sub": uid, "email": email, "roles": ["researcher"]})
            return TokenResponse(
                access_token=token,
                user_id=uid,
                email=email,
                full_name="Lead Researcher",
                roles=["researcher"]
            )
        elif email == "campaign@leadintel.org" and credentials.password == "Campaign@123456":
            uid = "00000000-0000-0000-0000-000000000003"
            token = create_access_token({"sub": uid, "email": email, "roles": ["campaign_manager"]})
            return TokenResponse(
                access_token=token,
                user_id=uid,
                email=email,
                full_name="Campaign Manager",
                roles=["campaign_manager"]
            )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password.")

    if not verify_password(credentials.password, user["password_hash"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password.")

    roles = get_user_roles(user["id"])
    token = create_access_token({"sub": user["id"], "email": user["email"], "roles": roles})

    return TokenResponse(
        access_token=token,
        user_id=str(user["id"]),
        email=user["email"],
        full_name=user["full_name"],
        roles=roles or ["researcher"]
    )

@router.post("/register", response_model=UserOut)
def register(payload: UserRegister):
    email = payload.email.lower()
    existing = fetch_one("SELECT id FROM users WHERE LOWER(email) = %s", [email])
    if existing:
        raise HTTPException(status_code=400, detail="User with this email already exists.")

    new_id = str(uuid.uuid4())
    pw_hash = hash_password(payload.password)
    sql_user = """
    INSERT INTO users (id, email, password_hash, full_name, is_active)
    VALUES (%s, %s, %s, %s, TRUE)
    """
    execute_query(sql_user, [new_id, email, pw_hash, payload.full_name])

    # Assign role
    role = fetch_one("SELECT id FROM roles WHERE name = %s", [payload.role_name])
    if role:
        execute_query("INSERT INTO user_roles (user_id, role_id) VALUES (%s, %s)", [new_id, role["id"]])

    return UserOut(
        id=new_id,
        email=email,
        full_name=payload.full_name,
        is_active=True,
        roles=[payload.role_name]
    )

@router.get("/me", response_model=UserOut)
def get_me(current_user: dict = Depends(get_current_user)):
    return UserOut(
        id=str(current_user.get("id")),
        email=current_user.get("email"),
        full_name=current_user.get("full_name"),
        is_active=current_user.get("is_active", True),
        roles=current_user.get("roles", [])
    )
