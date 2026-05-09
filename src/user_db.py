from datetime import datetime, timezone

import certifi
import streamlit as st
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

_ca = certifi.where()


@st.cache_resource
def _get_auth_client() -> MongoClient:
    """Return a cached write-enabled MongoClient for user operations."""
    uri = (
        f"mongodb+srv://{st.secrets['whiskeydb_rw']}:{st.secrets['whiskeydb_pwd_rw']}"
        f"@{st.secrets['whiskeydb_url']}/?retryWrites=true&w=majority"
        f"&appName=WhiskeyRecommender"
    )
    client = MongoClient(
        uri,
        server_api=ServerApi("1"),
        tls=True,
        tlsAllowInvalidCertificates=False,
        tlsCAFile=_ca,
    )
    # Create indexes the first time the client is built
    users = client["whiskey_database"]["users"]
    users.create_index("email", unique=True)
    users.create_index("username", unique=True)
    return client


def _users_col():
    return _get_auth_client()["whiskey_database"]["users"]


def get_user_by_username(username: str) -> dict | None:
    return _users_col().find_one({"username": username})


def get_user_by_email(email: str) -> dict | None:
    return _users_col().find_one({"email": email})


def create_user(username: str, email: str, hashed_password: str) -> str:
    """Insert a new user document and return the inserted _id as a string."""
    doc = {
        "username": username,
        "email": email,
        "hashed_password": hashed_password,
        "created_at": datetime.now(timezone.utc),
        "search_history": [],
    }
    result = _users_col().insert_one(doc)
    return str(result.inserted_id)


@st.cache_resource(ttl=300)
def load_authenticator_credentials() -> dict:
    """Build a streamlit-authenticator credentials dict from all users in MongoDB.

    Result is cached for 5 minutes. Call load_authenticator_credentials.clear()
    after registration to pick up the new user immediately.
    """
    credentials: dict = {"usernames": {}}
    for user in _users_col().find(
        {}, {"username": 1, "email": 1, "hashed_password": 1}
    ):
        credentials["usernames"][user["username"]] = {
            "name": user["username"],
            "email": user["email"],
            "password": user["hashed_password"],
        }
    return credentials