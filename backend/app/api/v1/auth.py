from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.core.security import create_access_token, hash_password, verify_password
from app.db.session import get_db
from app.models import User
from app.schemas import ChangePasswordRequest, LoginRequest, Message, TokenResponse, UserOut

router = APIRouter(prefix="/auth", tags=["认证"])


def _login(db: Session, username: str, password: str) -> TokenResponse:
    user = db.scalar(select(User).where(User.username == username))
    if user is None or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    if user.status != "active":
        raise HTTPException(status_code=403, detail="账号已被禁用")

    user.last_login_at = datetime.now()
    db.commit()
    db.refresh(user)
    token, expires_in = create_access_token(user.id, user.role)
    return TokenResponse(
        access_token=token,
        expires_in=expires_in,
        user=UserOut.model_validate(user),
    )


@router.post("/login", response_model=TokenResponse, summary="用户名密码登录")
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    return _login(db, payload.username, payload.password)


@router.post("/token", response_model=TokenResponse, summary="Swagger OAuth2 登录")
def token(
    form: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> TokenResponse:
    return _login(db, form.username, form.password)


@router.get("/me", response_model=UserOut, summary="当前登录用户")
def me(user: User = Depends(get_current_user)) -> UserOut:
    return UserOut.model_validate(user)


@router.post("/change-password", response_model=Message, summary="修改自己的密码")
def change_password(
    payload: ChangePasswordRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Message:
    if not verify_password(payload.old_password, user.password_hash):
        raise HTTPException(status_code=400, detail="原密码错误")
    user.password_hash = hash_password(payload.new_password)
    db.commit()
    return Message(message="密码修改成功")
