# Tests for the guardrail and topic classification logic
# Co-authored with CoCo

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent import is_census_related, validate_sql, parse_llm_response, resolve_state_name


class TestGuardrails:
    """Test the guardrail functions that prevent off-topic responses."""

    def test_census_related_population(self):
        assert is_census_related("What is the population of California?")

    def test_census_related_income(self):
        assert is_census_related("Which state has the highest median income?")

    def test_census_related_housing(self):
        assert is_census_related("How many homes are owner-occupied in Texas?")

    def test_census_related_education(self):
        assert is_census_related("What percentage of people have a college degree?")

    def test_census_related_employment(self):
        assert is_census_related("What is the unemployment rate in Michigan?")

    def test_census_related_comparison(self):
        assert is_census_related("Compare population between New York and Florida")

    def test_census_related_demographics(self):
        assert is_census_related("What is the racial breakdown of Georgia?")

    def test_not_census_weather(self):
        assert not is_census_related("What is the weather like today?")

    def test_not_census_recipe(self):
        assert not is_census_related("How do I make chocolate cake?")

    def test_not_census_programming(self):
        assert not is_census_related("Write me a Python function to sort a list")

    def test_not_census_sports(self):
        assert not is_census_related("Who won the Super Bowl?")

    def test_not_census_stocks(self):
        assert not is_census_related("What is Apple's stock price?")


class TestSQLValidation:
    """Test SQL validation to prevent dangerous queries."""

    def test_valid_select(self):
        sql = "SELECT STATE_NAME, TOTAL_POPULATION FROM CENSUS_AGENT.PUBLIC.V_POPULATION"
        is_valid, _ = validate_sql(sql)
        assert is_valid

    def test_valid_aggregate(self):
        sql = "SELECT STATE_NAME, SUM(TOTAL_POPULATION) FROM CENSUS_AGENT.PUBLIC.V_STATE_SUMMARY GROUP BY STATE_NAME"
        is_valid, _ = validate_sql(sql)
        assert is_valid

    def test_reject_drop(self):
        sql = "DROP TABLE CENSUS_AGENT.PUBLIC.V_POPULATION"
        is_valid, error = validate_sql(sql)
        assert not is_valid
        assert "DROP" in error

    def test_reject_delete(self):
        sql = "DELETE FROM CENSUS_AGENT.PUBLIC.V_POPULATION WHERE STATE_NAME = 'CA'"
        is_valid, error = validate_sql(sql)
        assert not is_valid
        assert "DELETE" in error

    def test_reject_insert(self):
        sql = "INSERT INTO CENSUS_AGENT.PUBLIC.V_POPULATION VALUES ('XX', '99', 'Fake', '000', 0)"
        is_valid, error = validate_sql(sql)
        assert not is_valid
        assert "INSERT" in error

    def test_reject_wrong_table(self):
        sql = "SELECT * FROM SOME_OTHER_DATABASE.SCHEMA.SENSITIVE_TABLE"
        is_valid, error = validate_sql(sql)
        assert not is_valid
        assert "allowed Census views" in error

    def test_reject_update(self):
        sql = "UPDATE CENSUS_AGENT.PUBLIC.V_POPULATION SET TOTAL_POPULATION = 0"
        is_valid, error = validate_sql(sql)
        assert not is_valid


class TestResponseParsing:
    """Test LLM response parsing handles various formats."""

    def test_parse_valid_json(self):
        response = '{"action": "query", "sql": "SELECT 1", "explanation": "test"}'
        result = parse_llm_response(response)
        assert result["action"] == "query"
        assert result["sql"] == "SELECT 1"

    def test_parse_json_with_surrounding_text(self):
        response = 'Here is the result: {"action": "refuse", "message": "Not census"} done.'
        result = parse_llm_response(response)
        assert result["action"] == "refuse"

    def test_parse_invalid_json(self):
        response = "This is not JSON at all"
        result = parse_llm_response(response)
        assert result["action"] == "error"

    def test_parse_empty_response(self):
        response = ""
        result = parse_llm_response(response)
        assert result["action"] == "error"

    def test_parse_clarification(self):
        response = '{"action": "clarify", "message": "Which state?"}'
        result = parse_llm_response(response)
        assert result["action"] == "clarify"
        assert "Which state" in result["message"]


class TestStateResolution:
    """Test state name to abbreviation resolution."""

    def test_resolve_california(self):
        result = resolve_state_name("What is the population of California?")
        assert "CA" in result or "California" in result

    def test_resolve_new_york(self):
        result = resolve_state_name("income in new york")
        assert "NY" in result or "new york" in result

    def test_no_change_for_abbreviation(self):
        result = resolve_state_name("population in CA")
        assert "CA" in result


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
