from pathlib import Path

from app.core.parsing import parse_document
from app.core.parsing.pdf_parser import PDF_parser
from app.core.parsing.text_parser import TEXT_parser


FIXTURES_DIR = Path(__file__).parent / "fixtures"


def test_parse_txt():
    file_path = FIXTURES_DIR / "test.txt"

    parser = TEXT_parser()
    pages = parser.parse(file_path)

    assert len(pages) == 1
    assert pages[0].number == 1
    assert pages[0].text.strip() != ""
    assert "RAG Assistant Test" in pages[0].text


def test_parse_markdown():
    file_path = FIXTURES_DIR / "test.md"

    parser = TEXT_parser()
    pages = parser.parse(file_path)

    assert len(pages) == 1
    assert pages[0].number == 1
    assert pages[0].text.strip() != ""
    assert "# RAG Assistant Test" in pages[0].text


def test_parse_pdf():
    file_path = FIXTURES_DIR / "test.pdf"

    parser = PDF_parser()
    pages = parser.parse(file_path)

    assert len(pages) > 0

    for page in pages:
        assert page.number > 0
        assert isinstance(page.text, str)


def test_parser_routing_txt():
    file_path = FIXTURES_DIR / "test.txt"

    pages = parse_document(file_path)

    assert len(pages) == 1
    assert pages[0].number == 1


def test_parser_routing_markdown():
    file_path = FIXTURES_DIR / "test.md"

    pages = parse_document(file_path)

    assert len(pages) == 1
    assert pages[0].number == 1


def test_parser_routing_pdf():
    file_path = FIXTURES_DIR / "test.pdf"

    pages = parse_document(file_path)

    assert len(pages) > 0


def test_unsupported_file():
    file_path = FIXTURES_DIR / "test.docx"

    file_path.write_text(
        "This should not be parsed.",
        encoding="utf-8",
    )

    try:
        parse_document(file_path)
        assert False, "Expected ValueError"
    except ValueError as exc:
        assert "Unsupported document type" in str(exc)