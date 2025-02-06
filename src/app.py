import streamlit as st
from streamlit_pills import pills
from vector_db import *
from language_models import *
# Initialize the vector store

# Streamlit App Title
st.title("🥃 Whiskey Recommender")

# Sidebar Wishlist
st.sidebar.header("📌 Wishlist")
if "wishlist" not in st.session_state:
    st.session_state.wishlist = []

for whiskey in st.session_state.wishlist:
    st.sidebar.write(f"- {whiskey}")

def display_whiskey(whiskey_doc):
    """Displays whiskey details in markdown format with tag pills."""

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
        #st.markdown("👃 **Nose Notes:**")
        pills("👃 Nose Notes:", nose_tags, format_func=lambda x: x, index=None)

    if palette_tags:
        #st.markdown("👅 **Palette Notes:**")
        pills("👅 Palette Notes:", palette_tags, format_func=lambda x: x, index=None)

    if finish_tags:
        #st.markdown("🥃 **Finish Notes:**")
        pills("🥃 Finish Notes:", finish_tags, format_func=lambda x: x, index=None)


# User Query Input
query = st.text_input("🔍 Describe what you're looking for in a whiskey:")

if query:
    # Search vector database
    results = vector_store.similarity_search_with_score(query, k=5)

    if results:
        st.subheader("🍂 Recommended Whiskeys")
        for doc, score in results:
            whiskey_name = doc.metadata.get("whiskey_name", "Unknown Whiskey")
            whiskey_id = doc.metadata.get('_id')
            with st.expander(f"**{whiskey_name}** (Score: {score:.2f})"):
                display_whiskey(doc)  # ✅ Use the new function

                # Bookmark button
                if st.button(f"📌 Add {whiskey_name} to Wishlist", key=f"{whiskey_name}_{whiskey_id}"):
                    if f"{whiskey_name}_{whiskey_id}" not in st.session_state.wishlist:
                        st.session_state.wishlist.append(f"{whiskey_name}_{whiskey_id}")

else:
    st.write("👆 Enter a description to find similar whiskeys.")