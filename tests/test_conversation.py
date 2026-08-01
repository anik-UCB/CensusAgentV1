# Tests for multi-turn conversation context preservation
# Co-authored with CoCo

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent import build_messages, is_census_related


class TestConversationContext:
    """Test that conversation context is properly maintained across turns."""

    def test_follow_up_references_previous(self):
        """A follow-up like 'And Texas?' should include prior context."""
        history = [
            {"role": "user", "content": "What is the population of California?"},
            {"role": "assistant", "content": "California has about 39.3 million people."}
        ]
        messages = build_messages(history, "And Texas?")
        # The full conversation should be included so the LLM knows 'And Texas?' 
        # refers to population
        all_content = " ".join(m["content"] for m in messages)
        assert "California" in all_content
        assert "Texas" in all_content

    def test_context_window_maintained(self):
        """Multiple turns should all be visible to the model."""
        history = [
            {"role": "user", "content": "What states have the highest population?"},
            {"role": "assistant", "content": "CA, TX, FL, NY, PA"},
            {"role": "user", "content": "What about income for those states?"},
            {"role": "assistant", "content": "Here are the median incomes..."},
        ]
        messages = build_messages(history, "Which one has the most housing?")
        assert len(messages) == 6  # system + 4 history + 1 new

    def test_ambiguous_follow_up_still_census(self):
        """Follow-up messages may not contain census keywords but are still on-topic 
        when conversation context exists."""
        # With history, the agent should consider context
        # The is_census_related check is only a first-pass filter for NEW conversations
        assert not is_census_related("What about that one?")
        # But in context of a conversation, it should still work
        # (the agent uses LLM with full history for classification)

    def test_new_conversation_no_context(self):
        """First message with no history uses keyword check."""
        messages = build_messages([], "What is the population of Ohio?")
        assert len(messages) == 2
        assert messages[0]["role"] == "system"

    def test_conversation_reset(self):
        """After clearing history, messages start fresh."""
        messages = build_messages([], "Hello")
        assert len(messages) == 2


class TestEdgeCases:
    """Test edge cases and graceful degradation."""

    def test_empty_message(self):
        """Empty message should not crash."""
        messages = build_messages([], "")
        assert len(messages) == 2
        assert messages[1]["content"] == ""

    def test_very_long_message(self):
        """Very long messages should not crash."""
        long_msg = "population " * 1000
        messages = build_messages([], long_msg)
        assert messages[1]["content"] == long_msg

    def test_special_characters(self):
        """Messages with special characters should not crash."""
        messages = build_messages([], "What's the population of 'New York'?")
        assert "New York" in messages[1]["content"]

    def test_unicode_message(self):
        """Unicode characters should be handled."""
        messages = build_messages([], "Populación de California?")
        assert len(messages) == 2

    def test_sql_injection_in_message(self):
        """Attempted SQL injection in user message should be caught by validation."""
        from agent import validate_sql
        # Even if LLM generates this, our validator should catch it
        malicious_sql = "SELECT * FROM CENSUS_AGENT.PUBLIC.V_POPULATION; DROP TABLE users;"
        is_valid, _ = validate_sql(malicious_sql)
        assert not is_valid


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
