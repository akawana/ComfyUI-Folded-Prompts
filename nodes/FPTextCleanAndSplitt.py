import re
import os
import json
import hashlib

from comfy_api.latest import ComfyExtension, io

_AR_BLOCK_RE = re.compile(r"<AR([1-5])>(.*?)</>", re.DOTALL | re.IGNORECASE)
_AR_OPEN_RE  = re.compile(r"<AR([1-5])>", re.IGNORECASE)
_AR_CLOSE_RE = re.compile(r"</>",         re.IGNORECASE)


def collapse_empty_lines(text: str) -> str:
    text = re.sub(r'\n\s*\n+', '\n\n', text)
    text = re.sub(r'^\s*\n+',  '',     text)
    return text


def build_full_text(before_text: str | None, text: str | None, after_text: str | None) -> str:
    parts = []
    if before_text:
        parts.append(str(before_text))
    if text:
        parts.append(str(text))
    if after_text:
        parts.append(str(after_text))
    return "\n".join([p for p in parts if p is not None and str(p) != ""])


def get_uncommented_text(full_text: str, comment_prefix: str) -> str:
    if not full_text:
        return ""
    lines = full_text.splitlines()
    kept  = []
    for raw_line in lines:
        stripped = raw_line.lstrip()
        if comment_prefix and stripped.startswith(comment_prefix):
            continue
        if comment_prefix:
            idx = raw_line.find(comment_prefix)
            if idx != -1:
                raw_line = raw_line[:idx].rstrip()
        kept.append(raw_line)
    return "\n".join(kept)


def make_all_expt_comments(uncommented_text: str) -> str:
    if not uncommented_text:
        return ""
    s = _AR_OPEN_RE.sub("", uncommented_text)
    s = _AR_CLOSE_RE.sub("", s)
    return collapse_empty_lines(s)


def make_all_expt_areas(uncommented_text: str) -> str:
    if not uncommented_text:
        return ""
    return collapse_empty_lines(re.sub(_AR_BLOCK_RE, "", uncommented_text))


def extract_ar_blocks(text: str) -> dict[str, list[str]]:
    ar_contents = {f"AR{i}": [] for i in range(1, 6)}
    for m in _AR_BLOCK_RE.finditer(text):
        tag_num = int(m.group(1))
        content = (m.group(2) or "").strip()
        if content:
            ar_contents[f"AR{tag_num}"].append(content)
    return ar_contents


def load_comment_prefix() -> str:
    try:
        settings_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "..", "user", "settings.json"
        )
        if os.path.exists(settings_path):
            with open(settings_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                val = data.get("keybinding_extra.comment_prefix")
                if val and isinstance(val, str):
                    # print(f"[FP load_comment_prefix] loaded from settings: {val.strip()!r}")
                    return val.strip()
    except Exception as e:
        print(f"[FP load_comment_prefix] error reading settings: {e}")
    return "//"


class FPTextCleanAndSplitt(io.ComfyNode):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="FPTextCleanAndSplitt",
            display_name="FP Text Clean And Splitt",
            category="AK/Folded Prompts",
            description=(
                "Strips comments and splits AR-tagged blocks from prompt text. "
                "Outputs cleaned text, text without AR areas, per-AR list, "
                "and an Impact Pack wildcard string."
            ),
            inputs=[
                io.String.Input(
                    "text",
                    default="",
                    multiline=True,
                    force_input=True,
                ),
                io.String.Input(
                    "before_text",
                    default="",
                    multiline=False,
                    force_input=True,
                    optional=True,
                ),
                io.String.Input(
                    "after_text",
                    default="",
                    multiline=False,
                    force_input=True,
                    optional=True,
                ),
            ],
            outputs=[
                io.String.Output(display_name="all_expt_comments"),
                io.String.Output(display_name="all_expt_areas"),
                io.Custom("LIST").Output(display_name="ar_list"),
                io.String.Output(display_name="impact_wildcard"),
            ],
            hidden=[io.Hidden.unique_id],
        )

    # @classmethod
    # def fingerprint_inputs(cls, text: str = "", before_text: str = "", after_text: str = "", **kwargs) -> str:
    #     full = (before_text or "") + (text or "") + (after_text or "")
    #     h = hashlib.sha256(full.encode()).hexdigest()
    #     print(f"[FPTextCleanAndSplitt fingerprint_inputs] text={str(text)[:60]!r} => hash={h[:16]}...")
    #     return h

    @classmethod
    def execute(
        cls,
        text: str = "",
        before_text: str = "",
        after_text: str = "",
    ) -> io.NodeOutput:
        unique_id = cls.hidden.unique_id if cls.hidden else "?"
        # print(f"[FP EXECUTE] id={unique_id} called")

        full_text = build_full_text(before_text, text, after_text)

        if not full_text.strip():
            # print(f"[FP EXECUTE] id={unique_id} => empty input, returning blanks")
            return io.NodeOutput("", "", [None] * 5, "")

        prefix = load_comment_prefix()
        # print(f"[FP EXECUTE] id={unique_id} comment_prefix={prefix!r}")
        uncommented_text = get_uncommented_text(full_text, prefix)

        ar_contents = extract_ar_blocks(uncommented_text)
        found_ars   = [k for k, v in ar_contents.items() if v]
        # print(f"[FP EXECUTE] id={unique_id} AR blocks found: {found_ars if found_ars else 'none'}")

        all_expt_comments = make_all_expt_comments(uncommented_text)
        all_expt_areas    = make_all_expt_areas(uncommented_text)

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
                str(p).replace("\r\n", "\n").replace("\r", "\n").strip()
                for p in parts_local
                if p is not None and str(p).strip() != ""
            )
            flat = re.sub(r"\s*,\s*",    ", ", flat)
            flat = re.sub(r"(?:,\s*){2,}", ", ", flat)
            flat = re.sub(r"(?:,\s*)+$",   "",   flat).strip()

            if not flat:
                continue

            if not flat.endswith(","):
                flat += ","
            if flat.endswith(","):
                flat += " "

            impact_lines.append(f"[AR{n}]{flat}")

        bt = (before_text or "").strip()
        at = (after_text  or "").strip()

        if bt or at:
            # print(f"[FP EXECUTE] id={unique_id} before_text={bt[:40]!r} after_text={at[:40]!r}")
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
                    new_line = f"{tag}] {bt} {rest} {at}".rstrip() if rest else f"{tag}] {bt} {at}".rstrip()
                    new_impact_lines.append(new_line)
                else:
                    new_impact_lines.append(line)
            impact_lines = new_impact_lines

        impact_wildcard = "\n".join(impact_lines)

        # print(f"[FP EXECUTE] id={unique_id} all_expt_comments={all_expt_comments[:80]!r}")
        # print(f"[FP EXECUTE] id={unique_id} all_expt_areas={all_expt_areas[:80]!r}")
        # print(f"[FP EXECUTE] id={unique_id} ar_list={[v[:40] if v else None for v in ar_list]}")
        # print(f"[FP EXECUTE] id={unique_id} impact_wildcard={impact_wildcard[:120]!r}")
        # print(f"[FP EXECUTE] id={unique_id} done")

        return io.NodeOutput(all_expt_comments, all_expt_areas, ar_list, impact_wildcard)


class FPTextCleanAndSplittExtension(ComfyExtension):
    async def get_node_list(self) -> list[type[io.ComfyNode]]:
        return [FPTextCleanAndSplitt]


async def comfy_entrypoint() -> FPTextCleanAndSplittExtension:
    return FPTextCleanAndSplittExtension()


NODE_CLASS_MAPPINGS = {
    "FPTextCleanAndSplitt": FPTextCleanAndSplitt,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "FPTextCleanAndSplitt": "FP Text Clean And Splitt",
}
