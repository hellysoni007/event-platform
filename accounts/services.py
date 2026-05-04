import hashlib
import hmac
import secrets
import string
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone
from rest_framework import status

from accounts.models import OTPChallenge, UserProfile, UserRole
from core.error_codes import ErrorCodes
from core.exceptions import DomainError

OTP_LENGTH = 6
RESEND_COOLDOWN_SECONDS = 60
MAX_RESENDS_PER_HOUR = 5
MAX_VERIFY_ATTEMPTS = 10


def normalize_email(email: str) -> str:
    return email.strip().lower()


def generate_username() -> str:
    chars = string.ascii_lowercase + string.digits
    for _ in range(3):
        candidate = "usr_" + "".join(secrets.choice(chars) for _ in range(12))
        if not User.objects.filter(username=candidate).exists():
            return candidate
    raise DomainError(
        detail="Could not generate username.",
        code=ErrorCodes.INTERNAL_ERROR,
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


def generate_otp() -> str:
    return "".join(secrets.choice(string.digits) for _ in range(OTP_LENGTH))


def hash_otp(otp: str) -> str:
    return hmac.new(settings.SECRET_KEY.encode(), otp.encode(), hashlib.sha256).hexdigest()


def verify_otp_hash(candidate: str, otp_hash: str) -> bool:
    candidate_hash = hash_otp(candidate)
    return hmac.compare_digest(candidate_hash, otp_hash)


def create_or_resend_signup_otp(email: str, password: str, role: str):
    email = normalize_email(email)
    if role not in UserRole.values:
        raise DomainError(detail="Invalid role.", code=ErrorCodes.VALIDATION_ERROR)

    user = User.objects.filter(email__iexact=email).first()
    was_existing = user is not None
    if user and user.is_active:
        raise DomainError(
            detail="Email already exists.",
            code=ErrorCodes.EMAIL_ALREADY_EXISTS,
            status_code=status.HTTP_409_CONFLICT,
        )

    with transaction.atomic():
        if not user:
            user = User.objects.create_user(
                username=generate_username(),
                email=email,
                password=password,
                is_active=False,
            )
            UserProfile.objects.create(user=user, role=role)
        else:
            if password:
                user.set_password(password)
                user.save(update_fields=["password"])
            if hasattr(user, "profile"):
                user.profile.role = role
                user.profile.save(update_fields=["role"])
            else:
                UserProfile.objects.create(user=user, role=role)

        return issue_new_otp(user, is_resend=was_existing)


def issue_new_otp(user: User, is_resend: bool):
    now = timezone.now()
    latest = OTPChallenge.objects.filter(user=user, is_active=True).order_by("-created_at").first()

    if is_resend and latest:
        delta = (now - latest.created_at).total_seconds()
        if delta < RESEND_COOLDOWN_SECONDS:
            raise DomainError(
                detail="OTP resend cooldown in effect.",
                code=ErrorCodes.OTP_RESEND_COOLDOWN,
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            )
        hourly_count = OTPChallenge.objects.filter(user=user, created_at__gte=now - timedelta(hours=1)).count()
        if hourly_count >= MAX_RESENDS_PER_HOUR:
            raise DomainError(
                detail="OTP resend limit exceeded.",
                code=ErrorCodes.OTP_RESEND_LIMIT_EXCEEDED,
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            )

    OTPChallenge.objects.filter(user=user, is_active=True).update(is_active=False)
    otp = generate_otp()
    challenge = OTPChallenge.objects.create(
        user=user,
        otp_hash=hash_otp(otp),
        expires_at=OTPChallenge.default_expiry(),
        resend_count=(latest.resend_count + 1) if latest else 0,
    )
    send_mail(
        subject="Your verification OTP",
        message=f"Your OTP is {otp}. It expires in 5 minutes.",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
    )
    return challenge


def verify_email_otp(email: str, otp: str):
    email = normalize_email(email)
    user = User.objects.filter(email__iexact=email).first()
    if not user:
        raise DomainError(detail="Invalid OTP.", code=ErrorCodes.INVALID_OTP)

    challenge = OTPChallenge.objects.filter(user=user, is_active=True).order_by("-created_at").first()
    if not challenge:
        raise DomainError(detail="Invalid OTP.", code=ErrorCodes.INVALID_OTP)
    if challenge.is_expired():
        raise DomainError(detail="OTP expired.", code=ErrorCodes.OTP_EXPIRED)

    if challenge.attempts >= MAX_VERIFY_ATTEMPTS:
        raise DomainError(
            detail="OTP attempts exceeded.",
            code=ErrorCodes.OTP_ATTEMPTS_EXCEEDED,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        )

    if not verify_otp_hash(otp, challenge.otp_hash):
        challenge.attempts += 1
        challenge.save(update_fields=["attempts", "updated_at"])
        raise DomainError(detail="Invalid OTP.", code=ErrorCodes.INVALID_OTP)

    user.is_active = True
    user.save(update_fields=["is_active"])
    if hasattr(user, "profile"):
        user.profile.email_verified_at = timezone.now()
        user.profile.save(update_fields=["email_verified_at"])
    challenge.is_active = False
    challenge.save(update_fields=["is_active", "updated_at"])
    return user


def login_user(email: str, password: str):
    email = normalize_email(email)
    user = User.objects.filter(email__iexact=email).first()
    if not user:
        raise DomainError(
            detail="Invalid credentials.",
            code=ErrorCodes.INVALID_CREDENTIALS,
            status_code=status.HTTP_401_UNAUTHORIZED,
        )
    if not user.is_active:
        raise DomainError(
            detail="Email is not verified.",
            code=ErrorCodes.EMAIL_NOT_VERIFIED,
            status_code=status.HTTP_403_FORBIDDEN,
        )

    auth_user = authenticate(username=user.username, password=password)
    if not auth_user:
        raise DomainError(
            detail="Invalid credentials.",
            code=ErrorCodes.INVALID_CREDENTIALS,
            status_code=status.HTTP_401_UNAUTHORIZED,
        )
    return auth_user
