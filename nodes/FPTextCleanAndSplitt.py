import re
import os
import json
from collections import defaultdict

_AR_BLOCK_RE = re.compile(r"<AR([1-5])>(.*?)</>", re.DOTALL | re.IGNORECASE)
_AR_OPEN_RE = re.compile(r"<AR([1-5])>", re.IGNORECASE)
_AR_CLOSE_RE = re.compile(r"</>", re.IGNORECASE)


def build_full_text(before_text: str | None, text: str | None, after_text: str | None) -> str:
    parts = []
    if before_text:
        parts.append(str(before_text).rstrip())
    if text:
        parts.append(str(text))
    if after_text:
        parts.append(str(after_text).lstrip())
    return "\n".join([p for p in parts if p is not None and str(p) != ""])


def get_uncommented_text(full_text: str, comment_prefix: str) -> str:
    if not full_text:
        return ""
    lines = full_text.splitlines()
    kept = []
    for raw_line in lines:
        stripped = raw_line.lstrip()
        if comment_prefix and stripped.startswith(comment_prefix):
            continue
        kept.append(raw_line)
    return "\n".join(kept)


def make_all_expt_comments(uncommented_text: str) -> str:
    if not uncommented_text:
        return ""
    s = _AR_OPEN_RE.sub("", uncommented_text)
    s = _AR_CLOSE_RE.sub("", s)
    return s


def make_all_expt_areas(uncommented_text: str) -> str:
    if not uncommented_text:
        return ""
    return re.sub(_AR_BLOCK_RE, "", uncommented_text).strip()


def extract_ar_blocks(text: str) -> dict[str, list[str]]:
    ar_contents = {f"AR{i}": [] for i in range(1, 6)}
    for m in _AR_BLOCK_RE.finditer(text):
        tag_num = int(m.group(1))
        content = (m.group(2) or "").strip()
        if content:
            ar_contents[f"AR{tag_num}"].append(content)
    return ar_contents


class FPTextCleanAndSplitt:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "text": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "",
                        "forceInput": True,
                    },
                ),
            },
            "optional": {
                "before_text": (
                    "STRING",
                    {
                        "multiline": False,
                        "default": "",
                        "forceInput": True,
                    },
                ),
                "after_text": (
                    "STRING",
                    {
                        "multiline": False,
                        "default": "",
                        "forceInput": True,
                    },
                ),
            },
        }

    RETURN_TYPES = ("STRING", "STRING", "LIST", "STRING")
    RETURN_NAMES = ("all_expt_comments", "all_expt_areas", "ar_list", "impact_wildcard")
    FUNCTION = "execute"
    CATEGORY = "AK/Folded Prompts"
    OUTPUT_NODE = False

    @classmethod
    def IS_CHANGED(cls, before_text=None, text="", after_text=None, **kwargs):
        full = build_full_text(before_text or "", text or "", after_text or "")
        prefix = cls().get_comment_prefix()
        uncommented = get_uncommented_text(full, prefix)

        cleaned_for_hash = re.sub(
            r"<AR([1-5])>(?:(?!</>).)*</>",
            "",
            uncommented,
            flags=re.IGNORECASE | re.DOTALL,
        )

        cleaned_for_hash = cleaned_for_hash.replace("\r\n", "\n").replace("\r", "\n")
        cleaned_for_hash = re.sub(r"\s*,\s*", ", ", cleaned_for_hash)
        cleaned_for_hash = re.sub(r"(?:,\s*){2,}", ", ", cleaned_for_hash)
        cleaned_for_hash = re.sub(r"(?:,\s*)+$", "", cleaned_for_hash).strip()

        return hash(cleaned_for_hash)

    def execute(self, before_text=None, text="", after_text=None):
        full_text = build_full_text(before_text, text, after_text)

        if not full_text.strip():
            return ("", "", [None] * 5, "")

        prefix = self.get_comment_prefix()
        uncommented_text = get_uncommented_text(full_text, prefix)

        ar_contents = extract_ar_blocks(uncommented_text)

        all_expt_comments = make_all_expt_comments(uncommented_text).strip()
        all_expt_areas = make_all_expt_areas(uncommented_text).strip()

        ar_list = []
        for n in range(1, 6):
            combined = "\n".join(ar_contents[f"AR{n}"]).strip()
            ar_list.append(combined if combined else None)

        impact_lines = ["[LAB]"]
        for n in range(1, 6):
            parts_local = ar_contents.get(f"AR{n}", [])
            if not parts_local:
                continue

            flat = " ".join(
                [
                    str(p)
                    .replace("\r\n", "\n")
                    .replace("\r", "\n")
                    .strip()
                    for p in parts_local
                    if p is not None and str(p).strip() != ""
                ]
            )
            flat = re.sub(r"\s*,\s*", ", ", flat)
            flat = re.sub(r"(?:,\s*){2,}", ", ", flat)
            flat = re.sub(r"(?:,\s*)+$", "", flat).strip()

            if not flat:
                continue

            if not flat.endswith(","):
                flat += ","
            if flat.endswith(","):
                flat += " "

            impact_lines.append(f"[AR{n}]{flat}")

        bt = (before_text or "").strip()
        at = (after_text or "").strip()

        if bt or at:
            new_ar_list = []
            for v in ar_list:
                if v is None:
                    new_ar_list.append(None)
                else:
                    new_ar_list.append(f"{bt} {v} {at}".strip())
            ar_list = new_ar_list

            new_impact_lines = []
            for line in impact_lines:
                if line.startswith("[AR") and "]" in line:
                    tag, rest = line.split("]", 1)
                    rest = (rest or "").strip()
                    if rest:
                        new_line = f"{tag}] {bt} {rest} {at}".rstrip()
                    else:
                        new_line = f"{tag}] {bt} {at}".rstrip()
                    new_impact_lines.append(new_line)
                else:
                    new_impact_lines.append(line)
            impact_lines = new_impact_lines

        impact_wildcard = "\n".join(impact_lines)

        return (all_expt_comments, all_expt_areas, ar_list, impact_wildcard)

    def get_comment_prefix(self):
        try:
            settings_path = os.path.join(
                os.path.dirname(__file__), "..", "..", "..", "user", "settings.json"
            )
            if os.path.exists(settings_path):
                with open(settings_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    val = data.get("keybinding_extra.comment_prefix")
                    if val and isinstance(val, str):
                        return val.strip()
        except:
            pass
        return "//"


NODE_CLASS_MAPPINGS = {
    "FPTextCleanAndSplitt": FPTextCleanAndSplitt,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "FPTextCleanAndSplitt": "FP Text Clean And Splitt",
}
