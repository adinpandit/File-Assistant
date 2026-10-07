
import os
from uuid import uuid4

import pytest

from app.config import settings
from app.core.db import (
    get_connection,
    initialize_database,
)
from app.services.conv_store import ConversationStore
from app.services.user_store import UserStore


TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL"
)


@pytest.fixture
def database():

    if not TEST_DATABASE_URL:
        pytest.skip(
            "TEST_DATABASE_URL is not configured"
        )

    original_url = settings.database_url

    settings.database_url = TEST_DATABASE_URL

    initialize_database()

    yield

    settings.database_url = original_url


@pytest.fixture
def user(database):

    user_store = UserStore()

    email = (
        f"history-{uuid4()}@test.com"
    )

    return user_store.create_user(
        email=email,
        password="password123",
    )


def test_create_conversation(
    database,
    user,
):

    store = ConversationStore()

    conversation = (
        store.create_conversation(
            user_id=user.user_id,
            title="Test Conversation",
        )
    )

    assert conversation is not None

    assert (
        conversation.user_id
        == user.user_id
    )

    assert (
        conversation.title
        == "Test Conversation"
    )


def test_list_conversations(
    database,
    user,
):

    store = ConversationStore()

    store.create_conversation(
        user_id=user.user_id,
        title="Conversation One",
    )

    store.create_conversation(
        user_id=user.user_id,
        title="Conversation Two",
    )

    conversations = (
        store.list_conversations(
            user_id=user.user_id
        )
    )

    assert len(conversations) == 2


def test_add_and_list_messages(
    database,
    user,
):

    store = ConversationStore()

    conversation = (
        store.create_conversation(
            user_id=user.user_id,
            title="Chat",
        )
    )

    user_message = (
        store.add_message(
            conversation_id=(
                conversation.conversation_id
            ),
            user_id=user.user_id,
            role="user",
            content="What is RAG?",
        )
    )

    assistant_message = (
        store.add_message(
            conversation_id=(
                conversation.conversation_id
            ),
            user_id=user.user_id,
            role="assistant",
            content=(
                "RAG combines retrieval "
                "with generation."
            ),
        )
    )

    assert user_message is not None
    assert assistant_message is not None

    messages = (
        store.list_messages(
            conversation_id=(
                conversation.conversation_id
            ),
            user_id=user.user_id,
        )
    )

    assert len(messages) == 2

    assert (
        messages[0].role
        == "user"
    )

    assert (
        messages[1].role
        == "assistant"
    )


def test_get_recent_messages(
    database,
    user,
):

    store = ConversationStore()

    conversation = (
        store.create_conversation(
            user_id=user.user_id,
            title="Memory Test",
        )
    )

    store.add_message(
        conversation_id=(
            conversation.conversation_id
        ),
        user_id=user.user_id,
        role="user",
        content="What is RAG?",
    )

    store.add_message(
        conversation_id=(
            conversation.conversation_id
        ),
        user_id=user.user_id,
        role="assistant",
        content=(
            "RAG combines retrieval "
            "with generation."
        ),
    )

    store.add_message(
        conversation_id=(
            conversation.conversation_id
        ),
        user_id=user.user_id,
        role="user",
        content="Why is retrieval useful?",
    )

    messages = (
        store.get_recent_messages(
            conversation_id=(
                conversation.conversation_id
            ),
            user_id=user.user_id,
            limit=10,
        )
    )

    assert len(messages) == 3

    assert (
        messages[0].role
        == "user"
    )

    assert (
        messages[0].content
        == "What is RAG?"
    )

    assert (
        messages[1].role
        == "assistant"
    )

    assert (
        messages[1].content
        == (
            "RAG combines retrieval "
            "with generation."
        )
    )

    assert (
        messages[2].role
        == "user"
    )

    assert (
        messages[2].content
        == "Why is retrieval useful?"
    )


def test_get_recent_messages_respects_limit(
    database,
    user,
):

    store = ConversationStore()

    conversation = (
        store.create_conversation(
            user_id=user.user_id,
            title="Limit Test",
        )
    )

    store.add_message(
        conversation_id=(
            conversation.conversation_id
        ),
        user_id=user.user_id,
        role="user",
        content="Message one",
    )

    store.add_message(
        conversation_id=(
            conversation.conversation_id
        ),
        user_id=user.user_id,
        role="assistant",
        content="Message two",
    )

    store.add_message(
        conversation_id=(
            conversation.conversation_id
        ),
        user_id=user.user_id,
        role="user",
        content="Message three",
    )

    messages = (
        store.get_recent_messages(
            conversation_id=(
                conversation.conversation_id
            ),
            user_id=user.user_id,
            limit=2,
        )
    )

    assert len(messages) == 2

    assert (
        messages[0].content
        == "Message two"
    )

    assert (
        messages[1].content
        == "Message three"
    )


def test_user_cannot_access_other_users_conversation(
    database,
):

    user_store = UserStore()

    conversation_store = ConversationStore()

    user_a = user_store.create_user(
        email=f"a-{uuid4()}@test.com",
        password="password123",
    )

    user_b = user_store.create_user(
        email=f"b-{uuid4()}@test.com",
        password="password123",
    )

    conversation = (
        conversation_store.create_conversation(
            user_id=user_a.user_id,
            title="Private Conversation",
        )
    )

    result = (
        conversation_store.get_conversation(
            conversation_id=(
                conversation.conversation_id
            ),
            user_id=user_b.user_id,
        )
    )

    assert result is None


def test_delete_conversation(
    database,
    user,
):

    store = ConversationStore()

    conversation = (
        store.create_conversation(
            user_id=user.user_id,
            title="Delete Me",
        )
    )

    deleted = (
        store.delete_conversation(
            conversation_id=(
                conversation.conversation_id
            ),
            user_id=user.user_id,
        )
    )

    assert deleted is True

    result = (
        store.get_conversation(
            conversation_id=(
                conversation.conversation_id
            ),
            user_id=user.user_id,
        )
    )

    assert result is None
