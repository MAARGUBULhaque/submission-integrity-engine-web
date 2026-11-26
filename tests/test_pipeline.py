from pathlib import Path
import pytest

from src.extractors import extract
from src.chunking import chunk, boilerplate
from src.embeddings import Encoder, VectorIndex
from src.ai_detector import estimate
from run_integrity_check import coverage, run

DATA = Path(__file__).resolve().parents[1] / "sample_submissions"


def test_extractors():
    assert extract(DATA / "01_health.pdf")[0][1]["page"] == 1
    assert extract(DATA / "06_retail.pdf")[0][1]["page"] == 1

    with pytest.raises(ValueError):
        extract(DATA / "05_empty.pdf")


def test_overlap_and_coverage():
    cs = chunk(
        [(" ".join(["word"] * 250), {"page": 1})],
        size=100,
        overlap=20
    )

    assert coverage(cs, cs) == 100
    assert coverage(cs, cs[:2]) == 72


def test_boilerplate():
    docs = {
        str(i): [
            ("Shared prompt. Unique " + str(i), {"page": 1})
        ]
        for i in range(5)
    }

    assert "shared prompt." in boilerplate(docs)

    assert "Shared prompt" not in chunk(
        docs["0"],
        boilerplate(docs)
    )[0]["text"]


def test_self_exclusion():
    encoder = Encoder("lexical")

    c = chunk([("unique matching text", {})])[0]

    index = VectorIndex(
        [("a", c), ("b", c)],
        encoder
    )

    vector = encoder.encode([c["text"]])[0]

    assert [
        name for name, _, _ in index.search(vector, "a")
    ] == ["b"]


def test_ai_signal():
    assert estimate("One sentence.") is None

    assert estimate(
        "One two. Three four. Five six."
    ) == 100


def test_unsupported_format(tmp_path):
    path = tmp_path / "unsupported.docx"
    path.write_bytes(b"unsupported content")

    with pytest.raises(ValueError, match="Unsupported"):
        extract(path)


def test_integration(tmp_path):
    result = run(
        DATA,
        tmp_path,
        DATA.parent / "reference_data",
        backend="lexical"
    )

    assert len(result) == 10

    by_name = {
        report["document_id"]: report
        for report in result
    }

    assert (
        by_name["01_health.pdf"]["scores"]
        ["peer_similarity_percentage"] == 100
    )

    assert (
        by_name["09_external.pdf"]["scores"]
        ["external_similarity_percentage"] == 100
    )

    assert by_name["05_empty.pdf"]["status"] == "skipped"

    assert (tmp_path / "summary_matrix.csv").exists()


