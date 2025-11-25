"""
Streamlit UI for the Smart Resume Parser.
Run: streamlit run streamlit_app.py
"""

try:
    import streamlit as st
except ModuleNotFoundError:
    import sys
    err = (
        "Error: Streamlit is not installed in the Python environment you're using.\n"
        "To fix: install the project requirements into the project's virtualenv and run Streamlit with that Python.\n\n"
        "If you have the project's virtualenv at `.venv`, run (PowerShell):\n"
        "  .\\.venv\\Scripts\\python -m pip install -r requirements.txt\n"
        "  .\\.venv\\Scripts\\python -m streamlit run streamlit_app.py\n\n"
        "Or activate the virtualenv and run: (PowerShell)\n"
        "  .\\.venv\\Scripts\\Activate.ps1; streamlit run streamlit_app.py\n\n"
        "If you intended to run the app directly with `python streamlit_app.py`, please instead use `streamlit run` or ensure Streamlit is installed in that Python environment.\n"
    )
    sys.stderr.write(err + "\n")
    sys.exit(1)

import tempfile
import os
import json
from parser import (
    parse_resume_file,
    parse_resume_from_text,
    extract_text_from_pdf,
    extract_text_from_docx,
)
from utils import to_json, parsed_to_dataframe, df_to_csv_bytes

st.set_page_config(page_title="Smart Resume Parser", layout="wide")

st.title("Smart Resume Parser")
st.write("Upload a PDF / DOCX / TXT resume. We'll parse and extract structured fields.")

uploaded_file = st.file_uploader("Upload resume file", type=["pdf", "docx", "txt"])
sample_text = st.text_area("Or paste resume text here (optional)", height=150)

if st.button("Parse"):
    if uploaded_file is None and not sample_text.strip():
        st.warning("Please upload a file or paste resume text.")
    else:
        # handle file upload
        raw_text = ""
        if uploaded_file is not None:
            suffix = os.path.splitext(uploaded_file.name)[1].lower()
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(uploaded_file.read())
                tmp_path = tmp.name

            # Try to extract raw text explicitly so we can show diagnostics in the UI.
            try:
                if suffix == ".pdf":
                    raw_text = extract_text_from_pdf(tmp_path)
                elif suffix == ".docx":
                    raw_text = extract_text_from_docx(tmp_path)
                elif suffix == ".txt":
                    with open(tmp_path, "r", encoding="utf-8", errors="replace") as f:
                        raw_text = f.read()
                else:
                    # fallback: try generic parse which will pick an extractor
                    parsed = parse_resume_file(tmp_path)
            except Exception as e:
                raw_text = ""  # leave empty on extraction failure

            # If we have raw_text, parse from it (safer than re-opening file)
            if raw_text:
                parsed = parse_resume_from_text(raw_text)
            else:
                # fallback to file-based parse
                parsed = parse_resume_file(tmp_path)

            try:
                os.unlink(tmp_path)
            except Exception:
                pass
        else:
            parsed = parse_resume_from_text(sample_text)

        # Show raw extracted text preview for debugging/troubleshooting
        st.subheader("Raw text preview (first 1200 chars)")
        st.text_area("Raw extracted text", value=(raw_text or ""), height=200)

        # If parsed results look empty, give helpful advice
        if not parsed.get("skills") and not parsed.get("education") and not parsed.get("experience") and not parsed.get("contact"):
            st.warning(
                "Parsing returned no structured data. The resume may be a scanned PDF (image content) or use non-standard formatting.\n"
                "Try uploading a DOCX or a plain text version of the resume, or copy-paste the resume text into the text area."
            )

        # --- Diagnostics: show quick counts and section previews ---
        st.subheader("Diagnostics")
        contact = parsed.get("contact", {})
        skills = parsed.get("skills", []) or []
        education = parsed.get("education", []) or []
        experience = parsed.get("experience", []) or []

        st.write(
            f"Contact: emails={len(contact.get('emails',[]))}, phones={len(contact.get('phones',[]))}, linkedin={len(contact.get('linkedin',[]))}"
        )
        st.write(f"Skills: {len(skills)}   Education entries: {len(education)}   Experience entries: {len(experience)}")

        # Show parsed sections keys and short previews to help diagnose missing content
        raw_sections = parsed.get("raw_sections", {})
        if raw_sections:
            st.write("Sections found:", list(raw_sections.keys()))
            for k, v in raw_sections.items():
                preview = (v or "").strip().replace("\t", " ")
                if preview:
                    preview_display = preview[:400].replace("\n", " | ")
                    ellips = "..." if len(preview) > 400 else ""
                    st.markdown(f"**{k}**: {preview_display}{ellips}")

        # Show dataframe preview (what will be exported)
        st.subheader("Parsed data table preview")
        try:
            df = parsed_to_dataframe(parsed)
            st.dataframe(df)
            st.markdown("**CSV preview (first 400 chars):**")
            csv_preview = df.to_csv(index=False)[:400]
            st.code(csv_preview)
        except Exception as e:
            st.error(f"Could not build preview DataFrame: {e}")

        st.subheader("Extracted JSON")
        json_text = to_json(parsed)
        st.code(json_text, language="json")

        st.subheader("Contact")
        contact = parsed.get("contact", {})
        st.write("Emails:", contact.get("emails", []))
        st.write("Phones:", contact.get("phones", []))
        st.write("LinkedIn:", contact.get("linkedin", []))

        st.subheader("Skills")
        st.write(", ".join(parsed.get("skills", [])))

        st.subheader("Education")
        for edu in parsed.get("education", []):
            st.write(f"- {edu.get('degree')} — {edu.get('institution')} ({edu.get('year')})")

        st.subheader("Experience")
        for exp in parsed.get("experience", []):
            st.write(f"- {exp.get('title_company')}")
            for d in exp.get("details", []):
                st.write(f"    • {d}")

        # Exports
        st.subheader("Export")
        df = parsed_to_dataframe(parsed)
        csv_bytes = df_to_csv_bytes(df)
        st.download_button("Download JSON", data=json_text, file_name="parsed_resume.json", mime="application/json")
        st.download_button("Download CSV", data=csv_bytes, file_name="parsed_resume.csv", mime="text/csv")