# LLM-powered agent for US Census data queries with guardrails
# Co-authored with CoCo

import json
import re
from census_schema import SCHEMA_DESCRIPTION, STATE_ABBREVIATIONS, AVAILABLE_TOPICS


SYSTEM_PROMPT = f"""You are a helpful assistant that answers questions about US Census data.
You have access to American Community Survey (ACS) 2020 5-year estimates aggregated at the
state and county level.

{SCHEMA_DESCRIPTION}

INSTRUCTIONS:
1. When a user asks a question about census data, generate a SQL query to answer it.
2. Return your response as JSON with this structure:
   {{"action": "query", "sql": "<SQL query>", "explanation": "<brief explanation of what the query does>"}}

3. If the question is NOT about US Census/demographics data, return:
   {{"action": "refuse", "message": "<polite explanation that you can only answer Census-related questions>"}}

4. If the question is ambiguous or you need clarification, return:
   {{"action": "clarify", "message": "<ask for clarification>"}}

5. If the question CANNOT be answered with the available data, return:
   {{"action": "unavailable", "message": "<explain what data is available and what is not>"}}

CRITICAL OUTPUT FORMAT RULES:
- Return ONLY the raw JSON object. Nothing else.
- Do NOT wrap the JSON in markdown code fences (no ```json or ```).
- Do NOT add any explanation text before or after the JSON.
- The response must start with {{ and end with }}.
- For follow-up questions (like "and Texas?"), use the conversation context to understand what data was previously requested.
SQL RULES:
- Always use fully qualified names: CENSUS_AGENT.PUBLIC.<view_name>
- Use state abbreviations in WHERE clauses (e.g., STATE_NAME = 'CA' not 'California')
- For state name lookups, the user might say full names - convert to abbreviations
- Always include ORDER BY for ranked results
- Use LIMIT for top-N queries (default LIMIT 10 unless specified)
- Format large numbers with ROUND() where appropriate
- For percentage calculations, multiply by 100 and round to 1 decimal
- Never use SELECT *; always specify columns explicitly
- Return at most 20 rows unless user specifically asks for more
- When user asks about a STATE (e.g. "New York", "California"), use V_STATE_* views (V_STATE_SUMMARY, V_STATE_INCOME, V_STATE_EMPLOYMENT, V_STATE_EDUCATION, V_STATE_HOUSING) - they have one row per state, pre-aggregated
- Only use county-level views (V_POPULATION, V_INCOME, V_HOUSING, V_EDUCATION, V_EMPLOYMENT) when the user specifically asks about counties
- Always include meaningful labels in results (e.g. STATE_NAME, COUNTY alongside numeric values)
- Use V_STATE_SUMMARY for population, V_STATE_INCOME for income, V_STATE_EMPLOYMENT for jobs, V_STATE_EDUCATION for education, V_STATE_HOUSING for housing
- All V_STATE_* views include TOTAL_POPULATION, so you can ORDER BY TOTAL_POPULATION in any of them without needing a JOIN

TOPICS YOU CAN ANSWER:
- Population counts and demographics (age, sex, race/ethnicity)
- Household income distribution and median income
- Housing units, homeownership rates, home values
- Educational attainment levels
- Employment, unemployment rates, labor force participation
- Commute/transportation to work (drove alone, carpooled, public transit, bike, walk, WFH)
- Poverty rates
- Health insurance coverage and uninsured rates
- Internet/broadband access
- Language spoken at home (English, Spanish, Asian/Pacific, other)
- Household type (family, married couple, single parent, living alone)
- Veteran status
- SNAP/food stamp receipt
- Comparisons between states and counties

TOPICS YOU CANNOT ANSWER (politely decline):
- Individual-level data (specific people)
- Data newer than 2020
- Crime statistics, health data, voting patterns
- Business/economic data beyond household income
- Climate, environment, transportation specifics
- Non-US geographies
"""


def build_messages(conversation_history, user_message):
    """Build the message list for the LLM, including conversation context."""
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for msg in conversation_history[-10:]:
        messages.append(msg)
    messages.append({"role": "user", "content": user_message})
    return messages


def parse_llm_response(response_text):
    """Parse the LLM response, handling various formatting issues from Snowflake."""
    if not response_text:
        return {"action": "error", "message": "Empty response from AI service."}
    
    text = response_text.strip()
    
    # Remove outer quotes if wrapped (Snowflake string return format)
    if text.startswith('"') and text.endswith('"'):
        text = text[1:-1]
    
    # Handle Snowflake's double-quote escaping: "" -> "
    # But be careful: we need to do this iteratively since SQL inside JSON 
    # might have multiple levels of escaping
    text = text.replace('\\\\', '\x00')  # Preserve actual escaped backslashes
    text = text.replace('\\"', '"')       # Handle \"
    text = text.replace('""', '"')        # Handle ""
    text = text.replace('\x00', '\\')     # Restore backslashes
    
    # Remove markdown code fences if present
    text = re.sub(r'```json\s*', '', text)
    text = re.sub(r'```\s*', '', text)
    text = text.strip()
    
    # First try: direct JSON parse of the whole text
    try:
        result = json.loads(text)
        if isinstance(result, dict) and "action" in result:
            return result
    except (json.JSONDecodeError, ValueError):
        pass
    
    # Second try: find JSON object with balanced brace matching
    start_idx = text.find('{')
    if start_idx != -1:
        depth = 0
        in_string = False
        escape_next = False
        for i in range(start_idx, len(text)):
            ch = text[i]
            if escape_next:
                escape_next = False
                continue
            if ch == '\\':
                escape_next = True
                continue
            if ch == '"':
                in_string = not in_string
                continue
            if in_string:
                continue
            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    json_str = text[start_idx:i+1]
                    try:
                        return json.loads(json_str)
                    except json.JSONDecodeError:
                        pass
                    # Try with single quotes in SQL converted
                    try:
                        # Sometimes the SQL has unescaped quotes - try to fix
                        fixed = re.sub(r"(?<=: )\"(SELECT[^}]+)\"", lambda m: json.dumps(m.group(1)), json_str)
                        return json.loads(fixed)
                    except (json.JSONDecodeError, ValueError):
                        pass
                    break
    
    # Third try: regex extraction of action and fields
    action_match = re.search(r'"action"\s*:\s*"(\w+)"', text)
    if action_match:
        action = action_match.group(1)
        result = {"action": action}
        sql_match = re.search(r'"sql"\s*:\s*"((?:[^"\\]|\\.)*)"', text)
        if sql_match:
            result["sql"] = sql_match.group(1).replace('\\"', '"')
        msg_match = re.search(r'"(?:message|explanation)"\s*:\s*"((?:[^"\\]|\\.)*)"', text)
        if msg_match:
            result["message" if action != "query" else "explanation"] = msg_match.group(1)
        return result
    
    return {
        "action": "error",
        "message": "I had trouble processing that request. Could you rephrase your question?"
    }


def resolve_state_name(user_input):
    """Convert full state names to abbreviations in user queries."""
    text = user_input
    reverse_map = {v.lower(): k for k, v in STATE_ABBREVIATIONS.items()}
    for full_name, abbrev in reverse_map.items():
        if full_name in text.lower():
            text = re.sub(re.escape(full_name), abbrev, text, flags=re.IGNORECASE)
    return text


def is_census_related(user_message):
    """Quick check if the message is likely census-related."""
    msg_lower = user_message.lower()
    census_keywords = [
        'population', 'people', 'residents', 'inhabitants',
        'income', 'salary', 'earn', 'poverty', 'wealthy', 'rich', 'poor',
        'housing', 'homes', 'rent', 'own', 'homeowner', 'house',
        'education', 'college', 'degree', 'school', 'graduate',
        'employ', 'job', 'work', 'unemploy', 'labor',
        'age', 'old', 'young', 'senior', 'elderly', 'youth',
        'race', 'ethnic', 'hispanic', 'latino', 'white', 'black', 'asian',
        'male', 'female', 'men', 'women', 'gender', 'sex',
        'state', 'county', 'census', 'demographic',
        'california', 'texas', 'new york', 'florida',
        'compare', 'highest', 'lowest', 'most', 'least', 'top', 'bottom',
        'how many', 'which state', 'which county',
        'commute', 'transport', 'drive', 'transit', 'bicycle', 'walk', 'bus',
        'insur', 'uninsured', 'health coverage', 'medicaid', 'medicare',
        'internet', 'broadband', 'computer', 'online',
        'poverty', 'food stamp', 'snap',
        'language', 'english', 'spanish', 'bilingual',
        'veteran', 'military', 'served',
        'household', 'family', 'married', 'single', 'alone', 'living alone'
    ]
    return any(kw in msg_lower for kw in census_keywords)


def validate_sql(sql):
    """Basic SQL validation to prevent dangerous operations."""
    sql_upper = sql.upper().strip()
    forbidden = ['DROP', 'DELETE', 'INSERT', 'UPDATE', 'ALTER', 'CREATE',
                 'TRUNCATE', 'GRANT', 'REVOKE', 'EXECUTE']
    for word in forbidden:
        if re.search(rf'\b{word}\b', sql_upper):
            return False, f"Query contains forbidden operation: {word}"
    allowed_tables = [
        'CENSUS_AGENT.PUBLIC.V_POPULATION',
        'CENSUS_AGENT.PUBLIC.V_INCOME',
        'CENSUS_AGENT.PUBLIC.V_HOUSING',
        'CENSUS_AGENT.PUBLIC.V_EDUCATION',
        'CENSUS_AGENT.PUBLIC.V_EMPLOYMENT',
        'CENSUS_AGENT.PUBLIC.V_COMMUTE',
        'CENSUS_AGENT.PUBLIC.V_POVERTY',
        'CENSUS_AGENT.PUBLIC.V_HEALTH_INSURANCE',
        'CENSUS_AGENT.PUBLIC.V_INTERNET',
        'CENSUS_AGENT.PUBLIC.V_LANGUAGE',
        'CENSUS_AGENT.PUBLIC.V_HOUSEHOLD_TYPE',
        'CENSUS_AGENT.PUBLIC.V_VETERANS',
        'CENSUS_AGENT.PUBLIC.V_SNAP',
        'CENSUS_AGENT.PUBLIC.V_STATE_SUMMARY',
        'CENSUS_AGENT.PUBLIC.V_STATE_INCOME',
        'CENSUS_AGENT.PUBLIC.V_STATE_EMPLOYMENT',
        'CENSUS_AGENT.PUBLIC.V_STATE_EDUCATION',
        'CENSUS_AGENT.PUBLIC.V_STATE_HOUSING',
        'CENSUS_AGENT.PUBLIC.V_STATE_COMMUTE',
        'CENSUS_AGENT.PUBLIC.V_STATE_POVERTY',
        'CENSUS_AGENT.PUBLIC.V_STATE_HEALTH_INSURANCE',
        'CENSUS_AGENT.PUBLIC.V_STATE_INTERNET',
        'CENSUS_AGENT.PUBLIC.V_STATE_LANGUAGE',
        'CENSUS_AGENT.PUBLIC.V_STATE_HOUSEHOLD_TYPE',
        'CENSUS_AGENT.PUBLIC.V_STATE_VETERANS',
        'CENSUS_AGENT.PUBLIC.V_STATE_SNAP'
    ]
    if not any(t in sql_upper for t in [t.upper() for t in allowed_tables]):
        return False, "Query does not reference any allowed Census views"
    return True, ""


def format_results(df, explanation):
    """Format query results into a readable response."""
    if df is None or len(df) == 0:
        return "The query returned no results. This might mean the data isn't available for that specific area or criteria."

    response_parts = [explanation, ""]

    if len(df) == 1 and len(df.columns) <= 4:
        for col in df.columns:
            val = df.iloc[0][col]
            if isinstance(val, (int, float)) and abs(val) > 1000:
                val = f"{val:,.0f}"
            elif isinstance(val, float):
                val = f"{val:.1f}"
            response_parts.append(f"**{col.replace('_', ' ').title()}**: {val}")
    else:
        # Always show as a table with headers
        response_parts.append(df.head(20).to_markdown(index=False))
        if len(df) > 20:
            response_parts.append(f"\n*Showing first 20 of {len(df)} results.*")

    return "\n".join(response_parts)


MAX_RETRIES = 3


def _execute_with_retry(conn, sql, explanation, messages):
    """Execute SQL with agentic retry — feed errors back to the LLM for correction."""
    import pandas as pd

    last_error = None
    current_sql = sql
    retry_messages = list(messages)

    for attempt in range(MAX_RETRIES):
        is_valid, error_msg = validate_sql(current_sql)
        if not is_valid:
            last_error = error_msg
            break

        try:
            cursor = conn.cursor()
            cursor.execute(current_sql)
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchmany(50)
            df = pd.DataFrame(rows, columns=columns)
            cursor.close()
            return format_results(df, explanation)
        except Exception as e:
            last_error = str(e)[:400]

            if attempt == MAX_RETRIES - 1:
                break

            # Feed the error back to the LLM as context for a retry
            retry_messages.append({
                "role": "assistant",
                "content": json.dumps({"action": "query", "sql": current_sql, "explanation": explanation})
            })
            retry_messages.append({
                "role": "user",
                "content": (
                    f"That SQL query failed with this error:\n{last_error}\n\n"
                    f"Please fix the query and try again. Return the corrected JSON "
                    f"with action 'query' and the fixed SQL."
                )
            })

            try:
                retry_response = call_cortex_complete(conn, retry_messages)
            except Exception:
                break

            if not retry_response:
                break

            retry_parsed = parse_llm_response(retry_response)
            if retry_parsed.get("action") != "query" or not retry_parsed.get("sql"):
                break

            current_sql = retry_parsed["sql"]
            explanation = retry_parsed.get("explanation", explanation)

    return (
        f"I tried {attempt + 1} time(s) but couldn't get a working query. "
        f"Last error: {last_error}\n\n"
        f"Could you rephrase or be more specific?"
    )


def call_cortex_complete(conn, messages, model="llama3.1-70b"):
    """Call Snowflake Cortex Complete function."""
    # Flatten messages into a single prompt string
    prompt_parts = []
    for msg in messages:
        role = msg["role"]
        content = msg["content"]
        if role == "system":
            prompt_parts.append(f"[SYSTEM INSTRUCTIONS]\n{content}\n[END SYSTEM INSTRUCTIONS]\n")
        elif role == "user":
            prompt_parts.append(f"User: {content}")
        elif role == "assistant":
            prompt_parts.append(f"Assistant: {content}")
    prompt_parts.append("Assistant:")
    full_prompt = "\n\n".join(prompt_parts)

    # Use a Snowflake session variable to pass the prompt safely
    cursor = conn.cursor()
    try:
        # Set prompt as session variable (avoids all escaping issues)
        cursor.execute("CREATE OR REPLACE TEMPORARY TABLE _cortex_prompt(prompt VARCHAR(16777216))")
        cursor.execute("INSERT INTO _cortex_prompt VALUES (%s)", (full_prompt,))
        cursor.execute(f"SELECT SNOWFLAKE.CORTEX.COMPLETE('{model}', (SELECT prompt FROM _cortex_prompt)) AS response")
        result = cursor.fetchone()
        if result and result[0]:
            return result[0] if isinstance(result[0], str) else str(result[0])
        return None
    finally:
        cursor.close()


def process_query(conn, conversation_history, user_message):
    """
    Main agent logic: process user message, generate SQL, execute, return response.
    Returns (response_text, updated_history).
    """
    import pandas as pd

    if not is_census_related(user_message) and len(conversation_history) == 0:
        refusal = (
            "I'm a US Census data assistant. I can help you with questions about "
            "population demographics, income, housing, education, and employment "
            "across US states and counties (based on ACS 2020 data). "
            "Could you ask me something related to these topics?"
        )
        return refusal, conversation_history

    messages = build_messages(conversation_history, user_message)

    try:
        llm_response = call_cortex_complete(conn, messages)
    except Exception as e:
        return f"I encountered an error connecting to the AI service: {str(e)[:200]}", conversation_history

    if llm_response is None:
        return "I'm having trouble processing your request right now. Please try again.", conversation_history

    parsed = parse_llm_response(llm_response)
    action = parsed.get("action", "error")

    # Debug: if parsing failed, include a hint of what was received
    if action == "error":
        preview = llm_response[:300] if llm_response else "None"
        parsed["message"] = parsed["message"] + f"\n\n*Debug: Raw response preview: {preview}...*"

    if action == "refuse":
        response = parsed.get("message", "I can only answer questions about US Census data.")
    elif action == "clarify":
        response = parsed.get("message", "Could you provide more details about what you're looking for?")
    elif action == "unavailable":
        response = parsed.get("message", "That specific data isn't available in my dataset.")
    elif action == "query":
        sql = parsed.get("sql", "")
        explanation = parsed.get("explanation", "")

        is_valid, error_msg = validate_sql(sql)
        if not is_valid:
            response = f"I generated an unsafe query and caught it. Error: {error_msg}. Please rephrase."
        else:
            response = _execute_with_retry(conn, sql, explanation, messages)
    else:
        response = parsed.get("message", "I had trouble understanding that. Could you rephrase?")

    updated_history = conversation_history + [
        {"role": "user", "content": user_message},
        {"role": "assistant", "content": response}
    ]

    return response, updated_history
