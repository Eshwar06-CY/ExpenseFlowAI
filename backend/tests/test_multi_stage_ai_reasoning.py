"""
Comprehensive Multi-Stage AI Reasoning Engine Unit Test Suite - ExpenseFlowAI
"""

import pytest
from app.ai.intent_classifier import IntentClassifier, IntentType
from app.ai.entity_extractor import EntityExtractor
from app.ai.task_planner import TaskPlanner
from app.ai.decision_engine import DecisionEngine
from app.ai.conversation_manager import ConversationManager
from app.ai.prompt_builder import PromptBuilder
from app.ai.response_validator import ResponseValidator


def test_intent_classification_granular():
    # Joke
    res_joke = IntentClassifier.classify("Tell me a joke")
    assert res_joke.intent == IntentType.JOKE
    assert res_joke.requires_financial_data is False
    assert res_joke.confidence >= 0.90

    # Purchase decision
    res_buy = IntentClassifier.classify("Can I buy a bike?")
    assert res_buy.intent == IntentType.PURCHASE_DECISION
    assert res_buy.requires_financial_data is True
    assert res_buy.confidence >= 0.90

    # Goal planning
    res_plan = IntentClassifier.classify("Create a financial plan for buying a 2 lakh bike in 2 years")
    assert res_plan.intent == IntentType.GOAL_PLANNING
    assert res_plan.requires_financial_data is True


def test_entity_extraction():
    msg = "I want to buy a bike worth 2 lakhs in 2 years."
    entities = EntityExtractor.extract(msg)

    assert entities.goal_name == "Buy Bike"
    assert entities.target_amount == 200000.0
    assert entities.timeline_months == 24
    assert entities.category == "Vehicle"


def test_missing_info_detection_triggers_clarification():
    # User asks goal planning without providing income, expenses, or savings
    msg = "Create a financial plan to buy a bike worth ₹2 lakh."
    intent_res = IntentClassifier.classify(msg)
    entities = EntityExtractor.extract(msg)

    task_plan = TaskPlanner.plan_task(intent_res, entities, finance_summary={})
    decision = DecisionEngine.evaluate(intent_res, entities, task_plan)

    assert task_plan.is_complete is False
    assert "purchase_timeline" in task_plan.missing_fields
    assert decision.should_clarify is True
    assert "Before I generate a detailed affordability analysis" in task_plan.clarification_prompt
    assert "?" in task_plan.clarification_prompt


def test_decision_engine_skips_db_for_greetings_and_jokes():
    for msg in ["Hi", "Thanks", "Who are you?", "Tell me a joke"]:
        intent_res = IntentClassifier.classify(msg)
        entities = EntityExtractor.extract(msg)
        task_plan = TaskPlanner.plan_task(intent_res, entities)
        decision = DecisionEngine.evaluate(intent_res, entities, task_plan)

        assert decision.use_finance_engine is False
        assert decision.should_clarify is False


def test_multi_turn_entity_accumulation():
    turn1 = "I want to buy a bike."
    turn2 = "It costs 2 lakh."
    turn3 = "In 2 years."

    history = [
        {"role": "user", "content": turn1},
        {"role": "assistant", "content": "What is the price?"},
        {"role": "user", "content": turn2},
        {"role": "assistant", "content": "What is the timeline?"}
    ]

    entities = ConversationManager.accumulate_entities(turn3, chat_history=history)

    assert entities.goal_name == "Buy Bike"
    assert entities.target_amount == 200000.0
    assert entities.timeline_months == 24


def test_response_validator_sanitizes_metric_hallucinations():
    intent_res = IntentClassifier.classify("Hi")
    entities = EntityExtractor.extract("Hi")
    task_plan = TaskPlanner.plan_task(intent_res, entities)
    decision = DecisionEngine.evaluate(intent_res, entities, task_plan)

    bad_response = "Hi there! 👋\nComposite Score: 45/100\nHow can I help you today?"
    val = ResponseValidator.validate_and_sanitize(bad_response, decision, "Hi")

    assert val.is_valid is True
    assert "Composite Score:" not in val.sanitized_text
    assert "Hi there! 👋" in val.sanitized_text
