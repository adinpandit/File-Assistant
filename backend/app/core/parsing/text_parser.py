from pathlib import Path
from app.core.parsing.base import Page

supported_extensions = {
    ".txt",
    ".md"
}

class TEXT_parser:
    def parse(self,path:Path)->list[Page]:
        path = Path(path)

        if not path.exists():
            raise FileNotFoundError(f"Text file not found: {path}")

        if not path.is_file():
            raise ValueError(f"Expected a text file , got : {path}")

        extension  = path.suffix.lower()

        if extension not in supported_extensions:
            raise ValueError(f"Unsupported text file type : {extension}")

        try:
            text = path.read_text(
                encoding = "utf-8" #UTF-8 is the standard encoding for most modern text files.
            )
        except UnicodeDecodeError:
            text = path.read_text(
                encoding = "utf-8-sig" #utf-8-sig is UTF-8 that can handle a BOM (Byte Order Mark) at the beginning of a file.
            )

        return[
            Page(
                number = 1,
                text = text,
            )
        ]