import streamlit as st
from openai import OpenAI
import json
import os
import time
from tools.proton import get_emails_pure, send_email_pure, delete_email_pure
from tools.todoist import create_new_task, get_filtered_tasks

from dotenv import load_dotenv
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ASSISTANT_ID = os.getenv("ASSISTANT_ID")

client = OpenAI(api_key=OPENAI_API_KEY)

if "thread_id" not in st.session_state:
    thread = client.beta.threads.create()
    st.session_state.thread_id = thread.id

st.title("Davide Personal Assistant")

def reset_thread():
    st.session_state.thread_id = None
    st.experimental_rerun()

with st.sidebar:
    st.title("Thread Control")
    if st.button("Reset Thread"):
        reset_thread()

messages = client.beta.threads.messages.list(
    thread_id=st.session_state.thread_id
)

with st.sidebar:
    messages_list = []
    for msg in messages.data:
        message_content = ""
        for content_block in msg.content:
            if content_block.type == 'text':
                message_content += content_block.text.value
        messages_list.append({
            "role": msg.role,
            "content": message_content,
            "created_at": msg.created_at
        })
    st.write("Thread Messages:")
    st.json(messages_list)

for message in reversed(messages.data):
    with st.chat_message(message.role):
        full_content = ""
        for content_block in message.content:
            if content_block.type == 'text':
                full_content += content_block.text.value
        st.markdown(full_content)

if user_query := st.chat_input("Ask me a question"):
    client.beta.threads.messages.create(
        thread_id=st.session_state.thread_id,
        role="user",
        content=user_query
    )
    with st.chat_message("user"):
        st.markdown(user_query)

    run = client.beta.threads.runs.create(
        thread_id=st.session_state.thread_id,
        assistant_id=ASSISTANT_ID
    )

    run_status = ""
    while run_status not in ["completed", "requires_action"]:
        run = client.beta.threads.runs.retrieve(
            thread_id=st.session_state.thread_id,
            run_id=run.id
        )
        run_status = run.status
        time.sleep(0.5)

    if run_status == "requires_action":
        tool_outputs = []
        for tool_call in run.required_action.submit_tool_outputs.tool_calls:
            function_name = tool_call.function.name
            try:
                args = json.loads(tool_call.function.arguments)
                if function_name == "get_emails":
                    output = get_emails_pure(**args)
                elif function_name == "send_email":
                    output = send_email_pure(**args)
                elif function_name == "delete_email":
                    output = delete_email_pure(**args)
                elif function_name == "create_new_task":
                    output = create_new_task(**args)
                elif function_name == "get_tasks":
                    output = get_filtered_tasks(**args)
                else:
                    output = f"Function {function_name} not implemented."

                print(f"Executing {function_name} with args {args}")
            except Exception as e:
                output = f"Error: {str(e)}"

            tool_outputs.append({
                "tool_call_id": tool_call.id,
                "output": json.dumps(output)
            })

        client.beta.threads.runs.submit_tool_outputs(
            thread_id=st.session_state.thread_id,
            run_id=run.id,
            tool_outputs=tool_outputs
        )

        # Wait for completion after submitting tool outputs
        while True:
            run = client.beta.threads.runs.retrieve(
                thread_id=st.session_state.thread_id,
                run_id=run.id
            )
            if run.status == "completed":
                break
            time.sleep(0.5)

    messages = client.beta.threads.messages.list(
        thread_id=st.session_state.thread_id
    )

    latest_message = messages.data[0]
    if latest_message.role == "assistant":
        with st.chat_message("assistant"):
            full_content = ""
            for content_block in latest_message.content:
                if content_block.type == 'text':
                    full_content += content_block.text.value
            st.markdown(full_content)