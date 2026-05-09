import streamlit as st
from whiskey_structures import Whiskey, WhiskeyReview
from vector_db import *
from streamlit import pills

def display_drinking_session():
    st.title("Whiskey Drinking Session")

    # Search for whiskey
    search_query = st.text_input("Search for the whiskey you are drinking")
    if search_query:
        results = vector_store.similarity_search_with_score(search_query, k=5)
        whiskey_names = [(r.metadata.get('_id'), r.metadata.get('whiskey_name'), r.metadata.get('age')) for r,i in results]
        selected_whiskey = st.selectbox("Select the whiskey", whiskey_names)
    else:
        selected_whiskey = None

    # Feedback Form
    if selected_whiskey:
        selected_whiskey_doc = [x for x,i in results if x.metadata.get('_id') == selected_whiskey[0]][0]
        nose_options = selected_whiskey_doc.metadata.get('nose_tags')
        palette_options = selected_whiskey_doc.metadata.get('palette_tags')
        finish_options = selected_whiskey_doc.metadata.get('finish_tags')

        st.subheader("Step 1: Tasting Notes")
        nose = pills("Nose", options=nose_options, selection_mode='multi')
        extra_nose = st.text_input("Add additional nose notes")
        if extra_nose:
            nose += extra_nose.split(',')
        palette = pills("Palette", options=palette_options, selection_mode='multi')
        extra_palette = st.text_input("Add additional palette notes")
        if extra_palette:
            palette += extra_palette.split(',')
        finish = pills("Finish", options=finish_options, selection_mode='multi')
        extra_finish = st.text_input("Add additional finish notes")
        if extra_finish:
            finish += extra_finish.split(',')

        st.subheader("Step 2: Review")
        rating = st.slider("Rating (1-10)", 1, 10, 5)
        likes = st.pills("What did you like?", set(nose + palette + finish), selection_mode='multi', key='likes')
        dislikes = st.pills("What didn't you like?", set(nose + palette + finish), selection_mode='multi', key='dislikes')

        if st.button("Submit Feedback"):
            feedback = {
                "whiskey": selected_whiskey,
                "nose": nose,
                "palette": palette,
                "finish": finish,
                "rating": rating,
                "likes": likes,
                "dislikes": dislikes
            }
            st.success("Feedback submitted! Let's find your next whiskey...")

            nose_like = [tag for tag in nose if tag in likes]
            nose_dislike = [tag for tag in nose if tag in dislikes]
            palette_like = [tag for tag in palette if tag in likes]
            palette_dislike = [tag for tag in palette if tag in dislikes]
            finish_like = [tag for tag in finish if tag in likes]
            finish_dislike = [tag for tag in finish if tag in dislikes]

            st.session_state['nose_likes'] = nose_like
            st.session_state['palette_likes'] = palette_like
            st.session_state['finish_likes'] = finish_like
            st.rerun()