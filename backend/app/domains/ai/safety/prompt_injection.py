"""Prompt injection detector and input sanitization defenses for Domain 11."""

import re
from typing import Tuple, List

# Signatures of prompt injection, role override, system extraction, and credential theft
INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior|your)\s+(instructions|rules|directives)",
    r"disregard\s+(all\s+)?(previous|prior|your)\s+(instructions|rules|directives)",
    r"(reveal|print|show)\s+(me\s+)?(the\s+|your\s+)?(system|initial)\s+prompt",
    r"you\s+are\s+now\s+in\s+developer\s+mode",
    r"dan\s+mode",
    r"bypass\s+all\s+(filters|rules|restrictions)",
    r"drop\s+table\s+",
    r"select\s+.*\s+from\s+users",
    r"give\s+me\s+(the\s+)?database\s+credentials",
    r"(show|list|get|leak)\s+(me\s+)?(other|another)\s+student('s|\s+)(grades|records|mastery|data)?",
    r"call\s+(the\s+)?admin\s+(analytics\s+)?tool",
    r"(search|show|get|read|leak)\s+private\s+(faculty|student)\s+notes",
    r"(use\s+this\s+.*as\s+a\s+|new\s+)system\s+instruction",
    r"alter\s+my\s+grade",
    r"change\s+my\s+mastery",
    r"override\s+rbac",
    r"act\s+as\s+system\s+admin",
]

COMPILED_INJECTION_REGEX = [re.compile(p, re.IGNORECASE) for p in INJECTION_PATTERNS]


class PromptInjectionDefense:
    """Deterministic security scanner evaluating incoming prompts for adversarial patterns."""

    @staticmethod
    def scan_for_injection(text: str) -> Tuple[bool, List[str]]:
        """Scans input text against known jailbreak, instruction override, and adversarial patterns.
        
        Returns:
            (is_flagged: bool, matched_patterns: List[str])
        """
        matches = []
        for pattern in COMPILED_INJECTION_REGEX:
            if pattern.search(text):
                matches.append(pattern.pattern)

        return (len(matches) > 0, matches)
