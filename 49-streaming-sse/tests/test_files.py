# Downloads: buffered vs streamed (same bytes!), FileResponse and Range requests
from fastapi.testclient import TestClient

from app.data import csv_chunks, csv_rows


def test_streamed_and_buffered_send_the_same_bytes(client: TestClient) -> None:
    buffered = client.get("/export/buffered?rows=5000")
    streamed = client.get("/export/streamed?rows=5000")
    assert buffered.content == streamed.content
    assert streamed.text.count("\n") == 5001                    # the header + 5000 rows
    assert streamed.headers["content-disposition"] == 'attachment; filename="lessons.csv"'
    assert "content-length" not in streamed.headers             # unknown in advance


def test_the_generator_makes_chunks_of_1000_lines() -> None:
    chunks = list(csv_chunks(5000))                              # header + 5000 rows
    assert [chunk.count("\n") for chunk in chunks] == [1000, 1000, 1000, 1000, 1000, 1]
    assert "".join(chunks) == "".join(csv_rows(5000))            # nothing lost


def test_file_response_and_range(client: TestClient) -> None:
    full = client.get("/files/report")
    assert full.headers["accept-ranges"] == "bytes"
    size = int(full.headers["content-length"])
    part = client.get("/files/report", headers={"Range": "bytes=0-49"})
    assert part.status_code == 206
    assert part.headers["content-range"] == f"bytes 0-49/{size}"
    assert part.content == full.content[:50]


def test_limits(client: TestClient) -> None:
    assert client.get("/export/streamed?rows=0").status_code == 422
    assert client.get("/export/streamed?rows=2000000").status_code == 422
