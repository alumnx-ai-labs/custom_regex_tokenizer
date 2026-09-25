import streamlit as st

from api_client import ApiError, get_encodings, tokenize_file, tokenize_text

st.set_page_config(page_title="Tokenizer", page_icon="🔢")

st.title("Tokenizer")
st.write(
    "Paste text or upload a `.txt`/`.pdf` file to see exactly how it gets "
    "broken into tokens using `tiktoken`."
)

try:
    encodings = get_encodings()
except ApiError as exc:
    st.error(f"Could not reach the backend: {exc.detail}")
    st.stop()

encoding = st.selectbox("Encoding", encodings)

mode = st.radio("Input mode", ["Paste text", "Upload TXT file", "Upload PDF file"])

result = None
error = None

if mode == "Paste text":
    text = st.text_area("Text", height=200)
    if st.button("Tokenize"):
        try:
            result = tokenize_text(text, encoding)
        except ApiError as exc:
            error = exc
else:
    file_type = "txt" if mode == "Upload TXT file" else "pdf"
    uploaded_file = st.file_uploader(
        f"Upload a .{file_type} file", type=[file_type]
    )
    if st.button("Tokenize") and uploaded_file is not None:
        try:
            result = tokenize_file(
                uploaded_file.getvalue(), uploaded_file.name, encoding
            )
        except ApiError as exc:
            error = exc

if error is not None:
    st.error(f"{error.error_code}: {error.detail}")

if result is not None:
    if result["source_type"] != "text":
        st.subheader("Extracted Text")
        st.text_area("Extracted text", result["text"], height=200, disabled=True)

    st.subheader("Statistics")
    stats = result["statistics"]
    cols = st.columns(5)
    cols[0].metric("Characters", stats["character_count"])
    cols[1].metric("Words", stats["word_count"])
    cols[2].metric("Tokens", stats["token_count"])
    cols[3].metric("Tokens/Word", f"{stats['tokens_per_word']:.2f}")
    cols[4].metric("Tokens/Char", f"{stats['tokens_per_character']:.2f}")

    st.subheader("Tokens")
    for token in result["tokens"]:
        st.markdown(
            f"`#{token['index']}` **ID:** `{token['token_id']}` "
            f"**Decoded:** `{token['decoded_text']}`"
        )
