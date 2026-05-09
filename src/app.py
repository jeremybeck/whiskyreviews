import streamlit as st
import re
from collections import defaultdict
import numpy as np
from streamlit import pills
from vector_db import *
from language_models import *
import streamlit_authenticator as stauth
from auth_utils import hash_password
from user_db import (
    get_user_by_username,
    get_user_by_email,
    create_user,
    load_authenticator_credentials,
)

from sessions import display_drinking_session

# Initialize the vector store
st.set_page_config(page_title="Whisk(e)y Explorer", page_icon="🥃")


# ---------------------------------------------------------------------------
# Authentication (INT-5, INT-6, INT-7, INT-8)
# ---------------------------------------------------------------------------

def _build_authenticator():
    """Build a streamlit-authenticator Authenticate object from cached MongoDB credentials."""
    try:
        credentials = load_authenticator_credentials()
    except Exception:
        credentials = {"usernames": {}}
    return stauth.Authenticate(
        credentials,
        st.secrets.get("cookie_name", "whiskey_auth"),
        st.secrets.get("cookie_key", "whiskey_change_me_in_production"),
        cookie_expiry_days=30,
    )


def _render_registration_form():
    st.subheader("Create an account")
    with st.form("registration_form", clear_on_submit=True):
        reg_username = st.text_input("Username")
        reg_email = st.text_input("Email")
        reg_password = st.text_input("Password", type="password")
        reg_password2 = st.text_input("Confirm password", type="password")
        reg_signup_code = st.text_input("Signup Code")
        submitted = st.form_submit_button("Register")

    if submitted:
        expected_code = str(st.secrets.get("signup_code", ""))
        if reg_signup_code != expected_code:
            st.error("Invalid signup code.")
        elif len(reg_username) < 3:
            st.error("Username must be at least 3 characters.")
        elif not reg_email or "@" not in reg_email:
            st.error("Please enter a valid email address.")
        elif reg_password != reg_password2:
            st.error("Passwords do not match.")
        elif get_user_by_username(reg_username):
            st.error("That username is already taken.")
        elif get_user_by_email(reg_email):
            st.error("An account with that email already exists.")
        else:
            create_user(reg_username, reg_email, hash_password(reg_password))
            # Bust credential cache so the new user can log in immediately
            load_authenticator_credentials.clear()
            st.success("Account created! Please switch to the Login tab.")


# Build authenticator once at the top so the cookie is read before the auth check.
authenticator = _build_authenticator()

# Gate the app on authentication status (INT-8)
if not st.session_state.get("authentication_status"):
    st.title("🥃 Whiskey Recommender")
    tab_login, tab_register = st.tabs(["🔐 Login", "📝 Register"])

    with tab_login:
        authenticator.login(location="main")
        if st.session_state.get("authentication_status"):
            st.rerun()
        elif st.session_state.get("authentication_status") is False:
            st.error("Username or password is incorrect.")
        else:
            st.info("Enter your credentials to continue.")

    with tab_register:
        _render_registration_form()

    st.stop()

# ---------------------------------------------------------------------------
# Authenticated app
# ---------------------------------------------------------------------------

# Persist user_id in session state (INT-8)
if "user_id" not in st.session_state:
    _user_doc = get_user_by_username(st.session_state.get("username", ""))
    if _user_doc:
        st.session_state["user_id"] = str(_user_doc["_id"])

# Streamlit App Title
st.title("🥃 Whiskey Recommender")

# Sidebar: user info + logout (INT-8)
st.sidebar.header(f"👤 {st.session_state.get('name', st.session_state.get('username', 'User'))}")
authenticator.logout(location="sidebar")

# Sidebar Wishlist
st.sidebar.header("📌 Wishlist")
if "wishlist" not in st.session_state:
    st.session_state.wishlist = []

for whiskey in st.session_state.wishlist:
    st.sidebar.write(f"- {whiskey}")

# Fetch distinct regions, types, and countries from the vector database
distinct_regions = ["Highlands", "Lowlands", "Speyside", "Islay", "Campbeltown", "Kentucky", "Tennessee", "Ireland",
                    "Japan"]
distinct_types = ["Rye", "Bourbon", "Scotch", "Irish", "Japanese"]
distinct_countries = vectordb.distinct('whiskey_country_of_origin')  # Ensure this works with your vector database

# Sidebar Filters
num_whiskies = st.sidebar.slider("Number of Whiskeys", min_value=5, max_value=20, value=10, step=1)
selected_region = st.sidebar.selectbox("🌍 Filter by Region", ["All"] + distinct_regions)
selected_type = st.sidebar.selectbox("🥃 Filter by Whiskey Type", ["All"] + distinct_types)
selected_country = st.sidebar.selectbox("🥃 Filter by Country", ["All"] + distinct_countries)

# Add advanced search flag to the sidebar
advanced_search = st.sidebar.checkbox("🔍 Enable Advanced Search - Alpha")
results = None

def display_whiskey(whiskey_doc, advanced_search=False, query=None,
                    nose_query="", palette_query="", finish_query=""):

    # Metadata accessor
    get = whiskey_doc.get if advanced_search else whiskey_doc.metadata.get

    # Metadata fields
    distillery = get("distillery", "Unknown Distillery")
    whiskey_name = get("whiskey_name", "Unknown Whiskey")
    age = get("age", "No Age Statement")
    region = get("distillery_region", "Unknown Region")
    nose_tags = get("nose_tags", [])
    palette_tags = get("palette_tags", [])
    finish_tags = get("finish_tags", [])

    # Display metadata
    st.markdown(f"### {whiskey_name}")
    st.markdown(f"**{distillery}**")
    st.markdown(f"🕰️ Age: {age}")
    st.markdown(f"📍 Region: {region}")

    # Extract input keywords
    def extract_words(text):
        return set(re.findall(r'\b\w+\b', text.lower()))

    if advanced_search:
        nose_words = extract_words(nose_query)
        palette_words = extract_words(palette_query)
        finish_words = extract_words(finish_query)
    else:
        shared_words = extract_words(query or "")
        nose_words = palette_words = finish_words = shared_words

    # Matching logic
    def is_tag_match(tag, matched_words):
        tag_words = set(re.findall(r'\b\w+\b', tag.lower()))
        return not tag_words.isdisjoint(matched_words)

    # Tag rendering
    def render_tags(label, tags, matched_words):
        label_html = f"<strong>{label}</strong><br>"
        pill_html = ""
        for tag in tags:
            match = is_tag_match(tag, matched_words)
            bg_color = "#FFD700" if match else "#e0e0e0"
            text_color = "#000000" if match else "#555555"
            pill_html += (
                f"<span style='display:inline-block; background-color:{bg_color}; color:{text_color}; "
                f"padding:4px 10px; margin:2px 6px 6px 0; border-radius:15px; font-size:0.85rem;'>"
                f"{tag}</span>"
            )
        st.markdown(label_html + pill_html, unsafe_allow_html=True)

    # Render each tag section
    render_tags("👃 Nose Notes", nose_tags, nose_words)
    render_tags("👅 Palette Notes", palette_tags, palette_words)
    render_tags("🥃 Finish Notes", finish_tags, finish_words)


def construct_pre_filter(selected_region=None, selected_type=None, selected_country=None):
    pre_filter = {}

    if selected_region:
        if selected_region == 'All':
            pass
        else:
            pre_filter["distillery_region"] = {"$eq": selected_region}
    if selected_type:
        if selected_type == 'All':
            pass
        else:
            pre_filter["whiskey_type"] = {"$eq": selected_type}
    if selected_country:
        if selected_country == 'All':
            pass
        else:
            pre_filter["whiskey_country_of_origin"] = {"$eq": selected_country}

    return pre_filter if pre_filter else None  # Return None if no filters are applied


def query_multiple(nose_tags=None, palette_tags=None, finish_tags=None, filters=None, top_k=5):

    if filters is not None:
        filter_criteria = filters
    else:
        filter_criteria = {}

    if nose_tags:
        nose_embedding = Binary.from_vector(embedding_model.embed_query(nose_tags), BinaryVectorDtype.FLOAT32)
        nose_results = list(multiembed.aggregate([
            {"$vectorSearch": {
                "index": "test_index",
                "path": "nose_embedding",
                "queryVector": nose_embedding,
                "numCandidates": 10000,
                "limit": 5000,
                "filter": filter_criteria
            }},
            {
                "$project": {
                    "_id": 1,
                    "score": {"$meta": "vectorSearchScore"}
                }
            }
        ]))

    if palette_tags:
        palette_embedding = Binary.from_vector(embedding_model.embed_query(palette_tags), BinaryVectorDtype.FLOAT32)
        palette_results = list(multiembed.aggregate([
            {"$vectorSearch": {
                "index": "test_index",
                "path": "palette_embedding",
                "queryVector": palette_embedding,
                "numCandidates": 10000,
                "limit": 5000,
                "filter": filter_criteria
            }},
            {
                "$project": {
                    "_id": 1,
                    "score": {"$meta": "vectorSearchScore"}
                }
            }
        ]))

    if finish_tags:
        finish_embedding = Binary.from_vector(embedding_model.embed_query(finish_tags), BinaryVectorDtype.FLOAT32)
        finish_results = list(multiembed.aggregate([
            {"$vectorSearch": {
                "index": "test_index",
                "path": "finish_embedding",
                "queryVector": finish_embedding,
                "numCandidates": 10000,
                "limit": 5000,
                "filter": filter_criteria
            }},
            {
                "$project": {
                    "_id": 1,
                    "score": {"$meta": "vectorSearchScore"}
                }
            }
        ]))

    # Combine and rerank
    scores = defaultdict(lambda: [])  # Store a list of scores for each whiskey

    # Assign scores (higher rank = lower index)
    if 'finish_results' in locals():
        for result in finish_results:
            scores[result["_id"]].append(result["score"])

    if 'palette_results' in locals():
        for result in palette_results:
            scores[result["_id"]].append(result["score"])

    if 'nose_results' in locals():
        for result in nose_results:
            scores[result["_id"]].append(result["score"])

    # Compute final score as the average of available scores
    final_scores = {k: np.sum(v)/3 for k, v in scores.items()}  # Only average non-empty scores

    # Sort by best score
    sorted_results = sorted(final_scores.items(), key=lambda x: x[1], reverse=True)

    # Fetch final top results
    final_whiskeys = [(multiembed.find_one({"_id": whiskey_id}), score) for whiskey_id, score in sorted_results[:top_k]]

    return final_whiskeys

with st.expander('Search', expanded=True):
    if advanced_search:
        # Show form for advanced search filters
        with st.form("Advanced Tasting Notes"):
            st.write("🔍 **Advanced Search Filters**")
            #if 'nose_likes' not in st.session_state:
            #    st.session_state.nose_likes = []
            #if 'palette_likes' not in st.session_state:
            #    st.session_state.palette_likes = []
            #if 'finish_likes' not in st.session_state:
            #    st.session_state.finish_likes = []


            nose_notes = st.text_input("👃 Enter Nose Notes (comma-separated)", ','.join(st.session_state.get('nose_likes',[])))
            palette_notes = st.text_input("👅 Enter Palette Notes (comma-separated)", ','.join(st.session_state.get('palette_likes',[])))
            finish_notes = st.text_input("🥃 Enter Finish Notes (comma-separated)", ','.join(st.session_state.get('finish_likes',[])))

            # Submit button for the advanced form
            submitted = st.form_submit_button("Submit Advanced Search")

        if submitted:
            # Split the notes input into lists of tags
            nose_tags = nose_notes if nose_notes else None
            palette_tags = palette_notes if palette_notes else None
            finish_tags = finish_notes if finish_notes else None

            filter_conditions = construct_pre_filter(selected_region=selected_region, selected_type=selected_type,
                                                     selected_country=selected_country)

            results = query_multiple(nose_tags=nose_tags, palette_tags=palette_tags, finish_tags=finish_tags, filters=filter_conditions, top_k=num_whiskies)
    else:
        # User Query Input
        query = st.text_input("🔍 Describe what you're looking for in a whiskey:",
                              help="Want to get more specific about nose, palette, and finish? Enable Advanced Search in the sidebar.")
        if query:
            filter_conditions = construct_pre_filter(selected_region=selected_region, selected_type=selected_type,
                                                     selected_country=selected_country)
            # Search vector database
            results = vector_store.similarity_search_with_score(query, k=num_whiskies, pre_filter=filter_conditions)


    if results:
        st.subheader("🍂 Recommended Whiskeys")
        max_columns = 2
        num_rows = (num_whiskies + max_columns - 1) // max_columns  # This rounds up the division to ensure full rows
        # Create containers for each row
        for row in range(num_rows):
            cols = st.columns(max_columns)  # Create a row with up to 3 columns
            for col in range(min(max_columns, num_whiskies - row * max_columns)):  # Ensure we don't exceed k items
                with cols[col]:
                    item_index = row * max_columns + col  # Calculate the item index
                    if item_index < num_whiskies:
                        with st.container(border=True):
                            try:
                                if advanced_search:
                                    display_whiskey(results[item_index][0], advanced_search=advanced_search,
                                                    nose_query=nose_notes, palette_query=palette_notes,
                                                    finish_query=finish_notes)
                                else:
                                    display_whiskey(results[item_index][0], advanced_search=advanced_search, query=query)
                                if st.button(f"📌 Add {whiskey_name} to Wishlist", key=f"{whiskey_name}_{whiskey_id}"):
                                    if f"{whiskey_name}_{whiskey_id}" not in st.session_state.wishlist:
                                        st.session_state.wishlist.append(f"{whiskey_name}_{whiskey_id}")
                            except:
                                pass  # Replace this with your actual content


    else:
        st.write("👆 Enter a description to find similar whiskeys.")


with st.expander('Review', expanded=False):
    display_drinking_session()
