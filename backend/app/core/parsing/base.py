from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

@dataclass
class Page:
    """
    Represents one logical page of extracted document text.

    For PDFs:
        number = actual PDF page number

    For TXT/Markdown:
        number = 1
        text = entire document
    """
    number:int
    text:str

class ParsingError(Exception):
    """Raised when a file can't be turned into text."""

class Parser(Protocol):
    def parse(self,path:Path)->list[Page]: ...