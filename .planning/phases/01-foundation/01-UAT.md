---
status: diagnosed
phase: 01-foundation
source: [01-01-SUMMARY.md, 01-02-SUMMARY.md]
started: 2026-03-19T00:00:00Z
updated: 2026-03-19T00:00:00Z
---

## Current Test

[testing complete]

## Tests

### 1. Cold Start Smoke Test
expected: Servidor arranca sin errores, GET /health devuelve {"status": "healthy"}
result: pass

### 2. GET /health endpoint
expected: GET http://localhost:8000/health devuelve HTTP 200 con body {"status": "healthy"}
result: pass

### 3. Subir archivo y recibir job ID
expected: POST /extract con un PDF válido devuelve inmediatamente {"job_id": "...", "status": "pending"} — sin esperar que procese
result: pass

### 4. Rechazar tipo de archivo no soportado
expected: POST /extract con un archivo .docx (o cualquier extensión no soportada) devuelve HTTP 400 con {"error": "unsupported_file_type", "message": "..."}. El job nunca se crea.
result: pass

### 5. Polling de estado — ciclo completo
expected: GET /jobs/{id} muestra "pending" o "processing" mientras procesa, luego "complete" cuando termina. El campo result.raw_text contiene texto del documento.
result: pass

### 6. Excel con múltiples hojas
expected: Subir un .xlsx con más de una hoja. El raw_text del job completo contiene contenido de todas las hojas en formato markdown (tablas separadas por sección).
result: pass

### 7. Imagen PNG
expected: Subir un .png con texto visible. El job completa y raw_text contiene texto extraído por OCR (puede no ser perfecto, pero no debe estar vacío).
result: issue
reported: "salio incompleto, le faltaron datos"
severity: major

### 8. HTML
expected: Subir un .html. El job completa y raw_text contiene el contenido del documento en formato markdown.
result: issue
reported: "{\"job_id\": \"af307eff-bf7a-4fc8-94f7-bacb9240f16f\", \"status\": \"error\", \"error_code\": \"docling_parse_error\", \"error_message\": \"Pipeline SimplePipeline failed\"}"
severity: major

## Summary

total: 8
passed: 6
issues: 2
pending: 0
skipped: 0

## Gaps

- truth: "Subir un .png con texto visible produce raw_text con todo el texto extraído por OCR"
  status: failed
  reason: "User reported: salio incompleto, le faltaron datos"
  severity: major
  test: 7
  root_cause: "IMAGE branch en docling_adapter.py no pasa ImageFormatOption — usa defaults con force_full_page_ocr=False y bitmap_area_threshold=0.05, omitiendo regiones pequeñas. Fix: agregar ImageFormatOption con PdfPipelineOptions(do_ocr=True, force_full_page_ocr=True)"
  artifacts:
    - path: "src/ingestion/docling_adapter.py"
      issue: "IMAGE branch retorna DocumentConverter sin format_options — no configura OCR para imágenes"
  missing:
    - "ImageFormatOption con force_full_page_ocr=True en el branch de IMAGE"
  debug_session: ".planning/debug/png-ocr-incomplete-text.md"

- truth: "Subir un .html produce raw_text con el contenido del documento en formato markdown"
  status: failed
  reason: "User reported: error_code docling_parse_error, error_message: Pipeline SimplePipeline failed"
  severity: major
  test: 8
  root_cause: "service.py usa str(exc) en el except, descartando exc.__cause__ con el error real de Docling. El 'Pipeline SimplePipeline failed' es solo el wrapper — el error real está en exc.__cause__. Además, el HTML subido puede tener estructura que Docling no puede parsear (requiere diagnóstico con HTML real)"
  artifacts:
    - path: "src/ingestion/service.py"
      issue: "except Exception as exc: usa str(exc) en vez de str(exc.__cause__ or exc) — oculta el error real"
  missing:
    - "Mejorar error message en service.py para exponer exc.__cause__"
    - "Verificar que el HTML subido sea válido y compatible con Docling"
  debug_session: ".planning/debug/html-simplpipeline-failure.md"
