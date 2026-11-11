# Big downloads: everything at once vs a stream vs a file from disk
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Query, Request
from fastapi.responses import FileResponse, PlainTextResponse, StreamingResponse

from app.data import csv_chunks, csv_rows

router = APIRouter(tags=["Files"])

Rows = Annotated[int, Query(ge=1, le=1_000_000)]
ATTACHMENT = {"Content-Disposition": 'attachment; filename="lessons.csv"'}


@router.get("/export/buffered", response_class=PlainTextResponse)
def export_buffered(rows: Rows = 200_000) -> PlainTextResponse:
    """BAD for big data: build the WHOLE file in memory, then send it"""
    body = "".join(csv_rows(rows))
    return PlainTextResponse(body, media_type="text/csv", headers=ATTACHMENT)


@router.get("/export/streamed")
def export_streamed(rows: Rows = 200_000) -> StreamingResponse:
    """GOOD: send the file piece by piece - 1,000 lines per chunk"""
    return StreamingResponse(csv_chunks(rows), media_type="text/csv", headers=ATTACHMENT)


@router.get("/export/line-by-line")
def export_line_by_line(rows: Rows = 200_000) -> StreamingResponse:
    """works - but one tiny chunk per line: a send() for every 25 bytes"""
    return StreamingResponse(csv_rows(rows), media_type="text/csv", headers=ATTACHMENT)


@router.get("/files/report")
def download_report(request: Request) -> FileResponse:
    """a file that already exists: FileResponse reads it in chunks (and supports Range)"""
    path: Path = request.app.state.report_path
    return FileResponse(path, media_type="text/csv", filename="report.csv")
