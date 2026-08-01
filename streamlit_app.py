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


def _check_secrets() -> str | None:
    """Validate that required secrets are configured. Returns error message or None."""
    try:
        secrets = st.secrets["snowflake"]
    except (KeyError, FileNotFoundError):
        return (
            "**Configuration missing.** No `[snowflake]` section found in secrets.\n\n"
            "Please add your Snowflake credentials to `.streamlit/secrets.toml`."
        )
    required = ["account", "user"]
    has_auth = "private_key" in secrets or "password" in secrets
    missing = [k for k in required if k not in secrets]
    if missing or not has_auth:
        parts = [f"`{k}`" for k in missing]
        if not has_auth:
            parts.append("`private_key` or `password`")
        return f"**Configuration incomplete.** Missing: {', '.join(parts)}"
    return None


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


def _get_healthy_connection():
    """Get a Snowflake connection, reconnecting if the cached one is stale."""
    conn = get_snowflake_connection()
    try:
        conn.cursor().execute("SELECT 1")
        return conn
    except Exception:
        # Cached connection went stale — clear and reconnect
        get_snowflake_connection.clear()
        return get_snowflake_connection()


# Check configuration before rendering UI
config_error = _check_secrets()
if config_error:
    st.error(config_error, icon="⚠️")
    st.stop()


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
        status_container = st.empty()
        response_container = st.empty()

        def _show_status(text):
            status_container.caption(f"⏳ {text}")

        _show_status("Connecting to database...")
        try:
            conn = _get_healthy_connection()
            _show_status("Generating answer...")
            import time
            start_time = time.time()
            response, updated_history = process_query(
                conn,
                st.session_state.conversation_history,
                prompt
            )
            elapsed = time.time() - start_time
            if elapsed > 5:
                _show_status(f"Completed in {elapsed:.1f}s")
                time.sleep(0.5)
            st.session_state.conversation_history = updated_history
        except snowflake.connector.errors.DatabaseError as e:
            error_code = getattr(e, 'errno', None)
            error_msg = str(e)
            if error_code == 250001 or "auth" in error_msg.lower():
                response = (
                    "**Authentication failed.** Snowflake rejected the login credentials.\n\n"
                    "Please verify your account, user, and private key / password in secrets.toml."
                )
            elif "warehouse" in error_msg.lower():
                response = (
                    "**Warehouse unavailable.** The configured warehouse may be suspended or "
                    "doesn't exist.\n\n"
                    "Try: `ALTER WAREHOUSE COMPUTE_WH RESUME;`"
                )
            else:
                response = (
                    "**Database error.** I'm having trouble executing the query.\n\n"
                    f"Detail: {error_msg[:200]}\n\n"
                    "Please try rephrasing your question."
                )
        except snowflake.connector.errors.OperationalError as e:
            response = (
                "**Connection lost.** The connection to Snowflake was interrupted.\n\n"
                "Please try again — I'll automatically reconnect."
            )
            get_snowflake_connection.clear()
        except Exception as e:
            error_msg = str(e)
            if "timeout" in error_msg.lower():
                response = (
                    "**Request timed out.** The query took too long. "
                    "Try a simpler question or narrow to a specific state/county."
                )
            else:
                response = (
                    "**Something went wrong.** I encountered an unexpected error.\n\n"
                    f"Detail: {error_msg[:200]}\n\n"
                    "Please try again."
                )
        status_container.empty()
        response_container.markdown(response)

    st.session_state.messages.append({"role": "assistant", "content": response})
