import io
import uuid

from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse, StreamingResponse

from models import ExportRequest, ExtractRequest, ExtractResponse

import cardgen
import extractor
import llm_extractor
import pdf_reader
import quality
import segmenter
import exporter

app = FastAPI(title="PDF → Anki")

PDF_STORAGE: dict[str, bytes] = {}


@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    payload = await file.read()
    pdf_id = uuid.uuid4().hex[:8]
    PDF_STORAGE[pdf_id] = payload
    return {"pdf_id": pdf_id, "filename": file.filename, "size": len(payload)}


@app.post("/extract", response_model=ExtractResponse)
async def extract_cards(request: ExtractRequest, pdf_id: str):
    if pdf_id not in PDF_STORAGE:
        return JSONResponse({"error": "pdf_id not found"}, status_code=404)

    pages = pdf_reader.read_pdf(PDF_STORAGE[pdf_id])
    sections = segmenter.split_into_sections(pages)

    cards: list[dict[str, object]] = []
    llm_report: dict[str, object] | None = None

    if request.use_llm:
        cards, llm_metrics = await llm_extractor.generate_cards(
            sections, request.language or "en", request.card_types, request.max_cards
        )
        llm_report = {
            "used": llm_metrics.get("used", False),
            "generated": int(llm_metrics.get("generated", 0)),
            "enriched": int(llm_metrics.get("generated", 0)),
            "model": llm_metrics.get("model"),
            "duration_ms": int(llm_metrics.get("duration_ms", 0)),
            "chunks": int(llm_metrics.get("chunks", 0)),
            "error": llm_metrics.get("error"),
            "mode": "extraction",
        }

    if not cards:
        facts = extractor.extract_facts(sections, request.language)
        cards = cardgen.generate_cards(
            facts, request.card_types, request.max_cards, request.language
        )

    cards = quality.apply_checks(cards)
    metrics = {"pages": float(len(pages)), "candidates": float(len(cards))}

    return ExtractResponse(cards=cards, metrics=metrics, llm=llm_report)


@app.post("/export.apkg")
async def export_apkg(body: ExportRequest):
    package = exporter.build_apkg(body.deck_name, body.cards)
    return StreamingResponse(
        io.BytesIO(package),
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f'attachment; filename="{body.deck_name}.apkg"'
        },
    )
