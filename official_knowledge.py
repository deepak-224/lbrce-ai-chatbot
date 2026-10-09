
import os
import re
import time
from io import BytesIO

import requests
from bs4 import BeautifulSoup

try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None


# ============================================================
# CONFIGURATION
# ============================================================

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
GROQ_MODEL = "openai/gpt-oss-20b"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

REQUEST_TIMEOUT = 25
GROQ_TIMEOUT = 60
CACHE_SECONDS = 1800
MAX_PAGE_CHARS = 7000
MAX_CONTEXT_CHARS = 6500
MAX_SYLLABUS_ANSWER_CHARS = 14000

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; LBRCECollegeAssistant/1.0)"
}

OFFICIAL_SYLLABUS_PAGE = (
    "https://www.lbrce.ac.in/academic_pages/course_structure.php"
)

CSE_SYLLABUS_PAGE = (
    "https://lbrce.ac.in/cse/csecourse_syllabus.php"
)

R23_CSE_PDF = (
    "https://lbrce.ac.in/academics/syllabus/R23/"
    "R23_CSE_Syllabus1.pdf"
)

PLACEMENT_2025_2026_URL = (
    "https://www.lbrce.ac.in/placements/stat2526.php"
)


# ============================================================
# OFFICIAL SOURCES
# ============================================================

SOURCES = [
    {
        "name": "LBRCE Homepage",
        "url": "https://www.lbrce.ac.in/",
    },
    {
        "name": "Admissions",
        "url": "https://lbrce.ac.in/admission_pages/admissions.php",
    },
    {
        "name": "Courses and Departments",
        "url": "https://www.lbrce.ac.in/courses.php",
    },
    {
        "name": "Course Structure and Syllabus",
        "url": OFFICIAL_SYLLABUS_PAGE,
    },
    {
        "name": "CSE Syllabus",
        "url": CSE_SYLLABUS_PAGE,
    },
    {
        "name": "Contact Information",
        "url": "https://lbrce.ac.in/quicklinks_pages/contact.php",
    },
    {
        "name": "Placement Statistics 2025-2026",
        "url": PLACEMENT_2025_2026_URL,
    },
    {
        "name": "General Placement Statistics",
        "url": "https://www.lbrce.ac.in/placements/pstatistics.php",
    },
    {
        "name": "Placement Selections 2026-2027",
        "url": "https://www.lbrce.ac.in/placements/stat2627.php",
    },
    {
        "name": "Examination Timetables",
        "url": (
            "https://www.lbrce.ac.in/examsection_pages/"
            "examtables.php"
        ),
    },
    {
        "name": "ERP Portal",
        "url": "https://erp.lbrce.ac.in/",
    },
]


# ============================================================
# CACHES
# ============================================================

PAGE_CACHE = {}

PDF_CACHE = {
    "time": 0,
    "pages": None,
    "error": None,
}


# ============================================================
# COMMON HELPERS
# ============================================================

def normalize(text):
    """Normalize whitespace and dash characters."""
    if not text:
        return ""

    text = str(text)
    text = text.replace("\u2013", "-")
    text = text.replace("\u2014", "-")
    text = text.replace("\u2212", "-")
    text = re.sub(r"[ \t]+", " ", text)

    return text.strip()


def fetch_page(url):
    """Download and extract readable text from an official webpage."""
    cached = PAGE_CACHE.get(url)

    if cached and time.time() - cached["time"] < CACHE_SECONDS:
        return cached["text"]

    try:
        response = requests.get(
            url,
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        for element in soup(
            ["script", "style", "noscript", "svg", "iframe"]
        ):
            element.decompose()

        pieces = []

        for element in soup.find_all(
            ["h1", "h2", "h3", "h4", "p", "li", "tr"]
        ):
            value = normalize(element.get_text(" ", strip=True))

            if value:
                pieces.append(value)

        page_text = "\n".join(pieces)[:MAX_PAGE_CHARS]

        if page_text:
            PAGE_CACHE[url] = {
                "time": time.time(),
                "text": page_text,
            }

        print(
            f"[LBRCE] Loaded webpage: {url} "
            f"({len(page_text)} characters)"
        )

        return page_text

    except requests.RequestException as exc:
        print(f"[LBRCE] Webpage retrieval failed: {url}: {exc}")
        return ""


# ============================================================
# OFFICIAL R23 CSE PDF READER
# ============================================================

def get_r23_cse_pdf_pages(force_refresh=False):
    """
    Download the official R23 CSE PDF and extract page text.

    Returns a list of page texts, or None on failure.
    """
    global PDF_CACHE

    if PdfReader is None:
        PDF_CACHE["error"] = (
            "pypdf is not installed. Run: "
            ".\\.venv\\Scripts\\python.exe -m pip install pypdf"
        )
        return None

    if (
        not force_refresh
        and PDF_CACHE["pages"] is not None
        and time.time() - PDF_CACHE["time"] < CACHE_SECONDS
    ):
        return PDF_CACHE["pages"]

    try:
        response = requests.get(
            R23_CSE_PDF,
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()

        if not response.content.startswith(b"%PDF"):
            raise ValueError(
                "The official syllabus URL did not return a valid PDF."
            )

        reader = PdfReader(BytesIO(response.content))
        pages = []

        for page_number, page in enumerate(reader.pages):
            try:
                page_text = page.extract_text() or ""
            except Exception as exc:
                print(
                    f"[LBRCE] Could not extract PDF page "
                    f"{page_number + 1}: {exc}"
                )
                page_text = ""

            pages.append(page_text)

        if not any(text.strip() for text in pages):
            raise ValueError(
                "No readable text could be extracted from the PDF."
            )

        PDF_CACHE = {
            "time": time.time(),
            "pages": pages,
            "error": None,
        }

        print(
            f"[LBRCE] Extracted text from {len(pages)} PDF pages."
        )

        return pages

    except Exception as exc:
        PDF_CACHE["error"] = str(exc)
        print(f"[LBRCE] Syllabus PDF retrieval failed: {exc}")
        return None


# ============================================================
# VERIFIED VII SEMESTER COURSE REFERENCE
# ============================================================

# These names and credits reflect the published VII Semester
# structure in the official LBRCE CSE R23 syllabus PDF.
#
# This reference list is not used to invent detailed unit topics.
# Detailed units must be extracted separately from the PDF.

R23_CSE_VII_COURSES = [
    {
        "code": "23AM06",
        "title": "Deep Learning",
        "credits": "3",
        "category": "Core subject",
    },
    {
        "code": "23HS05",
        "title": "Human Resources & Project Management",
        "credits": "2",
        "category": "Core subject",
    },
    {
        "code": "23IT11",
        "title": "Software Architecture & Design Patterns",
        "credits": "3",
        "category": "Program Elective IV",
    },
    {
        "code": "23CS16",
        "title": "Blockchain Technology",
        "credits": "3",
        "category": "Program Elective IV",
    },
    {
        "code": "23IT08",
        "title": "DevOps",
        "credits": "3",
        "category": "Program Elective IV",
    },
    {
        "code": "23AD11",
        "title": "Agentic AI",
        "credits": "3",
        "category": "Program Elective IV",
    },
    {
        "code": "23IT12",
        "title": "Agile Methodologies",
        "credits": "3",
        "category": "Program Elective V",
    },
    {
        "code": "23IT10",
        "title": "Generative AI",
        "credits": "3",
        "category": "Program Elective V",
    },
    {
        "code": "23AM07",
        "title": "Computer Vision",
        "credits": "3",
        "category": "Program Elective V",
    },
    {
        "code": "23CS17",
        "title": "Cyber Physical Systems",
        "credits": "3",
        "category": "Program Elective V",
    },
    {
        "code": "23AMS1",
        "title": "Prompt Engineering Lab",
        "credits": "2",
        "category": "Laboratory",
    },
    {
        "code": "23MC05",
        "title": "Constitution of India",
        "credits": "Non-credit / mandatory",
        "category": "Mandatory course",
    },
    {
        "code": "23PI02",
        "title": "Evaluation of Industry Internship / Mini Project",
        "credits": "2",
        "category": "Internship / Mini Project evaluation",
    },
]


def get_seventh_semester_section(pages):
    """
    Locate the actual VII Semester course-structure table.

    A page must contain the VII Semester heading and multiple
    known VII Semester codes. This helps reject table-of-contents
    pages that only mention the semester name.
    """
    if not pages:
        return None

    expected_codes = {
        course["code"] for course in R23_CSE_VII_COURSES
    }

    candidates = []

    for index, page in enumerate(pages):
        text = page or ""

        if not re.search(
            r"\bVII\s+SEMESTER\b",
            text,
            re.IGNORECASE,
        ):
            continue

        codes_found = {
            code
            for code in expected_codes
            if re.search(rf"\b{re.escape(code)}\b", text, re.I)
        }

        if len(codes_found) >= 2:
            candidates.append((index, len(codes_found)))

    if not candidates:
        print(
            "[LBRCE] Could not identify the actual VII Semester "
            "table using its course codes."
        )
        return None

    # Prefer the page with the greatest number of expected codes.
    start_index = max(candidates, key=lambda item: item[1])[0]

    section_parts = []

    for index in range(start_index, min(start_index + 4, len(pages))):
        text = pages[index] or ""

        next_semester = re.search(
            r"\bVIII\s+SEMESTER\b",
            text,
            re.IGNORECASE,
        )

        if next_semester:
            text = text[:next_semester.start()]

        section_parts.append(text)

        if next_semester:
            break

    section = "\n".join(section_parts).strip()

    return section or None


def extract_semester_subjects(section):
    """
    Return verified VII Semester courses whose codes appear in
    the identified official table section.

    Unknown course details are not generated.
    """
    if not section:
        return []

    extracted = []
    section_upper = section.upper()

    for course in R23_CSE_VII_COURSES:
        code = course["code"]

        if re.search(rf"\b{re.escape(code)}\b", section_upper):
            extracted.append(course.copy())

    # Open elective entries do not have specific course codes/titles
    # in the semester table, so their names are not invented.
    if re.search(
        r"\bOPEN\s+ELECTIVE\s*[-–]?\s*III\b",
        section,
        re.IGNORECASE,
    ):
        extracted.append({
            "code": "Not specified in the table",
            "title": "Open Elective III (SWAYAM/NPTEL MOOC, 12 weeks)",
            "credits": "3",
            "category": "Open Elective III",
        })

    if re.search(
        r"\bOPEN\s+ELECTIVE\s*[-–]?\s*IV\b",
        section,
        re.IGNORECASE,
    ):
        extracted.append({
            "code": "Not specified in the table",
            "title": "Open Elective IV",
            "credits": "3",
            "category": "Open Elective IV",
        })

    return extracted


# ============================================================
# DETAILED UNIT EXTRACTION
# ============================================================

def find_unit_content(pages, course_code, course_title=None):
    """
    Extract unit topics from a detailed syllabus section.

    The course code and title must be found near unit headings.
    This function returns no unit data when the match is uncertain.
    """
    if not pages or not course_code:
        return []

    code_pattern = re.compile(
        rf"\b{re.escape(course_code)}\b",
        re.IGNORECASE,
    )

    title_words = []

    if course_title:
        title_words = [
            word.lower()
            for word in re.findall(r"[A-Za-z]{4,}", course_title)
        ]

    candidates = []

    # Search the detailed syllabus pages, not the opening table.
    for page_index in range(min(10, len(pages)), len(pages)):
        page_text = pages[page_index] or ""

        if not code_pattern.search(page_text):
            continue

        # A heading may wrap across adjacent PDF pages.
        nearby_start = max(0, page_index - 1)
        nearby_end = min(page_index + 3, len(pages))

        nearby_pages = pages[nearby_start:nearby_end]
        nearby_text = "\n".join(nearby_pages)

        # A detailed course section should contain a unit heading.
        unit_matches = list(re.finditer(
            r"\bUNIT\s*[-–:]?\s*(I{1,3}|IV|V|1|2|3|4|5)\b",
            nearby_text,
            re.IGNORECASE,
        ))

        if not unit_matches:
            continue

        # Check that the course title occurs near the code.
        if title_words:
            code_position = nearby_text.lower().find(
                course_code.lower()
            )

            title_window = nearby_text[
                max(0, code_position - 300):
                min(len(nearby_text), code_position + 1200)
            ].lower()

            if not any(word in title_window for word in title_words):
                continue

        candidates.append((page_index, nearby_text))

    if not candidates:
        return []

    # The earliest matching detailed section is used.
    _, candidate_text = candidates[0]

    matches = list(re.finditer(
        r"\bUNIT\s*[-–:]?\s*(I{1,3}|IV|V|1|2|3|4|5)\b",
        candidate_text,
        re.IGNORECASE,
    ))

    roman_to_number = {
        "I": 1,
        "II": 2,
        "III": 3,
        "IV": 4,
        "V": 5,
    }

    units = []
    seen_units = set()

    for index, match in enumerate(matches):
        label = match.group(1).upper()

        unit_number = (
            int(label)
            if label.isdigit()
            else roman_to_number.get(label)
        )

        if unit_number is None or unit_number in seen_units:
            continue

        start = match.end()

        end = (
            matches[index + 1].start()
            if index + 1 < len(matches)
            else len(candidate_text)
        )

        content = normalize(candidate_text[start:end])

        if content:
            units.append({
                "unit": unit_number,
                "content": content[:1800],
            })
            seen_units.add(unit_number)

    return units


def format_r23_cse_syllabus_answer(message):
    """Build a syllabus response from the official R23 PDF."""
    pages = get_r23_cse_pdf_pages()

    if pages is None:
        error = PDF_CACHE.get("error") or "Unknown PDF retrieval error"

        return (
            "I could not retrieve or read the official R23 CSE syllabus "
            "PDF right now. I will not guess its subjects or units.\n\n"
            f"Official PDF: {R23_CSE_PDF}\n"
            f"Official syllabus page: {OFFICIAL_SYLLABUS_PAGE}\n\n"
            f"Technical detail: {error}"
        )

    section = get_seventh_semester_section(pages)

    if not section:
        return (
            "I downloaded the official R23 CSE syllabus PDF, but could "
            "not reliably identify the VII Semester course table. "
            "I will not guess the subjects or credits.\n\n"
            f"Official PDF: {R23_CSE_PDF}\n"
            f"Official syllabus page: {OFFICIAL_SYLLABUS_PAGE}"
        )

    subjects = extract_semester_subjects(section)

    if not subjects:
        return (
            "The official R23 CSE PDF was downloaded, but the VII "
            "Semester table could not be matched to the verified "
            "course list. Please check the PDF directly.\n\n"
            f"Official PDF: {R23_CSE_PDF}"
        )

    answer = [
        "LBRCE B.Tech CSE — R23 Regulation — VII Semester",
        "",
        "Official source:",
        R23_CSE_PDF,
        "",
        "Subjects and course options listed in the official "
        "VII Semester structure:",
        "",
    ]

    for subject in subjects:
        answer.append(
            f"- {subject['code']}: {subject['title']} "
            f"| Credits: {subject['credits']} "
            f"| Category: {subject['category']}"
        )

    answer.extend([
        "",
        "Elective note: Program Electives IV and V are options. "
        "The actual subjects taken depend on the electives offered "
        "and selected by your section.",
        "",
        "Detailed unit topics",
    ])

    unit_details_found = False

    for subject in subjects:
        code = subject["code"]

        if code == "Not specified in the table":
            continue

        units = find_unit_content(
            pages,
            code,
            subject["title"],
        )

        if not units:
            continue

        unit_details_found = True

        answer.extend([
            "",
            f"{code} — {subject['title']}",
        ])

        for unit in units:
            answer.append(
                f"Unit {unit['unit']}: {unit['content']}"
            )

    if not unit_details_found:
        answer.extend([
            "",
            "The PDF text extraction did not reliably match detailed "
            "unit sections to the listed subjects. No unit topics "
            "have been guessed. Open the official PDF to view the "
            "unit-wise syllabus.",
        ])

    answer.extend([
        "",
        "Official links:",
        f"- R23 CSE syllabus PDF: {R23_CSE_PDF}",
        f"- CSE syllabus page: {CSE_SYLLABUS_PAGE}",
        f"- Course Structure: {OFFICIAL_SYLLABUS_PAGE}",
    ])

    return "\n".join(answer)[:MAX_SYLLABUS_ANSWER_CHARS]


# ============================================================
# TOPIC DETECTION
# ============================================================

TOPIC_ALIASES = {
    "syllabus": [
        "syllabus",
        "course structure",
        "semester subjects",
        "subject codes",
        "course codes",
        "credits",
        "units",
        "7th semester",
        "7th sem",
        "seventh semester",
        "semester curriculum",
    ],
    "placements": [
        "placement",
        "placements",
        "placed students",
        "placement statistics",
        "recruiters",
        "companies",
        "company names",
        "highest package",
        "placement department",
    ],
    "admissions": [
        "admission",
        "admissions",
        "eapcet",
        "ecet",
        "management quota",
        "lateral entry",
        "eligibility",
        "seat allocation",
    ],
    "courses": [
        "courses offered",
        "branches",
        "departments",
        "programmes",
        "programs",
        "b.tech",
        "m.tech",
        "mba",
        "computer science",
    ],
    "contact": [
        "contact",
        "phone number",
        "telephone",
        "email",
        "address",
        "call us",
    ],
    "exams": [
        "exam timetable",
        "examination",
        "exam schedule",
        "exam notification",
        "semester exam",
        "results",
    ],
    "erp": [
        "erp",
        "student portal",
        "student login",
        "fee payment",
    ],
}


def identify_topics(message):
    """Identify topics in the user question."""
    text = normalize(message).lower()
    topics = set()

    for topic, keywords in TOPIC_ALIASES.items():
        if any(keyword in text for keyword in keywords):
            topics.add(topic)

    return topics


def is_college_question(message):
    """Check whether the question relates to LBRCE."""
    text = normalize(message).lower()

    keywords = [
        "lbrce",
        "lakireddy",
        "college",
        "campus",
        "placement",
        "admission",
        "syllabus",
        "semester",
        "course structure",
        "department",
        "eapcet",
        "ecet",
        "examination",
        "erp",
        "recruiter",
    ]

    return any(word in text for word in keywords)


# ============================================================
# SYLLABUS QUESTION ROUTING
# ============================================================

def is_syllabus_question(message):
    """Detect questions asking about a syllabus or course structure."""
    text = normalize(message).lower()

    return any(
        keyword in text
        for keyword in [
            "syllabus",
            "course structure",
            "semester subjects",
            "subject codes",
            "course codes",
            "semester curriculum",
            "7th semester",
            "7th sem",
            "seventh semester",
            "semester vii",
            "semester 7",
        ]
    )


def is_r23_cse_seventh_semester_question(message):
    """Detect the specific CSE R23 VII Semester request."""
    text = normalize(message).lower()

    is_cse = (
        "cse" in text
        or "computer science and engineering" in text
        or "computer science engineering" in text
    )

    is_seventh = any(
        term in text
        for term in [
            "7th semester",
            "7th sem",
            "seventh semester",
            "semester vii",
            "semester 7",
            "vii semester",
        ]
    )

    is_r23 = any(
        term in text
        for term in [
            "r23",
            "2023 batch",
            "joined in 2023",
            "2023 admission",
            "2026-2027",
            "2026–2027",
            "2026-27",
            "2026–27",
        ]
    )

    return is_cse and is_seventh and is_r23


def syllabus_answer(message):
    """Answer general syllabus questions using official links."""
    if is_r23_cse_seventh_semester_question(message):
        return format_r23_cse_syllabus_answer(message)

    text = normalize(message).lower()

    is_cse = (
        "cse" in text
        or "computer science and engineering" in text
        or "computer science engineering" in text
    )

    is_2026_2027 = any(
        year in text
        for year in [
            "2026-2027",
            "2026–2027",
            "2026-27",
            "2026–27",
        ]
    )

    joined_2023 = any(
        phrase in text
        for phrase in [
            "joined in 2023",
            "joined in the year 2023",
            "2023 batch",
            "2023 admission",
            "admission year 2023",
        ]
    )

    answer = []

    if is_cse:
        answer.extend([
            "For the LBRCE B.Tech Computer Science and Engineering "
            "syllabus, use the official CSE syllabus page:",
            CSE_SYLLABUS_PAGE,
        ])
    else:
        answer.extend([
            "For the official LBRCE course structure and syllabus, use:",
            OFFICIAL_SYLLABUS_PAGE,
        ])

    answer.append("")

    if joined_2023:
        answer.append(
            "For a student who joined B.Tech in 2023, R23 is likely "
            "to be the relevant regulation. Confirm it against your "
            "official syllabus document."
        )
    elif is_2026_2027:
        answer.append(
            "The academic year alone does not confirm which regulation "
            "applies. Select the regulation matching your admission batch."
        )
    else:
        answer.append(
            "LBRCE publishes syllabus documents under different "
            "regulations. Select the regulation that applies to your batch."
        )

    answer.extend([
        "",
        "I will not guess subject names, course codes, credits, or units.",
        "",
        "Official syllabus links:",
        f"- Course Structure: {OFFICIAL_SYLLABUS_PAGE}",
    ])

    if is_cse:
        answer.append(f"- CSE syllabus: {CSE_SYLLABUS_PAGE}")
        answer.append(f"- R23 CSE PDF: {R23_CSE_PDF}")

    return "\n".join(answer)


# ============================================================
# PLACEMENT COMPANY EXTRACTION
# ============================================================

def get_official_placement_company_list():
    """Extract company names from the official 2025-2026 table."""
    try:
        response = requests.get(
            PLACEMENT_2025_2026_URL,
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        company_names = []

        for table in soup.find_all("table"):
            rows = table.find_all("tr")

            if not rows:
                continue

            headers = [
                normalize(cell.get_text(" ", strip=True)).lower()
                for cell in rows[0].find_all(["th", "td"])
            ]

            company_index = next(
                (
                    index
                    for index, header in enumerate(headers)
                    if "company" in header
                ),
                None,
            )

            if company_index is None:
                continue

            for row in rows[1:]:
                cells = row.find_all(["td", "th"])

                if company_index >= len(cells):
                    continue

                name = normalize(
                    cells[company_index].get_text(" ", strip=True)
                )

                if not name or name.isdigit():
                    continue

                if name.lower() in {
                    "company",
                    "total",
                    "grand total",
                    "total placements",
                }:
                    continue

                company_names.append(name)

            if company_names:
                break

        unique_names = list(dict.fromkeys(company_names))

        if not unique_names:
            return None

        return {
            "companies": unique_names,
            "count": len(unique_names),
            "source": PLACEMENT_2025_2026_URL,
        }

    except requests.RequestException as exc:
        print(f"[LBRCE] Placement extraction failed: {exc}")
        return None


def is_2025_26_company_list_question(message):
    """Detect requests for the 2025-2026 placement company list."""
    text = normalize(message).lower()

    asks_for_companies = any(
        word in text
        for word in [
            "company",
            "companies",
            "recruiter",
            "recruiters",
        ]
    )

    asks_about_placements = any(
        word in text
        for word in ["placement", "placed", "selected"]
    )

    asks_for_year = any(
        year in text
        for year in [
            "2025-2026",
            "2025–2026",
            "2025-26",
            "2025–26",
            "25-26",
        ]
    )

    asks_for_list = any(
        word in text.lower()
        for word in ["list", "all", "names", "duplicate"]
    )

    return (
        asks_for_companies
        and asks_about_placements
        and asks_for_year
        and asks_for_list
    )


def placement_company_list_answer():
    """Format company names extracted from the official table."""
    result = get_official_placement_company_list()

    if not result:
        return (
            "I could not retrieve the company list from the official "
            "LBRCE placement page. Please try again later:\n"
            f"{PLACEMENT_2025_2026_URL}"
        )

    lines = [
        "Companies listed in the official LBRCE 2025-2026 placement table:",
        "",
    ]

    for number, company in enumerate(result["companies"], start=1):
        lines.append(f"{number}. {company}")

    lines.extend([
        "",
        f"Total unique company names: {result['count']}",
        f"Official source: {result['source']}",
    ])

    return "\n".join(lines)


# ============================================================
# OFFICIAL CONTEXT FOR GROQ
# ============================================================

def select_sources(message):
    """Choose official webpages relevant to the question."""
    topics = identify_topics(message)
    selected = set()

    if is_syllabus_question(message):
        selected.update([
            "Course Structure and Syllabus",
            "CSE Syllabus",
        ])

    if "placements" in topics:
        text = normalize(message).lower()

        if "2025-2026" in text or "2025–2026" in text:
            selected.add("Placement Statistics 2025-2026")
        elif "2026-2027" in text or "2026–2027" in text:
            selected.add("Placement Selections 2026-2027")
        else:
            selected.update([
                "General Placement Statistics",
                "Contact Information",
            ])

    if "admissions" in topics:
        selected.add("Admissions")

    if "courses" in topics:
        selected.update([
            "Courses and Departments",
            "Admissions",
        ])

    if "contact" in topics:
        selected.add("Contact Information")

    if "exams" in topics:
        selected.add("Examination Timetables")

    if "erp" in topics:
        selected.add("ERP Portal")

    if not selected:
        selected.add("LBRCE Homepage")

    return [
        source
        for source in SOURCES
        if source["name"] in selected
    ]


def collect_official_context(message):
    """Fetch relevant official webpages and combine their text."""
    sources = select_sources(message)

    print(f"[LBRCE] Question: {message}")
    print(f"[LBRCE] Topics: {identify_topics(message)}")
    print(
        "[LBRCE] Sources: "
        + ", ".join(source["name"] for source in sources)
    )

    parts = []

    for source in sources:
        page_text = fetch_page(source["url"])

        if page_text:
            parts.append(
                f"SOURCE: {source['name']}\n"
                f"URL: {source['url']}\n"
                f"CONTENT:\n{page_text}"
            )

    return "\n\n".join(parts)[:MAX_CONTEXT_CHARS]


# ============================================================
# GROQ API
# ============================================================

def call_groq(message, official_context):
    """Generate a college-information answer from official context."""
    if not GROQ_API_KEY:
        return (
            "The AI service is not configured. Please set GROQ_API_KEY "
            "in your environment or Render settings."
        )

    system_prompt = """
You are the LBRCE AI Assistant for Lakireddy Bali Reddy College
of Engineering.

Rules:
1. Use official source context for college-related answers.
2. Never invent course names, syllabus subjects, course codes, credits,
   unit topics, phone numbers, emails, dates, or statistics.
3. Preserve company names as published in official tables.
4. If sources disagree, explain the uncertainty.
5. An academic year does not automatically identify a regulation.
6. If the exact syllabus is not available in the supplied context,
   provide the official syllabus link.
7. Never claim to have read a PDF unless its text was retrieved.
8. Do not label a general admissions number as a direct placement number.
9. Keep answers clear and beginner-friendly.

OFFICIAL SOURCE CONTEXT:
""" + (official_context or "No official content was retrieved.")

    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message},
        ],
        "temperature": 0.1,
        "max_tokens": 1400,
    }

    try:
        response = requests.post(
            GROQ_URL,
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=GROQ_TIMEOUT,
        )

        if response.status_code != 200:
            print(
                "[LBRCE] Groq API error:",
                response.status_code,
                response.text[:1000],
            )
            return (
                "Sorry, I could not generate an answer right now. "
                "Please try again shortly."
            )

        data = response.json()
        choices = data.get("choices", [])

        if not choices:
            return (
                "Sorry, the AI service returned an empty response. "
                "Please try again."
            )

        answer = choices[0].get("message", {}).get("content", "")

        if not answer or not answer.strip():
            return (
                "Sorry, I could not find a reliable answer. "
                "Please try again."
            )

        return answer.strip()

    except requests.RequestException as exc:
        print(f"[LBRCE] Groq request failed: {exc}")
        return (
            "Sorry, the AI service is temporarily unavailable. "
            "Please try again later."
        )

    except (ValueError, KeyError, IndexError) as exc:
        print(f"[LBRCE] Invalid Groq response: {exc}")
        return (
            "Sorry, I received an unexpected response. "
            "Please try again."
        )


# ============================================================
# MAIN FUNCTION IMPORTED BY app.py
# ============================================================

def answer_from_official_site(message):
    """Main entry point used by the existing Flask application."""
    message = normalize(message)

    if not message:
        return "Please enter a question about LBRCE."

    # Specific R23 CSE VII Semester requests use the official PDF.
    if is_r23_cse_seventh_semester_question(message):
        return format_r23_cse_syllabus_answer(message)

    # Other syllabus questions use official syllabus guidance.
    if is_syllabus_question(message):
        return syllabus_answer(message)

    # Company names are extracted directly from the official table.
    if is_2025_26_company_list_question(message):
        return placement_company_list_answer()

    # Keep the assistant focused on LBRCE.
    if not is_college_question(message):
        return (
            "I am the LBRCE AI Assistant. I can help with official "
            "college information about courses, admissions, placements, "
            "syllabus, examinations, contacts, and the ERP portal."
        )

    official_context = collect_official_context(message)

    text = message.lower()

    asks_for_placement_contact = (
        ("placement" in text or "placements" in text)
        and any(
            word in text
            for word in [
                "contact",
                "phone",
                "number",
                "email",
                "call",
                "reach",
            ]
        )
    )

    if asks_for_placement_contact and not official_context:
        return (
            "I could not retrieve verified Placement Department "
            "contact details. Please check the official contact pages:\n"
            "https://lbrce.ac.in/quicklinks_pages/contact.php\n"
            "https://lbrce.ac.in/admission_pages/admissions.php\n\n"
            "A general admissions number should not be treated as "
            "a confirmed direct Placement Department number."
        )

    return call_groq(message, official_context)
