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

def get_openai_client()->OpenAI:
    if not settings.openai_api_key:
        raise ValueError("OPENAI_API_KEY is not configured")

    return OpenAI(api_key=settings.openai_api_key,)

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
