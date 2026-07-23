"""
Unit Test Suite for IntentClassifier & Intent-Aware Prompt System - ExpenseFlowAI
"""

import pytest
from app.ai.intent_classifier import IntentClassifier, IntentType
from app.ai.prompt_builder import PromptBuilder
from app.ai.prompt_templates import PromptSelector


def test_intent_greeting_classification():
    for msg in ["hi", "hello", "hey", "good morning", "greetings"]:
        intent, requires_data = IntentClassifier.classify(msg)
        assert intent == IntentType.GREETING
        assert requires_data is False


def test_intent_small_talk_classification():
    for msg in ["how are you?", "thanks!", "thank you so much", "cool", "awesome"]:
        intent, requires_data = IntentClassifier.classify(msg)
        assert intent == IntentType.SMALL_TALK
        assert requires_data is False


def test_intent_identity_classification():
    for msg in ["who are you?", "what is your name?", "tell me about yourself"]:
        intent, requires_data = IntentClassifier.classify(msg)
        assert intent == IntentType.IDENTITY
        assert requires_data is False


def test_intent_capabilities_classification():
    for msg in ["what can you do?", "how can you help me?", "help"]:
        intent, requires_data = IntentClassifier.classify(msg)
        assert intent == IntentType.CAPABILITIES
        assert requires_data is False


def test_intent_financial_query_classification():
    for msg in ["how much did I spend this month?", "what is my cashflow forecast?", "show my top category expenses"]:
        res = IntentClassifier.classify(msg)
        assert res.requires_financial_data is True


def test_intent_financial_advice_classification():
    for msg in ["can I buy a 1.5 lakh bike?", "how can I save more money?", "should I buy a new phone?"]:
        res = IntentClassifier.classify(msg)
        assert res.requires_financial_data is True


def test_intent_unknown_classification():
    res = IntentClassifier.classify("What is the weather outside?")
    assert res.intent == IntentType.GENERAL_QA
    assert res.requires_financial_data is False


def test_prompt_builder_omits_metrics_for_greetings():
    summary = {
        "total_balance": 15000.0,
        "period_income": 5000.0,
        "period_expense": 2000.0,
        "health_score": 85,
        "health_status": "Healthy"
    }

    # Greeting should omit metrics block
    prompt = PromptBuilder.build_prompt(financial_summary=summary, user_message="Hi")
    assert "VERIFIED FINANCIAL METRICS" not in prompt
    assert "USER MESSAGE:\nHi" in prompt

    # Financial Query should include metrics block
    fin_prompt = PromptBuilder.build_prompt(financial_summary=summary, user_message="How much did I spend?")
    assert "VERIFIED FINANCIAL METRICS" in fin_prompt
    assert "$15,000.00" in fin_prompt
