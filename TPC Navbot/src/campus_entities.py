"""Shared campus query vocabulary; aliases identify records, never supply facts.

Keep query understanding and retrieval filtering on the same vocabulary.
Nicknames and common spelling variants still require an approved record.
"""
import re
from functools import lru_cache


@lru_cache(maxsize=4096)
def normalize(text):
    text = re.sub(r"['’]s\b", "", text.casefold().replace("_", " "))
    text = re.sub(r"\b(?:bldg|bldng)\b", "building", text)
    text = re.sub(r"\bdept\b", "department", text)
    return " ".join(re.findall(r"\w+", text))


ENTITY_ALIASES = {
    'registrar': ('registrar', 'registrars office', 'records office', 'registrar office', 'registar', 'registrars'),
    'library': ('library', 'aklatan', 'basahan', 'basahanan', 'learning center', 'libray', 'borrow books', 'borrowing books', 'maghulam og libro', 'maghulam ug libro', 'manghiram ng libro'),
    'guidance office': ('guidance', 'guidance office', 'guidance center', 'counseling', 'counselling', 'tagapayo'),
    'cashier': ('cashier', 'accounting office', 'finance office', 'cashiering', 'finance services', 'kahera', 'kaser'),
    'clinic': ('clinic', 'tambalanan', 'medical clinic', 'health office', 'klinika'),
    'canteen': ('canteen', 'cafeteria', 'kaonan', 'kainan', 'kantina', 'kan anan', 'kan an', 'dining hall'),
    'gymnasium': ('gym', 'gymnasium', 'gymnasyum', 'covered court'),
    'security office': ('security office', 'campus security', 'gwardya', 'security', 'guardhouse', 'guard house', 'lost and found', 'lost found'),
    'student affairs': ('student affairs', 'saso', 'student services office', 'student services'),
    'student government': ('student government', 'ssg', 'supreme student'),
    'nstp office': ('nstp', 'rotc', 'cwts'),
    'chapel': ('chapel', 'kapilya', 'ecumenical'),
    'restroom': ('restroom', 'comfort room', 'toilet', 'cr', 'kasilyas', 'palikuran'),
    'tuition': ('tuition', 'matrikula', 'bayranan', 'school fees'),
    'admissions': ('admission', 'admissions', 'admission requirements', 'admission and eligibility requirements'),
    'enrollment': ('enrollment', 'enrolment', 'student enrollment', 'enrollment procedures', 'student enrollment procedures', 'enroll', 'enrol', 'magpaenroll', 'magpa enroll'),
    'scholarship': ('scholarship', 'scholarships', 'iskolarship'),
    'lost and found': ('lost and found', 'lost id', 'nawagtang nga id', 'nawalang id'),
    'wifi': ('wifi', 'wi fi', 'campus internet'),
    'student portal': ('student portal', 'lms', 'tpc portal'),
    'student handbook': ('handbook', 'dress code', 'uniform policy', 'uniporme'),
    'parking': ('parking', 'parking area'),
    'bsis department': ('bsis',),
    'bsais department': ('bsais',),
    'criminology department': ('bscrim', 'criminology', 'kriminolohiya', 'crim', 'crim building', 'crim department', 'criminolgy'),
    'agriculture department': ('bsag', 'agriculture', 'agri', 'agrikultura', 'agri building'),
    'political science department': ('polsci', 'baps', 'political science department'),
    'education department': ('beced', 'education department'),
    'computer laboratories': ('computer laboratories', 'computer laboratory', 'computer labs', 'computer lab', 'comlab', 'comlab1', 'comlab2', 'comlab 1', 'comlab 2', 'com lab'),
    'main building': ('main building', 'main academic building'),
    'administration offices': ('administration offices', 'administrative offices', 'admin offices', 'administration office', 'admin office', 'administration building', 'admin building', 'administration', 'admin'),
    'faculty offices': ('faculty offices', 'faculty office', 'faculty room'),
    'it office': ('it office', 'student id services', 'student id', 'student ids', 'id issuance', 'id replacement'),
    'enrollment documents': ('enrollment requirements and documents', 'enrollment documents', 'enrolment documents', 'enrollment requirements', 'enrolment requirements'),
    'academic programs': ('academic programs and departments', 'academic programs', 'degree programs', 'programs offered', 'courses offered', 'programs', 'courses'),
    'academic calendar': ('academic calendar and school schedule', 'academic calendar', 'school schedule', 'school calendar'),
    'examination policies': ('examination schedules and policies', 'examination policies', 'exam policies', 'examination schedules', 'examination schedule', 'exam schedules', 'exam schedule', 'examinations', 'exams', 'examination', 'exam'),
    'grading system': ('grading system and academic evaluation', 'grading system', 'academic evaluation', 'grading scale', 'passing grade', 'grading'),
    'attendance policies': ('student attendance and absence policies', 'attendance policies', 'attendance policy', 'attendance', 'absence policies', 'allowable absences'),
    'campus safety': ('campus safety and emergency procedures', 'campus safety', 'emergency procedures', 'emergency contacts', 'emergency numbers', 'emergency hotline', 'evacuation'),
    'campus accessibility': ('campus facilities and accessibility', 'campus accessibility', 'campus facilities', 'campus ramps', 'campus wheelchair access'),
    'campus transportation': ('campus transportation and parking rules', 'campus transportation', 'transportation rules', 'parking rules'),
    'campus communication': ('campus communication channels and announcements', 'campus communication', 'communication channels', 'campus announcements', 'official announcements', 'official website', 'tpc website', 'college website', 'official facebook page'),
    'college information': ('general college information', 'general campus information', 'college information', 'about tpc', 'about talibon polytechnic college', 'tpc contact', 'tpc phone', 'tpc email', 'tpc address', 'campus address', 'college address'),
    'computer studies': ('computer studies', 'bsis', 'bsais', 'ccis'),
}


NORMALIZED_ALIASES = {name: tuple(dict.fromkeys(normalize(alias) for alias in aliases))
                      for name, aliases in ENTITY_ALIASES.items()}


def destination_matches(text):
    words = " " + normalize(str(text)) + " "
    return {name for name, aliases in NORMALIZED_ALIASES.items()
            if any(" " + alias + " " in words for alias in aliases)}
