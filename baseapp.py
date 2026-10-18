
import os

import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

# Load configuration from the local .env file
load_dotenv()

ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "").rstrip("/")
# st.write("Configured endpoint:", ENDPOINT)
# st.write("Request base URL:", f"{ENDPOINT}/openai/v1/")
API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT")

st.set_page_config(
    page_title="CampusMate Lite",
    page_icon="🎓",
    layout="centered",
)

st.title("CampusMate Lite")
st.subheader("Your AI-powered study assistant")
st.write(
    "Enter an academic question or topic, and GPT-4.1 "
    "will help you understand it."
)

question = st.text_area(
    "What would you like help with?",
    placeholder="Example: Explain operating system deadlocks.",
    height=120,
)

if st.button("Generate Answer", type="primary"):
    if not question.strip():
        st.warning("Please enter a question first.")
    elif not ENDPOINT or not API_KEY or not DEPLOYMENT:
        st.error("Configuration is missing. Check your .env file.")
    else:
        try:
            with st.spinner("CampusMate is thinking..."):
                client = OpenAI(
                    api_key=API_KEY,
                    base_url=f"{ENDPOINT}/openai/v1/",
                )

                
            response = client.responses.create(
                model=DEPLOYMENT,
                instructions=(
                    "You are CampusMate, a helpful academic assistant. "
                    "Explain concepts clearly, use examples, and structure "
                    "answers for college students."
                ),
                input=question,
            )

            answer = response.output_text


            st.subheader("Your Answer")
            st.markdown(answer or "The model returned an empty response.")

        
        except Exception as e:
            st.error("AI request failed.")
            st.write("Error type:", type(e).__name__)
            st.code(str(e))

            st.info(
                "If the problem persists, inspect the terminal "
                "for the detailed error message."
            )
