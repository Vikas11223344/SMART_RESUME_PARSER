# SMART_RESUME_PARSER
# Smart Resume Parser

Objective
- Extract structured information (contact, skills, education, experience, summary) from resumes in PDF or DOCX format.
- Provide a Streamlit UI to upload resumes, view parsed results, and export JSON/CSV.

Tech stack
- Python 3.9+
- spaCy
- PyMuPDF (fitz)
- python-docx
- pandas
- Streamlit

Features
- Text extraction for PDF and DOCX files.
- Cleaning and preprocessing of extracted text.
- Section detection using headings and heuristics.
- Skills extraction using spaCy PhraseMatcher + fallback regex/keylist.
- Education and Experience extraction using regex and section parsing.
- Export results to JSON and CSV from the UI.

Repository layout (suggested)
- streamlit_app.py         # Streamlit UI
- parser.py                # Core parsing logic
- utils.py                 # Helpers (exporters, cleaners)
- requirements.txt
- tests/
  - sample1.txt
  - sample2.txt
  - sample3.txt
  - sample4.txt
  - sample5.txt
- outputs/
  - sample1.json
  - sample1.csv

Setup (local)
1. Create and activate a venv:
   - python -m venv venv
   - source venv/bin/activate   (or venv\Scripts\activate on Windows)

2. Install requirements:
   - pip install -r requirements.txt

3. Download spaCy model:
   - python -m spacy download en_core_web_sm
   (or en_core_web_md for better phrase matching if you prefer)

Run the Streamlit app
- streamlit run streamlit_app.py

What I included
- A production-ready starter parser (parser.py) with:
  - PDF/DOCX extraction
  - Basic cleaning and section splitting
  - Contact, skills, education, experience extraction
- Streamlit UI (streamlit_app.py)
- Utility functions to export JSON and CSV (utils.py)
- 5 sample plain-text resumes in tests/ to test parser locally
- Example parsed outputs in outputs/

Notes & next steps
- Improve entity extraction by training/adding more domain rules or using a custom spaCy model.
- Add fuzzy matching for skills (e.g., using RapidFuzz) and a larger curated skills ontology.
- Support bulk uploads and background tasks for large batches.
- Add unit tests around parser functions.
