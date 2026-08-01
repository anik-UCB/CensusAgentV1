# US Census Data Chat Agent

An interactive, chat-based agent that answers natural language questions grounded in the US Census dataset (American Community Survey 2020, 5-year estimates).

## Live Demo

Deploy on Streamlit Community Cloud for a public URL accessible without login:
`https://<your-app-name>.streamlit.app`

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│  Streamlit Community Cloud (Public URL)                  │
│                                                         │
│  ┌───────────────┐    ┌──────────────────────────────┐ │
│  │ streamlit_app │───▶│ agent.py                     │ │
│  │ (Chat UI)     │    │ - Guardrail classifier       │ │
│  │               │    │ - Message builder (context)   │ │
│  │ session_state │    │ - SQL validator              │ │
│  │ (history)     │    │ - Result formatter           │ │
│  └───────────────┘    └──────────┬───────────────────┘ │
│                                  │                      │
└──────────────────────────────────┼──────────────────────┘
                                   │ Snowflake Connector
                                   ▼
┌─────────────────────────────────────────────────────────┐
│  Snowflake                                              │
│                                                         │
│  ┌────────────────────┐   ┌──────────────────────────┐ │
│  │ CORTEX.COMPLETE()  │   │ CENSUS_AGENT.PUBLIC       │ │
│  │ (llama3.1-70b)     │   │ ├── V_POPULATION         │ │
│  │                    │   │ ├── V_INCOME              │ │
│  │ NL → SQL generation│   │ ├── V_HOUSING            │ │
│  │ + guardrails       │   │ ├── V_EDUCATION          │ │
│  └────────────────────┘   │ ├── V_EMPLOYMENT         │ │
│                            │ └── V_STATE_SUMMARY      │ │
│                            └──────────────────────────┘ │
│                                      ▲                  │
│                    Curated views over │                  │
│                    SafeGraph ACS 2020 │                  │
│                    (242K+ block groups aggregated to     │
│                     state/county level)                  │
└─────────────────────────────────────────────────────────┘
```

### Key Design Decisions

1. **Grounded responses**: All data answers come from SQL queries against real Census views — the LLM generates SQL, not data. This eliminates hallucinated statistics.

2. **Two-layer LLM approach**: Cortex Complete (llama3.1-70b) handles both NL→SQL translation and conversational context. The system prompt embeds full schema documentation.

3. **Guardrails**:
   - **Keyword pre-filter**: Fast check rejects obviously off-topic messages before calling the LLM
   - **LLM-level instructions**: System prompt explicitly defines what topics are in/out of scope
   - **SQL validation**: Generated SQL is validated against an allowlist of views and blocked operations
   - **Graceful degradation**: Errors return helpful messages, not stack traces

4. **Conversation context**: Last 10 messages are passed to the LLM on each turn, enabling follow-up questions like "And Texas?" after asking about California.

5. **Data aggregation**: Raw Census Block Group data (242K rows) is pre-aggregated to state/county level via Snowflake views, making queries fast and responses interpretable.

## Project Structure

```
census-chat-agent/
├── streamlit_app.py          # Chat UI (Streamlit)
├── agent.py                  # LLM agent logic, guardrails, SQL gen
├── census_schema.py          # Schema metadata for LLM grounding
├── requirements.txt          # Python dependencies
├── .streamlit/
│   └── secrets.toml.example  # Credential template
├── sql/
│   └── setup_views.sql       # SQL to create Census views in Snowflake
├── tests/
│   ├── __init__.py
│   ├── test_guardrails.py    # Topic classification + SQL safety
│   ├── test_query_gen.py     # Query pattern validation
│   └── test_conversation.py  # Multi-turn context + edge cases
└── README.md
```

## Setup

### 1. Snowflake Prerequisites

You need a Snowflake account with:
- The **SafeGraph US Open Census Data** marketplace listing installed
- A warehouse (default: `COMPUTE_WH`)
- Access to `SNOWFLAKE.CORTEX.COMPLETE` function

Run the setup SQL to create the curated views:

```sql
-- Execute sql/setup_views.sql in your Snowflake account
-- This creates CENSUS_AGENT database with 6 views
```

### 2. Local Development

```bash
# Clone the repo
git clone <your-repo-url>
cd census-chat-agent

# Install dependencies
pip install -r requirements.txt

# Configure credentials
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# Edit .streamlit/secrets.toml with your Snowflake credentials

# Run locally
streamlit run streamlit_app.py
```

### 3. Deploy to Streamlit Community Cloud

1. Push this repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub repo
4. Set the main file to `streamlit_app.py`
5. In **App Settings > Secrets**, paste your Snowflake credentials:

```toml
[snowflake]
account = "xy12345.us-east-1"
user = "CENSUS_APP_USER"
password = "your_password"
role = "ACCOUNTADMIN"
warehouse = "COMPUTE_WH"
```

6. Deploy — your app will be live at `https://<app>.streamlit.app`

### 4. (Recommended) Create a Service User

For production, create a dedicated read-only user:

```sql
CREATE ROLE CENSUS_READER;
GRANT USAGE ON DATABASE CENSUS_AGENT TO ROLE CENSUS_READER;
GRANT USAGE ON SCHEMA CENSUS_AGENT.PUBLIC TO ROLE CENSUS_READER;
GRANT SELECT ON ALL VIEWS IN SCHEMA CENSUS_AGENT.PUBLIC TO ROLE CENSUS_READER;
GRANT USAGE ON DATABASE US_OPEN_CENSUS_DATA_NEIGHBORHOOD_INSIGHTS_FREE_DATASET TO ROLE CENSUS_READER;
GRANT USAGE ON SCHEMA US_OPEN_CENSUS_DATA_NEIGHBORHOOD_INSIGHTS_FREE_DATASET.PUBLIC TO ROLE CENSUS_READER;
GRANT SELECT ON ALL TABLES IN SCHEMA US_OPEN_CENSUS_DATA_NEIGHBORHOOD_INSIGHTS_FREE_DATASET.PUBLIC TO ROLE CENSUS_READER;
GRANT USAGE ON WAREHOUSE COMPUTE_WH TO ROLE CENSUS_READER;

CREATE USER CENSUS_APP_SVC PASSWORD='<strong_password>' DEFAULT_ROLE=CENSUS_READER;
GRANT ROLE CENSUS_READER TO USER CENSUS_APP_SVC;
```

## Testing

### Run Tests

```bash
# With pytest
pytest tests/ -v

# Without pytest (standalone)
python -m tests.test_guardrails
python -m tests.test_query_gen
python -m tests.test_conversation
```

### Testing Strategy

| Layer | What's tested | Approach |
|-------|--------------|----------|
| **Guardrails** | Topic classification (on/off-topic), SQL safety validation | Unit tests with known inputs — no Snowflake connection needed |
| **Query patterns** | Structural SQL validity, message building, history truncation | Unit tests verifying generated SQL passes validation |
| **Conversation** | Multi-turn context, edge cases (empty input, unicode, injection) | Unit tests for message assembly; integration tests need live connection |
| **End-to-end** | Full query flow: NL → SQL → results → formatted response | Requires Snowflake connection; run manually or in CI with secrets |

**Tradeoffs**:
- Unit tests (46 tests) run fast, no infrastructure needed, catch most logic bugs
- Integration/E2E tests require a live Snowflake connection but validate the full pipeline
- The LLM layer is tested indirectly via response parsing tests (mocking the LLM output format)
- We test the *contract* (input/output shape) rather than specific LLM outputs, since those are non-deterministic

## Example Conversations

**Simple factual:**
> User: What is the population of California?
> Agent: California has a total population of 39,346,023.

**Comparative:**
> User: Which 5 states have the highest unemployment rate?
> Agent: [table with state names and rates]

**Follow-up (context preserved):**
> User: What about their education levels?
> Agent: [table showing education for those same states]

**Off-topic (guardrail):**
> User: What's the best pizza in New York?
> Agent: I'm a US Census data assistant. I can help with demographics, income, housing, education, and employment data. Could you ask something related to these topics?

**Unanswerable (graceful):**
> User: What was the population of California in 2023?
> Agent: My data is from the ACS 2020 5-year estimates. I don't have data for 2023. I can tell you the 2020 population if that would help.

## Data Source

- **Dataset**: SafeGraph US Open Census Data (free Snowflake Marketplace listing)
- **Source**: US Census Bureau American Community Survey (ACS), 2020 5-year estimates
- **Granularity**: Aggregated from Census Block Group level to state/county
- **Coverage**: All 50 states + DC + Puerto Rico (~3,200 counties)
- **Topics**: Population, income, housing, education, employment
