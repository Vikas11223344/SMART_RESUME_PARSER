"""
Core resume parsing utilities.
- Extract text from PDF (PyMuPDF) and DOCX (python-docx)
- Clean text
- Split into sections heuristically
- Extract contact, skills, education, experience
"""

import re
from typing import List, Dict, Any
try:
    import fitz  # PyMuPDF
    FITZ_AVAILABLE = True
except Exception:
    fitz = None
    FITZ_AVAILABLE = False

try:
    import docx
    DOCX_AVAILABLE = True
except Exception:
    docx = None
    DOCX_AVAILABLE = False

try:
    import spacy
    from spacy.matcher import PhraseMatcher
    SPACY_AVAILABLE = True
except Exception:
    spacy = None
    PhraseMatcher = None
    SPACY_AVAILABLE = False

# Load spaCy model at import time (user must ensure it's installed)
try:
    if SPACY_AVAILABLE:
        nlp = spacy.load("en_core_web_sm")
    else:
        nlp = None
except Exception:
    # If the model isn't present, parsing still may work for regex parts,
    # but spaCy-dependent features will fail until user downloads the model.
    nlp = None


# ---------- Text extraction ----------
def extract_text_from_pdf(path: str) -> str:
    if not FITZ_AVAILABLE:
        raise RuntimeError(
            "PyMuPDF (`fitz`) is not installed in this Python environment.\n"
            "Install it in your virtualenv with: `.\\.venv\\Scripts\\python -m pip install pymupdf`"
        )
    doc = fitz.open(path)
    text_chunks = []
    for page in doc:
        text_chunks.append(page.get_text("text"))
    return "\n".join(text_chunks)


def extract_text_from_docx(path: str) -> str:
    if not DOCX_AVAILABLE:
        raise RuntimeError(
            "python-docx is not installed in this Python environment.\n"
            "Install it in your virtualenv with: `.\\.venv\\Scripts\\python -m pip install python-docx`"
        )
    doc = docx.Document(path)
    paragraphs = [p.text for p in doc.paragraphs]
    return "\n".join(paragraphs)


# ---------- Cleaning ----------
def clean_text(text: str) -> str:
    # Normalize whitespace and remove multiple empty lines
    text = text.replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Remove weird control chars
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]+", "", text)
    return text.strip()


# ---------- Section splitting ----------
SECTION_HEADERS = [
    r"\bexperience\b",
    r"\bwork experience\b",
    r"\bprofessional experience\b",
    r"\beducation\b",
    r"\bskills\b",
    r"\btechnical skills\b",
    r"\bprojects\b",
    r"\bcertifications\b",
    r"\babout\b",
    r"\bsummary\b",
    r"\bobjective\b",
]


def split_sections(text: str) -> Dict[str, str]:
    """
    Splits resume text into sections based on header keywords.
    Returns dict header_lower -> content.
    """
    lines = text.splitlines()
    header_idxs = []
    for i, line in enumerate(lines):
        norm = line.strip().lower()
        for hdr in SECTION_HEADERS:
            if re.search(hdr, norm):
                header_idxs.append((i, norm))
                break

    if not header_idxs:
        # No clear headers; return everything as 'main'
        return {"main": text}

    sections = {}
    for idx, (line_no, norm) in enumerate(header_idxs):
        start = line_no + 1
        end = header_idxs[idx + 1][0] if idx + 1 < len(header_idxs) else len(lines)
        header = lines[line_no].strip()
        sections[header.lower()] = "\n".join(lines[start:end]).strip()

    # Also include text before first header as 'top'
    first_header_line = header_idxs[0][0]
    top_text = "\n".join(lines[:first_header_line]).strip()
    if top_text:
        sections["top"] = top_text

    return sections


# ---------- Contact extraction ----------
EMAIL_RE = re.compile(r"[\w\.-]+@[\w\.-]+\.\w+")
PHONE_RE = re.compile(
    r"(\+?\d{1,3}[-.\s]?)?(\(?\d{2,4}\)?[-.\s]?)?[\d\-.\s]{6,15}"
)
LINKEDIN_RE = re.compile(r"(https?://)?(www\.)?linkedin\.com/[\w\-/]+")


def extract_contact(text: str) -> Dict[str, Any]:
    emails = EMAIL_RE.findall(text)
    phones = PHONE_RE.findall(text)
    # PHONE_RE returns tuples due to groups; rebuild candidates
    phone_candidates = set()
    for m in PHONE_RE.finditer(text):
        candidate = m.group().strip()
        # filter out short numeric fragments
        digits = re.sub(r"\D", "", candidate)
        if 7 <= len(digits) <= 15:
            phone_candidates.add(candidate)
    linkedin = LINKEDIN_RE.findall(text)
    linkedin_urls = []
    for m in LINKEDIN_RE.finditer(text):
        linkedin_urls.append(m.group().strip())

    return {
        "emails": list(dict.fromkeys(emails)),
        "phones": list(phone_candidates),
        "linkedin": linkedin_urls,
    }


# ---------- Skills extraction ----------
# Small curated list for demonstration. Extend this list with real skills.
DEFAULT_SKILLS = [
    "python", "java", "c++", "c#", "javascript", "react", "node.js", "django",
    "flask", "sql", "postgresql", "mysql", "aws", "azure", "gcp", "docker",
    "kubernetes", "git", "linux", "nlp", "spaCy", "pandas", "numpy", "tensorflow",
    "pytorch", "scikit-learn", "excel", "tableau", "power bi"
]


def extract_skills(text: str, skills_list: List[str] = None) -> List[str]:
    if skills_list is None:
        skills_list = DEFAULT_SKILLS

    text_lower = text.lower()
    found = set()

    # 1) PhraseMatcher if spaCy available
    if nlp is not None:
        matcher = PhraseMatcher(nlp.vocab, attr="LOWER")
        patterns = [nlp.make_doc(s) for s in skills_list]
        matcher.add("SKILLS", patterns)
        doc = nlp(text_lower)
        matches = matcher(doc)
        for _mid, start, end in matches:
            span = doc[start:end].text
            found.add(span.lower())

    # 2) fallback: simple substring check
    for s in skills_list:
        if s.lower() in text_lower:
            found.add(s.lower())

    return sorted(list(found))


# ---------- Education extraction ----------
EDU_KEYWORDS = [
    "bachelor", "master", "b\.a\.", "b\.sc\.", "m\.sc\.", "phd", "b\.tech", "m\.tech",
    "bs", "ms", "mba", "associate", "high school", "secondary school"
]


def extract_education(section_text: str) -> List[Dict[str, str]]:
    """
    Very heuristic extraction: finds lines containing degree keywords and date-like tokens.
    """
    results = []
    lines = section_text.splitlines()
    for line in lines:
        low = line.lower()
        if any(re.search(k, low) for k in EDU_KEYWORDS):
            # try extract degree, institution, year
            year_match = re.search(r"(19|20)\d{2}", line)
            year = year_match.group(0) if year_match else ""
            # split by comma to attempt institution extraction
            parts = [p.strip() for p in re.split(r",|-", line) if p.strip()]
            degree = parts[0] if parts else line.strip()
            institution = parts[1] if len(parts) > 1 else ""
            results.append({"degree": degree, "institution": institution, "year": year, "raw": line.strip()})
    return results


# ---------- Experience extraction ----------
DATE_RANGE_RE = re.compile(
    r"((Jan(uary)?|Feb(ruary)?|Mar(ch)?|Apr(il)?|May|Jun(e)?|Jul(y)?|Aug(ust)?|Sep(tember)?|Oct(ober)?|Nov(ember)?|Dec(ember)?)[\w\.\s,-]*\d{4})|((19|20)\d{2})|present",
    flags=re.IGNORECASE,
)


def parse_experience(section_text: str) -> List[Dict[str, Any]]:
    """
    Heuristic parsing of experience lines into job entries.
    Looks for lines with title/company and date ranges.
    """
    entries = []
    lines = [l.strip() for l in section_text.splitlines() if l.strip()]
    cur_entry = None
    for line in lines:
        # if line contains a date, start a new entry
        if DATE_RANGE_RE.search(line):
            # finalize any previous
            if cur_entry:
                entries.append(cur_entry)
            # create new
            cur_entry = {"title_company": line, "dates": DATE_RANGE_RE.findall(line), "details": []}
        else:
            # continuation or bulleted details
            if cur_entry is None:
                # first line without date: treat as title/company
                cur_entry = {"title_company": line, "dates": [], "details": []}
            else:
                cur_entry["details"].append(line)
    if cur_entry:
        entries.append(cur_entry)

    # post-process to simplify dates
    for e in entries:
        dates = DATE_RANGE_RE.findall(e["title_company"])
        # flatten the tuples
        date_tokens = []
        for t in dates:
            for part in t:
                if isinstance(part, str) and re.search(r"(19|20)\d{2}|present", part, re.IGNORECASE):
                    date_tokens.append(part)
        e["date_tokens"] = date_tokens
    return entries


# ---------- Top-level parse ----------
def parse_resume_from_text(text: str) -> Dict[str, Any]:
    text = clean_text(text)
    sections = split_sections(text)

    # Aggregate for contact parsing (use entire text)
    contact = extract_contact(text)

    # Skills: check skills section first, fallback to whole text
    skills_text = ""
    for k in sections:
        if "skill" in k:
            skills_text = sections[k]
            break
    if not skills_text:
        skills_text = text

    skills = extract_skills(skills_text)

    # Education
    education_section = ""
    for k in sections:
        if "educat" in k:
            education_section = sections[k]
            break
    education = extract_education(education_section) if education_section else []

    # Experience
    experience_section = ""
    for k in sections:
        if "experi" in k:
            experience_section = sections[k]
            break
    experience = parse_experience(experience_section) if experience_section else []

    # Summary/objective
    summary = ""
    for k in sections:
        if "summary" in k or "objective" in k:
            summary = sections[k]
            break
    if not summary and "top" in sections:
        # take first 3 lines of top as a probable summary
        summary = "\n".join(sections["top"].splitlines()[:3])

    return {
        "contact": contact,
        "summary": summary,
        "skills": skills,
        "education": education,
        "experience": experience,
        "raw_sections": sections,
    }


def parse_resume_file(path: str) -> Dict[str, Any]:
    lpath = path.lower()
    if lpath.endswith(".pdf"):
        text = extract_text_from_pdf(path)
    elif lpath.endswith(".docx"):
        text = extract_text_from_docx(path)
    elif lpath.endswith(".txt"):
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
    else:
        raise ValueError("Unsupported file type. Supported: pdf, docx, txt")
    return parse_resume_from_text(text)


# For external import:
__all__ = [
    "extract_text_from_pdf",
    "extract_text_from_docx",
    "clean_text",
    "split_sections",
    "extract_contact",
    "extract_skills",
    "extract_education",
    "parse_experience",
    "parse_resume_from_text",
    "parse_resume_file",
]