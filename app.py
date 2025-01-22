import streamlit as st
import time
from openai import OpenAI

# Set page configuration
st.set_page_config(
    page_title="Read Replayer",
    page_icon="📘",
    layout="wide",
    initial_sidebar_state="collapsed",
)

api_key = st.secrets["openai_apikey"]
assistant_id = st.secrets["assistant_id"]

@st.cache_resource
def load_openai_client_and_assistant():
    client = OpenAI(api_key=api_key)
    my_assistant = client.beta.assistants.retrieve(assistant_id)
    thread = client.beta.threads.create()
    return client, my_assistant, thread

client, my_assistant, assistant_thread = load_openai_client_and_assistant()

def wait_on_run(run, thread):
    while run.status in ["queued", "in_progress"]:
        run = client.beta.threads.runs.retrieve(
            thread_id=thread.id,
            run_id=run.id,
        )
        time.sleep(0.5)
    return run

def get_assistant_response(user_input=""):
    message = client.beta.threads.messages.create(
        thread_id=assistant_thread.id,
        role="user",
        content=user_input,
    )

    run = client.beta.threads.runs.create(
        thread_id=assistant_thread.id,
        assistant_id=assistant_id,
    )

    run = wait_on_run(run, assistant_thread)

    messages = client.beta.threads.messages.list(
        thread_id=assistant_thread.id,
        order="asc",
        after=message.id  # Fixed syntax here
    )

    return messages.data[0].content[0].text.value

# Initialize session state variables
if 'query' not in st.session_state:
    st.session_state.query = ''
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

# Add custom CSS for styling messages
st.markdown(
    """
    <style>
    /* Main container */
    .chat-container {
        max-width: 700px;
        margin: 0 auto;
    }
    /* User messages */
    .user-message {
        background-color: #DCF8C6; /* Light green */
        color: #000000;            /* Black text color */
        padding: 10px;
        border-radius: 10px;
        text-align: right;
        margin-bottom: 10px;
        margin-left: auto;         /* Adjusted */
        margin-right: 20px;        /* Adjusted */
        max-width: 60%;            /* Added */
    }
    /* Assistant messages */
    .assistant-message {
        background-color: #F1F0F0; /* Light gray */
        color: #000000;            /* Black text color */
        padding: 10px;
        border-radius: 10px;
        text-align: left;
        margin-bottom: 10px;
        margin-left: 20px;         /* Adjusted */
        margin-right: auto;        /* Adjusted */
        max-width: 60%;            /* Added */
    }
    /* Message text */
    .message-text {
        font-size: 16px;
        line-height: 1.5;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Streamlit App Layout
st.title("📘 Read Replayer 📘")

# Sidebar
with st.sidebar:
    st.header("ℹ️ About")
    st.write("This app helps you get spoiler-free book updates")
    st.write("You can ask questions about characters, chapters or plot summaries.")
    st.write("Tell me where you are in the book and I can give you a synopsis of what has happened so far. ")
    st.write("You can ask things like 'Who is X', or 'Why is X doing Y'")

    # Add a reset button
    if st.button("🔄 Reset Conversation"):
        st.session_state.chat_history = []
        st.experimental_rerun()

def submit():
    user_input = st.session_state.query.strip()
    st.session_state.query = ''

    if user_input:
        st.session_state.chat_history.append(("You", user_input))
        result = get_assistant_response(user_input)
        st.session_state.chat_history.append(("Assistant", result))

# Input field
st.text_input(
    "Ask me anything about the upcoming elections. I can search through all the main party manifestos and compare them.",
    key='query',
    on_change=submit
)

# Display chat history
with st.container():
    for sender, message in st.session_state.chat_history:
        if sender == "You":
            st.markdown(
                f"<div class='user-message'><div class='message-text'>{message}</div></div>",
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f"<div class='assistant-message'><div class='message-text'>{message}</div></div>",
                unsafe_allow_html=True
            )