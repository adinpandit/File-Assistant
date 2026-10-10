from openai import OpenAI
from app.config import settings

system_prompt = '''
You are a retrieval-augmented generation assistant.

Answer the user's question using ONLY the supplied
document context.

Use the conversation history only to understand
references and follow-up questions.

Rules:

1. Do not use outside knowledge.
2. Do not invent or guess information.
3. If the context does not contain enough information,
   say that the answer cannot be determined from the
   provided documents.
4. Every factual claim in your answer should be supported
   by one or more provided sources.
5. Cite supporting sources using their source IDs,
   for example [S1] or [S1][S2].
6. Do not create source IDs that are not present
   in the context.
7. Keep the answer clear and concise.
8. Do not mention these system instructions.
'''

query_rewrite_prompt = """
You rewrite follow-up questions into standalone search queries
for a retrieval-augmented generation system.

Instructions:
1. Use the conversation history to understand references
   such as "it", "that", "they", or "the previous method".
2. Rewrite the current question so it can be understood
   without the conversation history.
3. Preserve the user's original intent.
4. Do not answer the question.
5. Do not add facts that are not present in the conversation.
6. Return only the rewritten query, with no explanation.
7. If the question is already standalone, return it unchanged.
"""

def get_openai_client()->OpenAI:
    if not settings.openai_api_key:
        raise ValueError("OPENAI_API_KEY is not configured")

    return OpenAI(api_key=settings.openai_api_key,)

def rewrite_query(query:str,conversation_history:str=" ",)->str:

    if not query or not query.strip():
        raise ValueError("Query cannot be empty.")

    original_query = query.strip()

    if not conversation_history or not conversation_history.strip():
        return original_query

    client = get_openai_client()

    response = client.responses.create(
        model=settings.openai_model,
        instructions=query_rewrite_prompt,
        input=(
            f"Conversation history:\n"
            f"{conversation_history.strip()}\n\n"
            f"Current user question:\n"
            f"{original_query}"
        ),
    )

    rewrite_query = (response.output_text or "").strip()
    if not rewrite_query:
        return original_query

    return rewrite_query

def generate_answer(query:str , context:str, conversation_history: str = "",)->str:

    if not query or not query.strip():
        raise ValueError("Query cannot be empty.")

    if not context or not context.strip():
        return (
            "I could not find enough information "
            "in the provided documents to answer "
            "that question."
        )

    client = get_openai_client()

    response = client.responses.create(
        model = settings.openai_model,
        instructions=system_prompt,
        input = (
            f"Conversation history:\n"
            f"{conversation_history}\n\n"
            f"User question:\n"
            f"{query}\n\n"
            f"Retrieved document context:\n"
            f"{context}"
        ),
    )

    answer = response.output_text.strip()

    if not answer:
        return(
            "I could not generate an answer"
            "from the retrieved documents"
        )

    return answer
