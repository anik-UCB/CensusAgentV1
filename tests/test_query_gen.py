# Tests for SQL query generation patterns
# Co-authored with CoCo

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent import validate_sql, build_messages, SYSTEM_PROMPT


class TestQueryPatterns:
    """Test that generated SQL patterns are structurally valid."""

    def test_state_population_query(self):
        sql = """
        SELECT STATE_NAME, TOTAL_POPULATION 
        FROM CENSUS_AGENT.PUBLIC.V_STATE_SUMMARY 
        WHERE STATE_NAME = 'CA'
        """
        is_valid, _ = validate_sql(sql)
        assert is_valid

    def test_top_states_by_income(self):
        sql = """
        SELECT STATE_NAME, AVG_MEDIAN_HOUSEHOLD_INCOME
        FROM CENSUS_AGENT.PUBLIC.V_INCOME
        GROUP BY STATE_NAME
        ORDER BY AVG_MEDIAN_HOUSEHOLD_INCOME DESC
        LIMIT 10
        """
        is_valid, _ = validate_sql(sql)
        assert is_valid

    def test_county_comparison(self):
        sql = """
        SELECT COUNTY, TOTAL_POPULATION, UNEMPLOYMENT_RATE
        FROM CENSUS_AGENT.PUBLIC.V_EMPLOYMENT
        WHERE STATE_NAME = 'TX'
        ORDER BY UNEMPLOYMENT_RATE DESC
        LIMIT 5
        """
        is_valid, _ = validate_sql(sql)
        assert is_valid

    def test_join_across_views(self):
        sql = """
        SELECT p.STATE_NAME, p.TOTAL_POPULATION, e.UNEMPLOYMENT_RATE
        FROM CENSUS_AGENT.PUBLIC.V_POPULATION p
        JOIN CENSUS_AGENT.PUBLIC.V_EMPLOYMENT e 
            ON p.STATE_NAME = e.STATE_NAME AND p.COUNTY_FIPS = e.COUNTY_FIPS
        WHERE p.STATE_NAME = 'NY'
        LIMIT 10
        """
        is_valid, _ = validate_sql(sql)
        assert is_valid

    def test_percentage_calculation(self):
        sql = """
        SELECT STATE_NAME, 
               ROUND(BACHELORS_DEGREE * 100.0 / NULLIF(TOTAL_POP_25_PLUS, 0), 1) AS BACHELORS_PCT
        FROM CENSUS_AGENT.PUBLIC.V_EDUCATION
        WHERE STATE_NAME = 'MA'
        LIMIT 10
        """
        is_valid, _ = validate_sql(sql)
        assert is_valid


class TestMessageBuilding:
    """Test conversation message building."""

    def test_empty_history(self):
        messages = build_messages([], "Hello")
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
        assert messages[1]["content"] == "Hello"

    def test_with_history(self):
        history = [
            {"role": "user", "content": "What is CA population?"},
            {"role": "assistant", "content": "39 million"}
        ]
        messages = build_messages(history, "And Texas?")
        assert len(messages) == 4
        assert messages[-1]["content"] == "And Texas?"

    def test_history_truncation(self):
        """History should be limited to last 10 messages."""
        history = [{"role": "user", "content": f"msg {i}"} for i in range(20)]
        messages = build_messages(history, "new question")
        # system + 10 history + 1 new = 12
        assert len(messages) == 12

    def test_system_prompt_contains_schema(self):
        messages = build_messages([], "test")
        assert "V_POPULATION" in messages[0]["content"]
        assert "V_INCOME" in messages[0]["content"]
        assert "V_HOUSING" in messages[0]["content"]
        assert "V_EDUCATION" in messages[0]["content"]
        assert "V_EMPLOYMENT" in messages[0]["content"]


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
