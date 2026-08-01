# Streamlit chat UI for the US Census Data Agent
# Co-authored with CoCo

import streamlit as st
import snowflake.connector
from agent import process_query

st.set_page_config(
    page_title="US Census Chat Agent",
    page_icon="📊",
    layout="centered"
)

st.title("US Census Data Chat Agent")
st.caption("Ask questions about US demographics, income, housing, education, and employment (ACS 2020)")


@st.cache_resource
def get_snowflake_connection():
    """Create and cache Snowflake connection."""
    connect_params = {
        "account": st.secrets["snowflake"]["account"],
        "user": st.secrets["snowflake"]["user"],
        "role": st.secrets["snowflake"].get("role", "ACCOUNTADMIN"),
        "warehouse": st.secrets["snowflake"].get("warehouse", "COMPUTE_WH"),
        "database": "CENSUS_AGENT",
        "schema": "PUBLIC",
    }

    if "private_key" in st.secrets["snowflake"]:
        from cryptography.hazmat.primitives import serialization
        private_key_pem = st.secrets["snowflake"]["private_key"].encode()
        private_key_obj = serialization.load_pem_private_key(private_key_pem, password=None)
        private_key_bytes = private_key_obj.private_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )
        connect_params["private_key"] = private_key_bytes
    else:
        connect_params["password"] = st.secrets["snowflake"].get("password", "")

    return snowflake.connector.connect(**connect_params)


if "messages" not in st.session_state:
    st.session_state.messages = []
if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = []

with st.sidebar:
    st.header("About")
    st.markdown("""
    This agent answers questions about US Census data using the 
    **American Community Survey (ACS) 2020** 5-year estimates.
    
    **Topics covered:**
    - Population & demographics
    - Income distribution
    - Housing & homeownership
    - Educational attainment
    - Employment & labor force
    
    **Geographic levels:**
    - All 50 states + DC + PR
    - County-level detail
    
    **Example questions:**
    - "What is the population of California?"
    - "Which state has the highest unemployment rate?"
    - "Compare median income between Texas counties"
    - "What percentage of people in New York have a bachelor's degree?"
    """)
    if st.button("Clear conversation"):
        st.session_state.messages = []
        st.session_state.conversation_history = []
        st.rerun()

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Ask about US Census data..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                conn = get_snowflake_connection()
                response, updated_history = process_query(
                    conn,
                    st.session_state.conversation_history,
                    prompt
                )
                st.session_state.conversation_history = updated_history
            except Exception as e:
                response = (
                    "I'm having trouble connecting to the database right now. "
                    "Please check the connection settings and try again.\n\n"
                    f"Error: {str(e)[:200]}"
                )
        st.markdown(response)

    st.session_state.messages.append({"role": "assistant", "content": response})
