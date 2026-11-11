# Register + verify the email, log in, forgot + reset the password
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.deps import DB, CurrentUser, MailerDep
from app.emails import (
    changed_email,
    reset_email,
    reset_lifetime,
    verify_email,
    verify_lifetime,
)
from app.links import issue_link, kill_links, use_link
from app.models import User
from app.schemas import (
    EmailIn,
    LinkIn,
    Message,
    PasswordChange,
    ResetIn,
    Token,
    UserCreate,
    UserOut,
)
from app.security import DUMMY_HASH, create_access_token, hash_password, verify_password

router = APIRouter(tags=["Auth"])

# the SAME answer for an email we know and one we don't - nobody learns who has an account
SENT = Message(detail="If the email belongs to an account, we sent a link")


@router.post("/users", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(data: UserCreate, db: DB, mailer: MailerDep, tasks: BackgroundTasks) -> User:
    user = User(email=data.email, full_name=data.full_name,
                password_hash=hash_password(data.password))
    db.add(user)
    try:
        await db.flush()                                # the INSERT - now user.id exists
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="Email already registered") from None
    token = await issue_link(db, user, "verify", verify_lifetime())
    await db.commit()
    tasks.add_task(mailer.send, verify_email(user.email, token))     # AFTER the answer
    await db.refresh(user)
    return user


@router.post("/verify-email", response_model=UserOut)
async def confirm_email(data: LinkIn, db: DB) -> User:
    user = await use_link(db, data.token, "verify")
    user.is_verified = True
    await db.commit()
    await db.refresh(user)
    return user


@router.post("/verify-email/resend", response_model=Message,
             status_code=status.HTTP_202_ACCEPTED)
async def resend_verification(data: EmailIn, db: DB, mailer: MailerDep,
                              tasks: BackgroundTasks) -> Message:
    user = await db.scalar(select(User).where(User.email == data.email.lower()))
    if user is not None and user.is_active and not user.is_verified:
        token = await issue_link(db, user, "verify", verify_lifetime())   # old link dies
        await db.commit()
        tasks.add_task(mailer.send, verify_email(user.email, token))
    return SENT


@router.post("/token", response_model=Token)
async def login(form: Annotated[OAuth2PasswordRequestForm, Depends()], db: DB) -> Token:
    user = await db.scalar(select(User).where(User.email == form.username.lower()))
    if user is None:
        verify_password(form.password, DUMMY_HASH)
    if user is None or not verify_password(form.password, user.password_hash) \
            or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Incorrect email or password",
                            headers={"WWW-Authenticate": "Bearer"})
    if not user.is_verified:                     # the password was right - so we may say it
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Please verify your email first")
    return Token(access_token=create_access_token(user.id))


@router.post("/password/forgot", response_model=Message, status_code=status.HTTP_202_ACCEPTED)
async def forgot_password(data: EmailIn, db: DB, mailer: MailerDep,
                          tasks: BackgroundTasks) -> Message:
    user = await db.scalar(select(User).where(User.email == data.email.lower()))
    if user is not None and user.is_active:
        token = await issue_link(db, user, "reset", reset_lifetime())
        await db.commit()
        tasks.add_task(mailer.send, reset_email(user.email, token))
    return SENT                                         # known or unknown: the same 202


@router.post("/password/reset", response_model=Message)
async def reset_password(data: ResetIn, db: DB, mailer: MailerDep,
                         tasks: BackgroundTasks) -> Message:
    user = await use_link(db, data.token, "reset")
    user.password_hash = hash_password(data.new_password)
    user.is_verified = True                             # the link proved the inbox, too
    await db.commit()
    tasks.add_task(mailer.send, changed_email(user.email))      # homework 44
    return Message(detail="Password changed - log in with the new password")


@router.post("/me/password", response_model=Message)
async def change_password(data: PasswordChange, user: CurrentUser, db: DB, mailer: MailerDep,
                          tasks: BackgroundTasks) -> Message:
    # homework 44: logged in - but the OLD password must be right (a borrowed laptop?)
    if not verify_password(data.old_password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Old password is wrong")
    user.password_hash = hash_password(data.new_password)
    await kill_links(db, user.id, "reset")              # an old reset link can't undo it
    await db.commit()
    tasks.add_task(mailer.send, changed_email(user.email))
    return Message(detail="Password changed")


@router.get("/me", response_model=UserOut)
async def read_me(user: CurrentUser) -> User:
    return user
