"""Security and HTML/Rich-Text sanitization utilities for learning content.

Prevents XSS, script execution, arbitrary embeds, and unsafe external protocol links.
"""

from html.parser import HTMLParser
import re
from typing import Set, Dict, List, Optional
from urllib.parse import urlparse

SAFE_TAGS: Set[str] = {
    "h1", "h2", "h3", "h4", "h5", "h6",
    "p", "br", "hr",
    "strong", "b", "em", "i", "u", "s", "strike", "mark",
    "ul", "ol", "li",
    "blockquote", "pre", "code",
    "a", "img", "span", "div",
    "table", "thead", "tbody", "tr", "th", "td",
}

SAFE_ATTRS: Dict[str, Set[str]] = {
    "a": {"href", "title", "target", "rel"},
    "img": {"src", "alt", "title", "width", "height"},
    "code": {"class"},
    "pre": {"class"},
    "span": {"class"},
    "div": {"class"},
    "th": {"colspan", "rowspan", "scope"},
    "td": {"colspan", "rowspan"},
}

SAFE_PROTOCOLS: Set[str] = {"http", "https", "mailto"}


class _HTMLSanitizer(HTMLParser):
    """Deterministic HTML parser that strips unsafe tags and attributes."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.result: List[str] = []
        self.skip_stack: int = 0  # To discard content inside <script>, <style>

    def handle_starttag(self, tag: str, attrs: list):
        tag_lower = tag.lower()
        if tag_lower in {"script", "style", "iframe", "object", "embed", "applet"}:
            self.skip_stack += 1
            return

        if self.skip_stack > 0:
            return

        if tag_lower not in SAFE_TAGS:
            return

        clean_attrs = []
        allowed = SAFE_ATTRS.get(tag_lower, set())

        for key, val in attrs:
            key_lower = key.lower()
            if key_lower.startswith("on"):  # Strip event handlers (onclick, etc.)
                continue
            if key_lower not in allowed:
                continue

            # Validate URLs for href and src
            if key_lower in {"href", "src"}:
                val_clean = val.strip()
                parsed = urlparse(val_clean)
                if parsed.scheme and parsed.scheme.lower() not in SAFE_PROTOCOLS:
                    continue  # Drop unsafe protocol (javascript:, data:, etc.)
                clean_attrs.append(f'{key_lower}="{self._escape_attr(val_clean)}"')
            elif key_lower == "rel" and tag_lower == "a":
                clean_attrs.append('rel="noopener noreferrer"')
            else:
                clean_attrs.append(f'{key_lower}="{self._escape_attr(val)}"')

        if tag_lower == "a" and "rel=" not in " ".join(clean_attrs):
            clean_attrs.append('rel="noopener noreferrer"')

        attrs_str = (" " + " ".join(clean_attrs)) if clean_attrs else ""
        if tag_lower in {"br", "hr", "img"}:
            self.result.append(f"<{tag_lower}{attrs_str} />")
        else:
            self.result.append(f"<{tag_lower}{attrs_str}>")

    def handle_endtag(self, tag: str):
        tag_lower = tag.lower()
        if tag_lower in {"script", "style", "iframe", "object", "embed", "applet"}:
            if self.skip_stack > 0:
                self.skip_stack -= 1
            return

        if self.skip_stack > 0:
            return

        if tag_lower in SAFE_TAGS and tag_lower not in {"br", "hr", "img"}:
            self.result.append(f"</{tag_lower}>")

    def handle_data(self, data: str):
        if self.skip_stack == 0:
            self.result.append(self._escape_text(data))

    @staticmethod
    def _escape_text(text: str) -> str:
        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )

    @staticmethod
    def _escape_attr(text: str) -> str:
        return (
            text.replace("&", "&amp;")
            .replace('"', "&quot;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )


def sanitize_html(raw_html: Optional[str]) -> str:
    """Sanitizes raw HTML to safe markup, stripping scripts, iframes, and malicious attributes."""
    if not raw_html:
        return ""
    sanitizer = _HTMLSanitizer()
    sanitizer.feed(raw_html)
    return "".join(sanitizer.result)


def validate_content_block(block_type: str, content: str, media_url: Optional[str] = None) -> tuple[str, Optional[str]]:
    """Validates and sanitizes a lesson content block.
    
    Returns (sanitized_content, validated_media_url).
    """
    valid_types = {
        "heading", "paragraph", "image", "video", "code",
        "callout", "quote", "resource", "embed"
    }
    if block_type not in valid_types:
        raise ValueError(f"Invalid block_type '{block_type}'. Must be one of {valid_types}")

    # Sanitize content
    sanitized_content = sanitize_html(content) if ("<" in content and ">" in content) else content

    # Validate media_url if provided
    validated_url = None
    if media_url:
        stripped_url = media_url.strip()
        parsed = urlparse(stripped_url)
        if parsed.scheme and parsed.scheme.lower() in SAFE_PROTOCOLS:
            validated_url = stripped_url
        elif stripped_url.startswith("/") or stripped_url.startswith("media/"):
            # Relative local storage reference
            validated_url = stripped_url
        else:
            raise ValueError("Invalid media URL protocol. Must be HTTP/HTTPS or local media path.")

    return sanitized_content, validated_url
