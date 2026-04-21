import streamlit_authenticator as stauth


def hash_password(plain: str) -> str:
    """Hash a plaintext password using streamlit-authenticator's native bcrypt hasher."""
    return stauth.Hasher._hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plaintext password against a stored hash."""
    return stauth.Hasher.check_pw(plain, hashed)
