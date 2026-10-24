"""Bounded student-question expansion, never a source of campus facts.

The supplied CSV supplies wording patterns, not policies or referral offices.
Only complete, reviewed language patterns may be rewritten. Unrecognized extra
instructions and constraints remain in the original question for normal checks.
"""
from dataclasses import asdict, dataclass
import re

from src.campus_entities import normalize
from src.query_safety import evaluate_query


CATEGORY_ENTITIES = {
    'academic programs': 'academic programs',
    'admissions': 'admissions',
    'student id': 'it office',
    'class schedules': 'academic calendar',
    'transportation': 'campus transportation',
    'accessibility': 'campus accessibility',
    'activities and events': None,
    'housing and accommodation': None,
    'graduation': None,
    'student services': 'student affairs',
    'scholarships and financial aid': 'scholarship',
    'campus navigation': None,
    'international new students': None,
    'enrollment': 'enrollment',
    'information technology': 'it office',
    'health and wellbeing': 'clinic',
    'academic policies': None,
    'student organizations': 'student government',
    'student records': 'registrar',
    'safety and security': 'campus safety',
    'privacy and data': None,
    'policies and rules': 'student handbook',
    'library': 'library',
    'fees and payments': 'cashier',
    'campus facilities': 'campus accessibility',
}

INTRODUCTIONS = {
    'english': (
        'I am a new student at TPC', 'I am getting ready for my first term at TPC',
        'I am new to TPC and I am not sure what to do', 'I am preparing to study at TPC',
        'I am starting at TPC and need guidance', 'I need help as a first-time TPC student',
        'I will be a new TPC student',
    ),
    'tagalog': (
        'Bagong estudyante ako sa TPC', 'Baguhan ako sa TPC at kailangan ko ng gabay',
        'Kailangan ko ng tulong bilang bagong estudyante sa TPC', 'Kakapasok ko lang sa TPC',
        'Mag-aaral ako sa TPC at gusto kong makasiguro', 'Magsisimula ako bilang estudyante sa TPC',
        'Naghahanda ako para sa unang term ko sa TPC',
    ),
    'bisaya': (
        'Bag-o pa ko nga na-enroll sa TPC', 'Bag-o pa ko sa TPC ug nanginahanglan ko og giya',
        'Bag-ong estudyante ko sa TPC', 'Kinahanglan ko og tabang isip bag-ong estudyante sa TPC',
        'Magsugod ko og eskwela sa TPC', 'Magtuon ko sa TPC ug gusto ko makasiguro',
        'Nangandam ko para sa akong unang term sa TPC',
    ),
}

# Each row represents one intent in English, Filipino and Cebuano. These are
# reviewed query words only; no dataset answer or referral becomes evidence.
QUESTION_PATTERNS = (
    ('office_hours', 'hours', ('What are the office hours?', 'Ano ang oras ng opisina?', 'Unsa ang oras sa opisina?')),
    ('location', 'location', ('Where should I go?', 'Saan ako dapat pumunta?', 'Asa ko angay moadto?')),
    ('online_option', 'services', ('Can I do this online?', 'Pwede ba itong gawin online?', 'Pwede ba kini buhaton online?')),
    ('schedule', 'hours', ('When is it scheduled?', 'Kailan ito naka-schedule?', 'Kanus-a kini naka-schedule?')),
    ('referral', 'contact', ('Where can I get help?', 'Saan ako makakakuha ng tulong?', 'Asa ko makakuha og tabang?')),
    ('follow_up', 'services', ('How do I follow up?', 'Paano ako magfo-follow up?', 'Unsaon nako pag-follow up?')),
    ('change_information', 'services', ('How do I change my information?', 'Paano ko babaguhin ang aking impormasyon?', 'Unsaon nako pag-usab sa akong impormasyon?')),
    ('requirements', 'services', ('What requirements do I need?', 'Ano ang mga requirements na kailangan ko?', 'Unsa ang mga requirements nga akong kinahanglan?')),
    ('documents', 'services', ('What documents should I prepare?', 'Anong mga dokumento ang dapat kong ihanda?', 'Unsa nga mga dokumento ang akong andamon?')),
    ('process', 'services', ('What is the process?', 'Ano ang proseso?', 'Unsa ang proseso?')),
    ('first_step', 'services', ('What is the first step?', 'Ano ang unang hakbang?', 'Unsa ang unang lakang?')),
    ('deadlines', 'services', ('What is the deadline?', 'Ano ang deadline?', 'Unsa ang deadline?')),
    ('fees', 'services', ('How much does it cost?', 'Magkano ang bayad o fees?', 'Pila ang bayad o fees?')),
    ('appointment', 'services', ('Do I need an appointment?', 'Kailangan ba ng appointment?', 'Kinahanglan ba og appointment?')),
    ('status', 'services', ('How can I check my status?', 'Paano ko malalaman ang status ko?', 'Unsaon nako pagkahibalo sa akong status?')),
    ('verify_information', 'services', ('How can I verify the information?', 'Paano ko mabe-verify ang impormasyon?', 'Unsaon nako pag-verify sa impormasyon?')),
    ('contact', 'contact', ('Who should I contact?', 'Sino ang dapat kong kontakin?', 'Kinsa ang akong kontakon?')),
    ('eligibility', 'services', ('Who is eligible?', 'Sino ang eligible?', 'Kinsa ang eligible?')),
    ('lost_item', 'services', ('What should I do if I lose a document or item?', 'Ano ang gagawin ko kung mawala ang dokumento o gamit ko?', 'Unsa akong buhaton kung mawala ang dokumento o gamit?')),
    ('correction', 'services', ('What should I do if I made a mistake?', 'Ano ang gagawin ko kung nagkamali ako?', 'Unsa akong buhaton kung nasayop ko?')),
)

_INTRODUCTIONS = {normalize(text): language for language, items in INTRODUCTIONS.items() for text in items}
_QUESTIONS = {normalize(question): (language, facet, intent)
              for facet, intent, questions in QUESTION_PATTERNS
              for language, question in zip(('english', 'tagalog', 'bisaya'), questions)}


@dataclass(frozen=True)
class QueryUnderstanding:
    original_query: str
    normalized_query: str
    language: str
    category: str
    entity: str | None
    intent: str
    facet: str
    audience: str | None = None
    period: str | None = None
    supported_pattern: bool = True
    school_topic: bool = True

    def as_dict(self):
        return asdict(self)


def _period(query):
    match = re.search(r'\b((?:19|20)\d{2})(?:\s*[-–/]\s*((?:19|20)\d{2}))?\b', query)
    return '-'.join(part for part in match.groups() if part) if match else None


def _canonical(entity, facet, category):
    subject = entity or category
    templates = {
        'office_hours': 'What are the {subject} office hours at TPC?',
        'location': 'Where is the {subject} at TPC?',
        'referral': 'Who should I contact about {subject} at TPC?',
        'contact': 'Who should I contact about {subject} at TPC?',
        'requirements': 'What are the requirements for {subject} at TPC?',
        'documents': 'What documents do I need for {subject} at TPC?',
        'process': 'What are the procedures for {subject} at TPC?',
        'first_step': 'What is the first step for {subject} at TPC?',
        'fees': 'How much are the fees for {subject} at TPC?',
        'deadlines': 'What is the deadline for {subject} at TPC?',
        'schedule': 'What is the schedule for {subject} at TPC?',
        'online_option': 'Can I complete {subject} online at TPC?',
        'eligibility': 'Who is eligible for {subject} at TPC?',
        'appointment': 'Do I need an appointment for {subject} at TPC?',
        'status': 'How can I check my {subject} status at TPC?',
        'follow_up': 'How do I follow up on {subject} at TPC?',
        'change_information': 'How do I change my information for {subject} at TPC?',
        'verify_information': 'How can I verify {subject} information at TPC?',
        'lost_item': 'What is the lost document or item procedure for {subject} at TPC?',
        'correction': 'How do I correct a mistake for {subject} at TPC?',
    }
    return templates[facet].format(subject=subject)


def understand_query(query, *, last_entity=None):
    """Expand complete student wording, preserving each requested fact facet.

    ``None`` means the existing resolver should inspect the unchanged question.
    A recognized topic with ``entity=None`` is an unsupported school topic, not
    permission to invent an office or search unverified answers. The caller must
    verify ``facet`` independently before rendering generic source services.
    """
    decision = evaluate_query(query)
    if not decision.allowed:
        return None
    query = decision.normalized_query
    # Dataset structure is explicit rather than inferred from an unrelated
    # adjacent sentence. Full matching prevents hiding a second user request.
    match = re.fullmatch(r'(?:(.+?)\.\s+)?([^.!]+[?])\s+About\s+([\w /&-]+)\.?', query, re.I)
    if match:
        intro, question, category_text = match.groups()
        if intro and normalize(intro) not in _INTRODUCTIONS:
            return None
        pattern = _QUESTIONS.get(normalize(question))
        category = normalize(category_text)
        if not pattern or category not in CATEGORY_ENTITIES:
            return None
        language, facet, intent = pattern
        entity = CATEGORY_ENTITIES[category]
        if category == 'enrollment' and facet in {'requirements', 'documents'}:
            entity = 'enrollment documents'
        return QueryUnderstanding(query, _canonical(entity, facet, category), language,
                                  category, entity, intent, facet,
                                  audience='new_student' if intro else None,
                                  period=_period(query))

    q = normalize(query)
    # Narrow real-student paraphrases extend the reviewed CSV wording. No
    # generated CSV answer, category label, or alleged office is consulted.
    enrollment_location = {
        'where do i register': 'english', 'where can i register': 'english',
        'saan ako magpaparehistro': 'tagalog', 'asa ko magparehistro': 'bisaya',
    }
    if q in enrollment_location:
        return QueryUnderstanding(query, _canonical('enrollment', 'location', 'enrollment'),
                                  enrollment_location[q], 'enrollment', 'enrollment',
                                  'location', 'location')
    requirements = (
        (r'(?:what|which) (?:are the )?(?:documents|requirements)(?: do i need)? (?:for|to) (?:freshman |freshmen |new student )?(?:enrollment|enrolment|enroll|enrol)(?: at tpc)?', 'english'),
        (r'(?:unsa|unsay|unsa ang) (?:mga )?(?:requirements|dokumento) (?:para sa|para) (?:freshmen |freshman |bag ong estudyante nga )?(?:enrollment|enrolment|maka enroll|magpa enroll)(?: sa tpc)?', 'bisaya'),
        (r'(?:ano|ano ang) (?:mga )?(?:requirements|dokumento) (?:para sa|para) (?:freshmen |freshman |bagong estudyanteng )?(?:enrollment|enrolment|makapag enroll|mag enroll)(?: sa tpc)?', 'tagalog'),
    )
    for pattern, language in requirements:
        if re.fullmatch(pattern, q):
            audience = 'new_student' if re.search(r'\b(?:freshman|freshmen|new student|bag ong estudyante|bagong estudyante)\b', q) else None
            return QueryUnderstanding(query, _canonical('enrollment documents', 'requirements', 'enrollment'),
                                      language, 'enrollment', 'enrollment documents',
                                      'services', 'requirements', audience=audience)
    submission_followups = {
        'where do i submit them': 'english', 'where should i submit them': 'english',
        'asa nako ipasa': 'bisaya', 'asa nako ipasa ang mga dokumento': 'bisaya',
        'saan ko isusumite ang mga dokumento': 'tagalog', 'saan ko isusumite ang mga ito': 'tagalog',
    }
    if q in submission_followups:
        # A submission location is not implied by a list of required documents.
        # Keep a distinct facet; only an explicit approved submission fact can
        # answer it, even when the previous subject is enrollment requirements.
        entity = last_entity if last_entity in {'enrollment documents', 'enrollment', 'admissions'} else None
        language = submission_followups[q]
        return QueryUnderstanding(query, f'Where do I submit documents for {entity or "enrollment"} at TPC?',
                                  language, 'enrollment', entity, 'location', 'submission',
                                  supported_pattern=bool(entity))
    return None
