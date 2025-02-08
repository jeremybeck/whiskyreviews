import streamlit as st
from streamlit_pills import pills
from vector_db import *
from language_models import *
# Initialize the vector store
st.set_page_config(page_title="Whisk(e)y Explorer", page_icon="🥃")

# Streamlit App Title
st.title("🥃 Whiskey Recommender")

# Sidebar Wishlist
st.sidebar.header("📌 Wishlist")
if "wishlist" not in st.session_state:
    st.session_state.wishlist = []

for whiskey in st.session_state.wishlist:
    st.sidebar.write(f"- {whiskey}")

##distinct_regions = vectordb.distinct("distillery_region")# Fetch distinct regions
#distinct_types = vectordb.distinct("whiskey_type")  # Fetch distinct whiskey types
distinct_regions = ["Highlands", "Lowlands", "Speyside", "Islay", "Campbeltown", "Kentucky", "Tennessee", "Ireland",  "Japan"]
distinct_types =    ["Rye","Bourbon","Scotch", "Irish", "Japanese"]
distinct_countries = vectordb.distinct('whiskey_country_of_origin')

# 🔹 Sidebar Filters
num_whiskies = st.sidebar.slider("Number of Whiskeys", min_value=5, max_value=20, value=10, step=1)
selected_region = st.sidebar.selectbox("🌍 Filter by Region", ["All"] + distinct_regions)
selected_type = st.sidebar.selectbox("🥃 Filter by Whiskey Type", ["All"] + distinct_types)
selected_country = st.sidebar.selectbox("🥃 Filter by Country", ["All"] + distinct_countries)

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

# User Query Input
query = st.text_input("🔍 Describe what you're looking for in a whiskey:")

if query:
    filter_conditions = construct_pre_filter(selected_region=selected_region, selected_type=selected_type, selected_country=selected_country)
    print(filter_conditions)
    # Search vector database
    results = vector_store.similarity_search_with_score(query, k=num_whiskies, pre_filter=filter_conditions)

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
        st.subheader('No Results - Try Another Query')

else:
    st.write("👆 Enter a description to find similar whiskeys.")