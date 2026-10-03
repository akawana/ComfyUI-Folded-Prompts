import re
import os
import json
import hashlib

from comfy_api.latest import ComfyExtension, io
from .PromptUtils import (
    clearCommentedLines, formatTags,
    clearHtmlLikeTags, clearHtmlLikeTagsWithContent,
    clearDoubleEmptyLines,
    htmlTagsContentList, getHtmlTagContent, insertStringToListItems,
    createImpactWildcard, extractNegotives,
)

_AR_BLOCK_RE = re.compile(r"<AR([1-5])>(.*?)</>", re.DOTALL | re.IGNORECASE)


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


_AR_TAGS = ("<AR1>", "<AR2>", "<AR3>", "<AR4>", "<AR5>", "<ALL>")


def make_all_expt_comments(full_text: str, comment_prefix: str) -> str:
    """
    all_expt_comments pipeline:
      clearCommentedLines → clearHtmlLikeTags(AR1..5, ALL) → clearDoubleEmptyLines → formatTags
    """
    if not full_text:
        return ""
    s = clearCommentedLines(full_text, comment_prefix)
    s = clearHtmlLikeTags(s, *_AR_TAGS)
    s = clearDoubleEmptyLines(s)
    return formatTags(s)


def make_all_expt_areas(full_text: str, comment_prefix: str) -> str:
    """
    all_expt_areas pipeline:
      clearCommentedLines → clearHtmlLikeTagsWithContent(AR1..5, ALL) → clearDoubleEmptyLines → formatTags
    """
    if not full_text:
        return ""
    s = clearCommentedLines(full_text, comment_prefix)
    s = clearHtmlLikeTagsWithContent(s, *_AR_TAGS)
    s = clearDoubleEmptyLines(s)
    return formatTags(s)


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
                "an Impact Pack wildcard string, and --negative tags."
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
                io.String.Output(display_name="negotives"),
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
            return io.NodeOutput("", "", [None] * 5, "", "")

        prefix = load_comment_prefix()
        # print(f"[FP EXECUTE] id={unique_id} comment_prefix={prefix!r}")
        uncommented_text = get_uncommented_text(full_text, prefix)
        uncommented_text, negotives = extractNegotives(uncommented_text)

        ar_contents = extract_ar_blocks(uncommented_text)
        found_ars   = [k for k, v in ar_contents.items() if v]
        # print(f"[FP EXECUTE] id={unique_id} AR blocks found: {found_ars if found_ars else 'none'}")

        all_expt_comments = make_all_expt_comments(uncommented_text, prefix)
        all_expt_areas    = make_all_expt_areas(uncommented_text, prefix)

        ar_list         = htmlTagsContentList(
            uncommented_text,
            ["AR1", "AR2", "AR3", "AR4", "AR5"],
            min_length=5,
            comment_prefix=prefix,
        )
        all_tag         = getHtmlTagContent(uncommented_text, "ALL", comment_prefix=prefix)
        embeds          = insertStringToListItems(ar_list, all_tag)
        impact_wildcard = createImpactWildcard(embeds)

        # print(f"[FP EXECUTE] id={unique_id} all_expt_comments={all_expt_comments[:80]!r}")
        # print(f"[FP EXECUTE] id={unique_id} all_expt_areas={all_expt_areas[:80]!r}")
        # print(f"[FP EXECUTE] id={unique_id} ar_list={[v[:40] if v else None for v in ar_list]}")
        # print(f"[FP EXECUTE] id={unique_id} impact_wildcard={impact_wildcard[:120]!r}")
        # print(f"[FP EXECUTE] id={unique_id} done")

        return io.NodeOutput(all_expt_comments, all_expt_areas, embeds, impact_wildcard, negotives)


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
