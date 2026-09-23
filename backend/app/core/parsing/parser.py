from pathlib import Path
from app.core.parsing.base import Page
from app.core.parsing.pdf_parser import PDF_parser
from app.core.parsing.text_parser import TEXT_parser

class Document_Parser:

    def __init__(self):
        self.Pdf_Parser = PDF_parser()
        self.Text_Parser = TEXT_parser()

    def parse(self,file_path:str|Path)->list[Page]:
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(
                f"Document not found: {path}"
            )

        extension = path.suffix.lower()

        if extension == ".pdf":
            return self.Pdf_Parser.parse(path)

        if extension in {".txt", ".md"}:
            return self.Text_Parser.parse(path)

        raise ValueError(
            f"Unsupported document type: {extension}"
        )

_document_parser = Document_Parser()


def parse_document(file_path: str | Path,) -> list[Page]:
    return _document_parser.parse(file_path)