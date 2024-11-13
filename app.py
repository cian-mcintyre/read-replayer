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

@st.cache_resource
def get_file_name(file_id):
    # Check if file name is already cached
    if 'file_id_to_name' not in st.session_state:
        st.session_state.file_id_to_name = {}
    if file_id in st.session_state.file_id_to_name:
        return st.session_state.file_id_to_name[file_id]
    else:
        # Retrieve file information from OpenAI API
        file_info = client.files.retrieve(file_id)
        file_name = file_info.get('filename', file_id)
        st.session_state.file_id_to_name[file_id] = file_name
        return file_name

def extract_page_number(annotation_text):
    # Example: Extract page number from text like ''
    import re
    match = re.search(r'【(\d+):(\d+)†source】', annotation_text)
    if match:
        page_number = match.group(1)
        return page_number
    else:
        return None

def get_assistant_response(user_input=""):
    try:
        # Create the user message
        message = client.beta.threads.messages.create(
            thread_id=assistant_thread.id,
            role="user",
            content=user_input,
        )

        # Start the assistant run
        run = client.beta.threads.runs.create(
            thread_id=assistant_thread.id,
            assistant_id=assistant_id,
        )

        # Wait for the run to complete
        run = wait_on_run(run, assistant_thread)

        # Retrieve the assistant's reply
        messages = client.beta.threads.messages.list(
            thread_id=assistant_thread.id,
            order="asc",
            after=message.id
        )

        assistant_message = messages.data[0]
        content_blocks = assistant_message.content

        # Initialize variables to store the answer text and sources
        answer_text = ""
        sources = []

        # Process the content blocks
        for block in content_blocks:
            if block.type == 'text':
                # Extract the text value
                text_value = block.text.value
                answer_text += text_value

                # Process annotations to extract sources
                for annotation in block.text.annotations:
                    if annotation.type == 'file_citation':
                        file_citation = annotation.file_citation
                        # Get file ID
                        file_id = file_citation.file_id
                        # Get file name
                        file_name = get_file_name(file_id)
                        # Extract page number from annotation text
                        page_number = extract_page_number(annotation.text)
                        sources.append({'file_name': file_name, 'page_number': page_number})

        # Remove duplicate sources
        unique_sources = [dict(t) for t in {tuple(d.items()) for d in sources}]

        return answer_text, unique_sources
    except Exception as e:
        st.error(f"An error occurred: {e}")
        return "", []

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
        result, sources = get_assistant_response(user_input)
        if result:
            st.session_state.chat_history.append(("Assistant", result, sources))

st.text_input("", key='user_input', on_change=submit, placeholder="Type your question here...")

# Display chat history
for message in st.session_state.chat_history:
    if message[0] == "You":
        st.markdown(f"<div class='user-message'><strong>You:</strong> {message[1]}</div>", unsafe_allow_html=True)
    else:
        assistant_response = message[1]
        sources = message[2]
        st.markdown(f"<div class='assistant-message'><strong>Assistant:</strong> {assistant_response}</div>", unsafe_allow_html=True)
        if sources:
            st.markdown("<strong>Sources:</strong>", unsafe_allow_html=True)
            for source in sources:
                file_name = source['file_name']
                page_number = source.get('page_number', 'Unknown')
                st.markdown(f"- {file_name}, Page: {page_number}", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("ℹ️ About")
    st.write("This app helps you learn about upcoming elections.")
    st.write("You can ask questions about party manifestos and compare policies.")
    st.write("Feel free to ask any questions!")

    # Add a reset button
    if st.button("🔄 Reset Conversation"):
        st.session_state.chat_history = []