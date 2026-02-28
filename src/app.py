import streamlit as st
from collections import defaultdict
import numpy as np
from streamlit_pills import pills
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


# Initialize the vector store
st.set_page_config(page_title="Whisk(e)y Explorer", page_icon="🥃")


# ---------------------------------------------------------------------------
# Authentication (INT-5, INT-6, INT-7, INT-8)
# ---------------------------------------------------------------------------

@st.cache_resource
def _build_authenticator():
    """Build the streamlit-authenticator Authenticate object from MongoDB users."""
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
        submitted = st.form_submit_button("Register")

    if submitted:
        if len(reg_username) < 3:
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
            _build_authenticator.clear()
            st.success("Account created! Please switch to the Login tab.")


# Gate the app on authentication status (INT-8)
if not st.session_state.get("authentication_status"):
    st.title("🥃 Whiskey Recommender")
    tab_login, tab_register = st.tabs(["🔐 Login", "📝 Register"])

    with tab_login:
        authenticator = _build_authenticator()
        authenticator.login(location="main")
        if st.session_state.get("authentication_status") is False:
            st.error("Username or password is incorrect.")
        elif st.session_state.get("authentication_status") is None:
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

authenticator = _build_authenticator()

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

def display_whiskey(whiskey_doc, json_flag=None):

    if json_flag:
        #""" whiskey details in markdown format with tag pills."""
        # Extract metadata
        distillery = whiskey_doc.get("distillery", "Unknown Distillery")
        whiskey_name = whiskey_doc.get("whiskey_name", "Unknown Whiskey")
        age = whiskey_doc.get("age", "No Age Statement")
        region = whiskey_doc.get("distillery_region", "Unknown Region")

        nose_tags = whiskey_doc.get("nose_tags", [])
        palette_tags = whiskey_doc.get("palette_tags", [])
        finish_tags = whiskey_doc.get("finish_tags", [])
    else:
        #"""Displays whiskey details in markdown format with tag pills."""
        # Extract metadata
        distillery = whiskey_doc.metadata.get("distillery", "Unknown Distillery")
        whiskey_name = whiskey_doc.metadata.get("whiskey_name", "Unknown Whiskey")
        age = whiskey_doc.metadata.get("age", "No Age Statement")
        region = whiskey_doc.metadata.get("distillery_region", "Unknown Region")

        nose_tags = whiskey_doc.metadata.get("nose_tags", [])
        palette_tags = whiskey_doc.metadata.get("palette_tags", [])
        finish_tags = whiskey_doc.metadata.get("finish_tags", [])

    # Markdown display
    st.markdown(f"### {whiskey_name}")
    st.markdown(f"**{distillery}**")
    st.markdown(f"🕰️ Age: {age}")  # Age Statement
    st.markdown(f"📍 Region: {region}")  # Region

    # Display tags as pills
    if nose_tags:
        pills("👃 Nose Notes:", nose_tags, format_func=lambda x: x, index=None)
    if palette_tags:
        pills("👅 Palette Notes:", palette_tags, format_func=lambda x: x, index=None)
    if finish_tags:
        pills("🥃 Finish Notes:", finish_tags, format_func=lambda x: x, index=None)


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
                "index": "multiembed_index_test",
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
                "index": "multiembed_index_test",
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
                "index": "multiembed_index_test",
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

if advanced_search:
    # Show form for advanced search filters
    with st.form("Advanced Tasting Notes"):
        st.write("🔍 **Advanced Search Filters**")
        nose_notes = st.text_input("👃 Enter Nose Notes (comma-separated)", "")
        palette_notes = st.text_input("👅 Enter Palette Notes (comma-separated)", "")
        finish_notes = st.text_input("🥃 Enter Finish Notes (comma-separated)", "")

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
    query = st.text_input("🔍 Describe what you're looking for in a whiskey:")
    if query:
        filter_conditions = construct_pre_filter(selected_region=selected_region, selected_type=selected_type,
                                                 selected_country=selected_country)
        # Search vector database
        results = vector_store.similarity_search_with_score(query, k=num_whiskies, pre_filter=filter_conditions)


if results:
    st.subheader("🍂 Recommended Whiskeys")
    for doc, score in results:
        try:
            whiskey_name = doc.metadata.get("whiskey_name", "Unknown Whiskey")
            whiskey_id = doc.metadata.get('_id')
        except:
            whiskey_name = doc.get("whiskey_name", "Unknown Whiskey")
            whiskey_id = doc.get('_id')
        with st.expander(f"**{whiskey_name}** (Score: {score:.2f}) (ID: {whiskey_id}) "):
            try:
                display_whiskey(doc, json_flag=advanced_search)  # ✅ Use the new function
                # Bookmark button
                if st.button(f"📌 Add {whiskey_name} to Wishlist", key=f"{whiskey_name}_{whiskey_id}"):
                    if f"{whiskey_name}_{whiskey_id}" not in st.session_state.wishlist:
                        st.session_state.wishlist.append(f"{whiskey_name}_{whiskey_id}")
            except:
                pass

else:
    st.write("👆 Enter a description to find similar whiskeys.")
