from pathlib import Path
from pypdf import PdfReader
from app.core.parsing.base import Page,ParsingError

class PDF_parser:
    def parse(self,file_path:str|Path)->list[Page]:

        path = Path(file_path)

        if not path.exists():
            return FileNotFoundError(f"PDF file not found : {path}")

        if not path.is_file():
            raise ValueError(f"Expected a file , got : {path}")

        if path.suffix.lower() != ".pdf":
            raise ValueError(f"Expected a PDF file , got {path.suffix}")

        try:
            reader = PdfReader(str(path))
        except Exception as e:
            raise ValueError(f"Could not rerad PDF: {path}")from e

        pages : list[Page] = []

        for page_number,pdf_page in enumerate(reader.pages,start=1,):
            try:
                text = pdf_page.extract_text() or ""
            except Exception as e:
                raise ParsingError(
                    f"Could not extract text from"
                    f"page {page_number} of {path}"
                ) from e

            pages.append(
                Page(
                    number = page_number,
                    text = text,
                )
            )

        return pages