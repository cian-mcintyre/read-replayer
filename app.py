import streamlit as st
import time
from openai import OpenAI

# Set page configuration
st.set_page_config(
    page_title="Election Helper",
    page_icon="🗳️",
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
    try:
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
            after=message.id
        )

        # Retrieve the assistant's reply message
        assistant_messages = [msg for msg in messages.data if msg.role == "assistant"]
        if assistant_messages:
            assistant_reply = assistant_messages[0].content
            return assistant_reply
        else:
            st.error("No assistant reply found.")
            return ""
    except Exception as e:
        st.error(f"An error occurred: {e}")
        return ""

# Initialize session state variables
if 'user_input' not in st.session_state:
    st.session_state.user_input = ''
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

# Add custom CSS
st.markdown(
    """
    <style>
    .chat-container {
        display: flex;
        flex-direction: column;
        margin-bottom: 20px;
    }
    .user-message, .assistant-message {
        max-width: 70%;
        padding: 10px;
        border-radius: 10px;
        margin-bottom: 10px;
        line-height: 1.5;
    }
    .user-message {
        align-self: flex-end;
        background-color: #DCF8C6; /* Light green */
        color: #000000;
    }
    .assistant-message {
        align-self: flex-start;
        background-color: #F1F0F0; /* Light gray */
        color: #000000;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Header and Instructions
st.markdown(
    """
    <div style='text-align: center;'>
        <h1>🗳️ Election Helper 🗳️</h1>
        <p>Ask me anything about the upcoming elections. I can search through all the main party manifestos and compare them.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# Input field
def submit():
    user_input = st.session_state.user_input.strip()
    st.session_state.user_input = ''

    if user_input:
        st.session_state.chat_history.append(("You", user_input))
        result = get_assistant_response(user_input)
        if result:
            st.session_state.chat_history.append(("Assistant", result))

# Input field
st.text_input("", key='user_input', on_change=submit, placeholder="Type your question here...")

# Display chat history
chat_container = st.container()
with chat_container:
    for sender, message in st.session_state.chat_history:
        if sender == "You":
            st.markdown(
                f"<div class='user-message'><strong>You:</strong> {message}</div>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f"<div class='assistant-message'><strong>Assistant:</strong> {message}</div>",
                unsafe_allow_html=True,
            )

# Sidebar
with st.sidebar:
    st.header("ℹ️ About")
    st.write("This app helps you learn about upcoming elections.")
    st.write("You can ask questions about party manifestos and compare policies.")
    st.write("Feel free to ask any questions!")

    # Add a reset button
    if st.button("🔄 Reset Conversation"):
        st.session_state.chat_history = []
        # Optionally, reset the assistant thread if needed