# checkmyexams
Built an AI exam platform using RAG, exam cloning, and knowledge tracing to generate personalized practice and feedback from raw PDFs and notes. Designed FastAPI backend, document parsing, and validation pipelines.
## Features

- **RAG-based semantic search** for retrieving relevant exam content.
- **Exam Cloner** that generates full-length practice exams matching style, difficulty, and topic patterns.
- **Knowledge Tracing model** to estimate student mastery and adapt question difficulty.
- **Document ingestion pipeline** supporting PDFs, DOCX, images.
- **LLM output guardrails** to reduce hallucinations and ensure correctness.
- **FastAPI backend** with modular, scalable architecture.
- Real-time question generation and feedback APIs.

Pipeline: PDF → Parser → Chunker → Embeddings → Pinecone → Context Builder → LLM (Exam Cloner / Feedback Engine) → Output Validator → API Response
