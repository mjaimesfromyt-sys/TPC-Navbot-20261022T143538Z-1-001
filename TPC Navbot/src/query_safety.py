"""Bound and classify untrusted questions before retrieval, memory or model calls.

This is a defense-in-depth input filter, not an authorization boundary. Approved
sources, non-executable retrieval, and server-side scope checks remain necessary.
The detector never executes code or follows links supplied in a question.
"""
from dataclasses import dataclass
import base64
import binascii
import html
import re
import unicodedata
from urllib.parse import unquote


MAX_QUERY_CHARS = 600
MAX_QUERY_WORDS = 120

_MESSAGES = {
    "english": {
        "too_long": "Please use no more than 600 characters, 120 words, and three school questions per message.",
        "invalid_input": "Please enter a short, readable question about TPC.",
        "empty": "Please enter a question about TPC.",
        "unsafe": "I can help with verified TPC information and official account recovery or IT support. I cannot follow requests to bypass safeguards, expose private information, or attack systems.",
    },
    "bisaya": {
        "too_long": "Palihug limitahi ang matag mensahe sa 600 ka karakter, 120 ka pulong, ug hangtod tulo ka pangutana bahin sa eskwelahan.",
        "invalid_input": "Palihug pagsulat og mubo ug klaro nga pangutana bahin sa TPC.",
        "empty": "Palihug pagsulat og pangutana bahin sa TPC.",
        "unsafe": "Makatabang ko sa verified nga impormasyon sa TPC ug opisyal nga account recovery o IT support. Dili ko makatabang sa paglikay sa mga panalipod, pagbutyag sa pribadong impormasyon, o pag-atake sa mga sistema.",
    },
    "tagalog": {
        "too_long": "Pakilimitahan ang bawat mensahe sa 600 karakter, 120 salita, at hanggang tatlong tanong tungkol sa paaralan.",
        "invalid_input": "Pakisulat ang maikli at malinaw na tanong tungkol sa TPC.",
        "empty": "Pakisulat ang tanong tungkol sa TPC.",
        "unsafe": "Makatutulong ako sa beripikadong impormasyon ng TPC at opisyal na account recovery o IT support. Hindi ako makatutulong sa pag-iwas sa mga pananggalang, paglalantad ng pribadong impormasyon, o pag-atake sa mga sistema.",
    },
}


@dataclass(frozen=True)
class QuerySafetyDecision:
    allowed: bool
    reason: str
    normalized_query: str = ""

    def refusal_message(self, language="english"):
        messages = _MESSAGES.get(language, _MESSAGES["english"])
        key = self.reason if self.reason in ("too_long", "empty", "invalid_input") else "unsafe"
        return "" if self.allowed else messages[key]


# Fold common Latin lookalikes only for detection; preserve user spelling in the
# returned text. NFKC handles full-width and mathematical Latin characters.
_CONFUSABLES = str.maketrans({
    "а": "a", "е": "e", "о": "o", "р": "p", "с": "c", "у": "y",
    "х": "x", "і": "i", "ј": "j", "ѕ": "s", "ԁ": "d", "ԛ": "q",
    "α": "a", "ε": "e", "ο": "o", "ρ": "p", "ι": "i", "κ": "k",
    "τ": "t", "υ": "u", "ν": "v", "χ": "x",
})
_LEET = str.maketrans({"0": "o", "1": "i", "3": "e", "4": "a", "5": "s", "7": "t", "@": "a", "$": "s"})
_BIDI_CONTROLS = frozenset("\u061c\u200e\u200f\u202a\u202b\u202c\u202d\u202e\u2066\u2067\u2068\u2069")

_INJECTION = tuple(re.compile(pattern, re.I) for pattern in (
    r"\b(?:ignore|disregard|forget|override|bypass)\b.{0,70}\b(?:instructions?|prompts?|rules?|guardrails?|safeguards?|restrictions?|safety filters?|polic(?:y|ies))\b",
    r"\b(?:do not|dont|don't|stop)\s+(?:follow(?:ing)?|obey(?:ing)?)\b.{0,50}\b(?:instructions?|rules?|polic(?:y|ies))\b",
    r"\b(?:ayaw|kalimti|baliwalaa|ibaliwala|huwag|balewalain|kalimutan|wag)\b.{0,70}\b(?:sunda|sundin|lagda|patakaran|instructions?|rules?|system|prompt)\b",
    r"\b(?:pretend|act as|you are now|switch to|enable|activate)\b.{0,60}\b(?:unrestricted|unfiltered|developer mode|admin mode|root|terminal|shell|dan|chatgpt|general (?:purpose|ai))\b",
    r"\b(?:jailbreak|developer mode|do anything now)\b",
    r"(?:<\|(?:im_start|im_end|system|assistant|endoftext)\|>|\[/?inst\]|<<\s*/?sys\s*>>)",
    r"(?:^|[\n\r])\s*(?:system|developer|assistant)\s*:\s*",
    r"\b(?:reveal|show|print|repeat|return|give|tell|dump|expose|display|what (?:is|are))\b.{0,65}\b(?:(?:your|hidden|internal|original|full)\s+)?(?:system|developer)\s+(?:prompt|message|instructions?)\b",
    r"\b(?:your|hidden|internal)\s+(?:system|developer)\s+(?:prompt|instructions?)\b",
    r"\b(?:treat|use|save|remember|learn|accept)\b.{0,45}\b(?:this|following|my|new)\b.{0,45}\b(?:verified (?:fact|source)|official (?:fact|source)|new (?:truth|rule)|system instructions?)\b",
))

_SENSITIVE = tuple(re.compile(pattern, re.I) for pattern in (
    r"\b(?:reveal|show|print|dump|export|expose|give|read|list|send|display|steal|leak|extract|exfiltrate|retrieve|get)\b.{0,70}(?:\b(?:(?:[a-z]+[_-])*api[ _-]?keys?|secret[ _-]?keys?|credentials?|access tokens?|service[ _-]?account[ _-]?keys?|database passwords?|admin passwords?)\b|\.env\b|os\.environ|st\.secrets|/etc/(?:passwd|shadow))",
    r"\b(?:what (?:is|are)|tell me)\b.{0,45}\b(?:your|gemini|openai|server|database|admin)\b.{0,30}\b(?:api[ _-]?keys?|passwords?|credentials?|secrets?)\b",
    r"\b(?:private|confidential|another student|other students?|ibang estudyante|laing estudyante|someone else'?s)\b.{0,60}\b(?:records?|grades?|passwords?|addresses?|phone|contact details|data|accounts?|logins?)\b",
    r"\b(?:dump|export|steal|leak|extract|exfiltrate)\b.{0,60}\b(?:student|school|portal|user|attendance)\b.{0,40}\b(?:database|records?|grades?|passwords?|data)\b",
    r"\b(?:ipakita|ibunyag|ihatag|ipadala|ibutang|kunin|kuhaon|ilabas)\b.{0,60}\b(?:api[ _-]?key|admin password|database password|secret key|pribadong|password sa uban|password ng iba)\b",
))

_HARMFUL = tuple(re.compile(pattern, re.I) for pattern in (
    r"\b(?:how (?:can|do|to)|help me|teach me|show me|steps? to|instructions? (?:to|for)|ways? to|paano|unsaon)[ -]+(?:(?:i|we|you|to|can|quickly|easily|anonymously|secretly|please|ko|mo|nako|pag|mag)[ -]+){0,5}(?:hack|hacking|crack|break into|ddos|dos attack|exploit|phish|steal)\b",
    r"\b(?:hack|crack|break into|attack|compromise|exploit|ddos|phish)\s+(?:(?:the|a|my|our|tpc|school|student|college|campus|this|someone'?s|their|an?)\s+){0,5}(?:portal|website|server|account|network|wifi|wi fi|database|system|email|password)\b",
    r"\b(?:bypass|disable|evade|circumvent|remove)\b.{0,45}\b(?:authenticat\w*|login|access controls?|firewalls?|security|antivirus|rate limit|content filter|restrictions?)\b",
    r"\b(?:write|create|generate|build|give|provide|send|run|execute|make|gumawa|gawan|paghimo|buhata)\b.{0,65}\b(?:malware|ransomware|keylogger|reverse shell|credential (?:stealer|harvester)|phishing (?:page|email|site)|(?:sql|command|xss) injection (?:payload|script)|exploit (?:code|script)|ddos (?:tool|script))\b",
    r"\b(?:sql injection|xss|reverse shell|credential stuffing|brute force)\b.{0,40}\b(?:payload|script|code|command|attack|school portal|student portal)\b",
    r"\b(?:perform|launch|mount|conduct)\b.{0,35}\b(?:sql injection|xss|credential stuffing|brute force|phishing|ddos|denial of service)\b",
    r"\b(?:scan|probe|enumerate)\s+(?:(?:the|a|our|tpc|school|campus|student|target)\s+){0,4}(?:servers?|networks?|websites?|portals?|open ports|vulnerabilities)\b",
    r"(?:^|\b(?:help me|how (?:can|do) i)\s+)(?:please\s+)?(?:run|execute|use|give|show)\b.{0,40}\b(?:nmap|sqlmap|metasploit|hydra|burp suite)\b",
    r"\b(?:gain unauthorized access|access without permission|hijack|take over)\b.{0,45}\b(?:portal|website|server|account|network|database|system|email)\b",
    r"\b(?:run|execute|eval|launch)\b.{0,30}\b(?:powershell|cmd\.exe|bash|whoami|curl|wget|subprocess|os\.system)\b",
    r"(?:os\.system\s*\(|subprocess\.(?:run|popen|call)\s*\(|__import__\s*\(|\beval\s*\(|\bexec\s*\(|(?:curl|wget)\b.{0,80}\|\s*(?:sh|bash|powershell))",
    r"\b(?:baguhin|palitan|usba|ilisan|change|alter|modify|tamper)\b.{0,50}\b(?:my|akong|aking|student|portal|school)\b.{0,25}\b(?:grades?|attendance|records?)\b.{0,45}\b(?:database|without permission|walang pahintulot|bypass|hack)\b",
))


def _views(text):
    """Produce bounded detection views for common transport obfuscation."""
    value = text
    for _ in range(2):
        value = unicodedata.normalize("NFKC", html.unescape(unquote(value)))
        value = "".join(char for char in value if unicodedata.category(char) != "Cf")
    value = value.casefold().translate(_CONFUSABLES)
    yield value
    # Preserve line-based role checks and inspect whitespace-obfuscated text.
    yield " ".join(value.split())
    folded = value.translate(_LEET)
    folded = re.sub(r"\b(?:[a-z][\s._-]+){2,}[a-z]\b", lambda m: re.sub(r"[\s._-]", "", m.group()), folded)
    yield folded
    yield " ".join(folded.split())
    # Encoded instructions remain untrusted. Inspect short base64 strings, but
    # never decode them into executable commands or pass them to any interpreter.
    for token in re.findall(r"(?<![\w+/])[A-Za-z0-9+/]{24,}={0,2}(?![\w+/=])", text):
        try:
            decoded = base64.b64decode(token + "=" * (-len(token) % 4), validate=True).decode("utf-8")
        except (ValueError, binascii.Error, UnicodeDecodeError):
            continue
        if decoded.isprintable():
            yield unicodedata.normalize("NFKC", decoded).casefold().translate(_CONFUSABLES)


def _reporting_question(text):
    """Keep incident reporting available without permitting a second task."""
    reporting = re.search(
        r"^(?:(?:how|where) (?:can|do|should) (?:i|we) (?:report|contact)|"
        r"who (?:can|do|should) (?:i|we) (?:contact|tell|inform)|"
        r"(?:paano|saan) (?:ko |ako )?(?:i?report|magreport|mag report)|"
        r"(?:unsaon|asa) (?:nako |ko )?(?:i?report|magreport|mag report))\b",
        text.strip(),
    )
    extra_action = re.search(
        r"(?:\b(?:and|then|also|but|ug|at)\b|[;.!?])\s*.{0,30}\b"
        r"(?:hack|crack|bypass|write|generate|create|show|give|provide|execute|run|attack|exploit|dump|export|steal|extract|exfiltrate|read|reveal|print|display|obtain|retrieve)\b",
        text,
    )
    # Asking whom to contact *to perform* an attack is not incident reporting.
    attack_contact = re.search(r"\bcontact\s+(?:\w+\s+){0,3}to\s+(?:hack|crack|bypass|attack|exploit)\b", text)
    return bool(reporting and not extra_action and not attack_contact)


def evaluate_query(query, *, max_chars=MAX_QUERY_CHARS, max_words=MAX_QUERY_WORDS):
    """Return a safe normalized question, or a refusal with no retained payload.

    ``allowed`` does not mean a question is in school scope or factually true.
    Reject invalid/oversize input *before* normalization to bound work and memory.
    A question is never silently truncated into a different request.
    """
    if (not isinstance(max_chars, int) or isinstance(max_chars, bool) or max_chars < 1
            or not isinstance(max_words, int) or isinstance(max_words, bool) or max_words < 1):
        raise ValueError("Question limits must be positive integers")
    if not isinstance(query, str):
        return QuerySafetyDecision(False, "invalid_input")
    if len(query) > max_chars:
        return QuerySafetyDecision(False, "too_long")
    if any((unicodedata.category(char) in ("Cc", "Cs") and char not in "\t\r\n") or char in _BIDI_CONTROLS for char in query):
        return QuerySafetyDecision(False, "invalid_input")
    normalized = unicodedata.normalize("NFKC", query)
    normalized = "".join(char for char in normalized if unicodedata.category(char) != "Cf")
    normalized = " ".join(normalized.split())
    if not normalized:
        return QuerySafetyDecision(False, "empty")
    if len(normalized) > max_chars or len(normalized.split()) > max_words:
        return QuerySafetyDecision(False, "too_long")
    # Keep line breaks in the detection view to catch forged role messages.
    for view in _views(query):
        for reason, patterns in (("prompt_injection", _INJECTION), ("sensitive_data", _SENSITIVE), ("harmful_request", _HARMFUL)):
            if any(pattern.search(view) for pattern in patterns):
                if reason == "harmful_request" and _reporting_question(view):
                    continue
                if (reason == "sensitive_data" and _reporting_question(view)
                        and _SENSITIVE[2].search(view)
                        and not any(pattern.search(view) for pattern in _SENSITIVE[:2] + _SENSITIVE[3:])):
                    continue
                return QuerySafetyDecision(False, reason)
    return QuerySafetyDecision(True, "allowed", normalized)
