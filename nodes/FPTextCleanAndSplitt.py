import re
import os
import json


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

    RETURN_TYPES = ("STRING", "LIST", "STRING")
    RETURN_NAMES = ("cleaned_text", "ar_list", "impact_wildcard")
    FUNCTION = "execute"
    CATEGORY = "AK/Folded Prompts"
    OUTPUT_NODE = False

    @classmethod
    def IS_CHANGED(cls, before_text=None, text="", after_text=None, **kwargs):
        before_text = before_text or ""
        text = text or ""
        after_text = after_text or ""

        full = "\n\n".join([s for s in (before_text, text, after_text) if s != ""])

        cleaned_for_hash = re.sub(
            r"<AR([1-5])>(?:(?!</>).)*</>",
            "",
            full,
            flags=re.IGNORECASE | re.DOTALL,
        )

        cleaned_for_hash = cleaned_for_hash.replace("\r\n", "\n").replace("\r", "\n")
        cleaned_for_hash = re.sub(r"\s*,\s*", ", ", cleaned_for_hash)
        cleaned_for_hash = re.sub(r"(?:,\s*){2,}", ", ", cleaned_for_hash)
        cleaned_for_hash = re.sub(r"(?:,\s*)+$", "", cleaned_for_hash).strip()

        return hash(cleaned_for_hash)

    def execute(self, before_text=None, text="", after_text=None):
        parts = []
        if before_text:
            parts.append(before_text.rstrip())
        if text:
            parts.append(text)
        if after_text:
            parts.append(after_text.lstrip())

        full_text = "\n".join(filter(None, parts))

        if not full_text.strip():
            return ("", [None] * 5, "")

        prefix = self.get_comment_prefix()
        lines = full_text.splitlines()

        cleaned_lines = []
        ar_contents = {f"AR{i}": [] for i in range(1, 6)}
        i = 0

        while i < len(lines):
            raw_line = lines[i]
            stripped = raw_line.lstrip()
            line = raw_line.strip()

            if prefix and stripped.startswith(prefix):
                i += 1
                continue

            inline_matches = list(
                re.finditer(r"<AR([1-5])>(.*?)</>", raw_line, re.IGNORECASE)
            )
            if inline_matches:
                for m in inline_matches:
                    tag_num = int(m.group(1))
                    content = m.group(2).strip()
                    if content:
                        ar_contents[f"AR{tag_num}"].append(content)

                remaining = re.sub(
                    r"<AR([1-5])>.*?</>", "", raw_line, flags=re.IGNORECASE
                )
                remaining = remaining.replace("\r\n", "\n").rstrip("\n")

                remaining = re.sub(r"\s*,\s*", ", ", remaining)
                remaining = re.sub(r"(?:,\s*){2,}", ", ", remaining)
                remaining = re.sub(r"(?:,\s*)+$", "", remaining).rstrip()

                if remaining:
                    if not remaining.endswith(","):
                        remaining += ","
                        remaining += " "
                    cleaned_lines.append(remaining)

                i += 1
                continue

            match = re.match(r"<AR([1-5])>(.*)$", line, re.IGNORECASE)
            if match:
                tag_num = int(match.group(1))
                tail = match.group(2)

                block_lines = []

                tail = tail.strip()
                if tail:
                    block_lines.append(tail)

                if "</>" in tail:
                    before, _sep, _after = tail.partition("</>")
                    before = before.strip()
                    if before:
                        block_lines.append(before)
                    content = "\n".join(block_lines).rstrip()
                    if content:
                        ar_contents[f"AR{tag_num}"].append(content)
                    i += 1
                    continue

                i += 1
                while i < len(lines):
                    inner_raw = lines[i]
                    inner_stripped = inner_raw.lstrip()
                    inner_line = inner_raw.strip()

                    if "</>" in inner_line:
                        before, _sep, _after = inner_raw.partition("</>")
                        before = before.strip()
                        if before:
                            block_lines.append(before)
                        i += 1
                        break

                    if prefix and inner_stripped.startswith(prefix):
                        i += 1
                        continue

                    block_lines.append(inner_raw.rstrip("\n"))
                    i += 1

                content = "\n".join(block_lines).rstrip()
                if content:
                    ar_contents[f"AR{tag_num}"].append(content)
                continue

            if line:
                cleaned_lines.append(raw_line.rstrip())
            i += 1

        cleaned_text = "\n".join(
            [ln.rstrip().replace("\r\n", "\n") for ln in cleaned_lines]
        ).strip()

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
                    rest = rest or ""
                    rest = rest.strip()
                    if rest:
                        new_line = f"{tag}] {bt} {rest} {at}".rstrip()
                    else:
                        new_line = f"{tag}] {bt} {at}".rstrip()
                    new_impact_lines.append(new_line)
                else:
                    new_impact_lines.append(line)
            impact_lines = new_impact_lines

        impact_wildcard = "\n".join(impact_lines)

        return (cleaned_text, ar_list, impact_wildcard)

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
