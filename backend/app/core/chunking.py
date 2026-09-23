from dataclasses import dataclass
from uuid import uuid4
from app.core.parsing.base import Page

chunk_size = 400
chunck_overlap = 60

@dataclass
class chunk:
    chunk_id:str
    document_id:str
    user_id:str|None
    chunk_index:int
    page_number:int
    text:str

def validate_chunck_config(chunk_size:int , chunk_overlap:int,)->None:

    if chunk_size <= 0:
        raise ValueError(f"chunk_size must be greater than 0")

    if chunk_overlap < 0:
        raise ValueError(f"chunk_overlap cannot be less than 0")

    if chunk_overlap >= chunk_size:
        raise ValueError(f"chunk_overlap must be smaller than chunk_size")

def split_text(text:str , chunk_size:int , chunk_overlap:int)->list[str]:

    text = text.strip()

    if not text:
        return []

    chunks:list[str] = []

    start = 0
    text_length = len(text)

    step = chunk_size - chunk_overlap

    while start < text_length:
        end = min(
            start + chunk_size,
            text_length,
        )

        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end >= text_length:
            break

        start += step

    return chunks

def chunk_pages(pages:list[Page] , document_id:str , user_id:str|None=None , chunk_size:int = chunk_size , chunk_overlap:int = chunck_overlap)->list[chunk]:

    validate_chunck_config(chunk_size,chunk_overlap,)

    chunks:list[chunk]=[]

    chunk_index = 0

    for page in pages:
        page_chunks = split_text(text=page.text,chunk_size=chunk_size,chunk_overlap=chunk_overlap,)

        for text in page_chunks:
            chunks.append(
                chunk(
                    chunk_id=str(uuid4()),
                    document_id=document_id,
                    user_id=user_id,
                    chunk_index=chunk_index,
                    page_number=page.number,
                    text=text,
                )
            )

            chunk_index += 1

    return chunks