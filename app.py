import streamlit as st
import time
from openai import OpenAI

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
if 'user_input' not in st.session_state:
    st.session_state.user_input = ''
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

# Streamlit App Layout
st.title("🗳️ Election Helper 🗳️")

def submit():
    user_input = st.session_state.query
    st.session_state.query = ''

    if user_input:
        st.session_state.chat_history.append(("You", user_input))
        result = get_assistant_response(user_input)
        st.session_state.chat_history.append(("Assistant", result))

# Input field
st.text_input("Ask me anything about the upcoming elections. I can search through all the main party manifestos and compare them.", key='query', on_change=submit)

# Display chat history
for sender, message in st.session_state.chat_history:
    if sender == "You":
        st.write(f"**You:** {message}")
    else:
        st.write(f"**Assistant:** {message}")
