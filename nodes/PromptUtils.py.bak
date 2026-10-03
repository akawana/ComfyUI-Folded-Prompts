"""
PromptUtils.py
==============
Utility functions for cleaning and formatting prompt text used in ComfyUI nodes.

Concept: Tag
------------
A tag is any sequence of characters separated by a comma or a newline, with
leading and trailing whitespace stripped.  A well-formed tag always ends with
", " (comma + space).  If a tag is terminated only by a newline (no trailing
comma), the comma + space must be appended.

Examples of raw tags and their canonical form:
    " blue_hair"           ->  "blue_hair, "
    "blue hair with white buns "  ->  "blue hair with white buns, "
    "upper teeth only\n"   ->  "upper teeth only, "
    "large areolae, "      ->  "large areolae, "   (already correct)
"""

import re
from typing import Optional


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _split_into_segments(text: str) -> list[tuple[str, str]]:
    """
    Split *text* into a list of (content, separator) pairs, where separator
    is either "," or "\\n" (the character that ended the segment) or "" for
    the very last segment.

    The split is done at commas and newlines; each segment keeps track of
    which delimiter closed it so we can decide whether to add a comma.
    """
    segments: list[tuple[str, str]] = []
    buf = ""
    for ch in text:
        if ch == ",":
            segments.append((buf, ","))
            buf = ""
        elif ch == "\n":
            segments.append((buf, "\n"))
            buf = ""
        else:
            buf += ch
    # trailing segment without a closing delimiter
    segments.append((buf, ""))
    return segments


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def formatTags(text: str) -> str:
    """
    Parse *text* into individual tags and return a reformatted version where
    every tag:

    * has its leading and trailing whitespace stripped,
    * ends with ", " (comma + space).

    Newline characters that separate tags are **preserved** in the output:
    each tag that was followed by a newline still ends on its own line.
    Tags that were separated only by commas remain on the same line.

    Empty segments (e.g. two consecutive commas, or a blank line) are
    preserved as-is so that intentional spacing in the source is not lost.

    Example
    -------
    Input::

        upper teeth only
        large areolae,   huge_breasts, blue eyes ,
        long hair, red hair

    Output::

        upper teeth only,
        large areolae, huge_breasts, blue eyes,
        long hair, red hair,
    """
    if not text:
        return text

    segments = _split_into_segments(text)
    output_parts: list[str] = []

    for raw_content, sep in segments:
        stripped = raw_content.strip()

        if not stripped:
            # Preserve the empty segment + its separator as blank space.
            if sep == "\n":
                output_parts.append("\n")
            elif sep == ",":
                # Two consecutive commas — keep one comma + space.
                output_parts.append(", ")
            # sep == "" means trailing empty content: nothing to add.
            continue

        # We have a real tag.  It must always end with ", ".
        tag_formatted = stripped + ", "

        if sep == "\n":
            # The tag was followed by a newline: keep it on its own line.
            output_parts.append(tag_formatted + "\n")
        elif sep == ",":
            # The tag was followed by a comma: inline, already ends with ", ".
            output_parts.append(tag_formatted)
        else:
            # Last segment (no separator).  Still needs the trailing ", ".
            output_parts.append(tag_formatted)

    result = "".join(output_parts)

    # Remove the very last trailing newline that _split_into_segments may
    # introduce if the original text ended with "\n", so we don't add an
    # extra blank line that wasn't there before.
    if not text.endswith("\n") and result.endswith("\n"):
        result = result[:-1]

    return result


def clearDoubleEmptyLines(text: str) -> str:
    """
    Collapse consecutive empty lines into a single empty line.

    A line is considered empty if it contains only whitespace (spaces, tabs)
    or nothing at all.  Any run of two or more such lines is replaced by a
    single completely empty line (no spaces).

    Example
    -------
    Input::

        hyperpigmentation,
            
          
         
        armpits_hyperpigmentation,

    Output::

        hyperpigmentation,

        armpits_hyperpigmentation,
    """
    if not text:
        return text
    return re.sub(r'(\n[ \t]*){2,}\n', '\n\n', text)


def clearHtmlLikeTags(text: str, *tags: str) -> str:
    """
    Remove HTML-like opening and closing tags from *text*, leaving the content
    inside them untouched.

    Supported closing forms
    -----------------------
    * Named:  ``</AR1>``, ``</ALL>``, etc.
    * Short:  ``</>``  (closes any open tag)

    Parameters
    ----------
    text : str
        Source text that may contain HTML-like tags.
    *tags : str
        Optional whitelist of opening tags to remove, e.g.
        ``"<AR1>"``, ``"<AR2>"``, ``"<ALL>"``.
        Tag names are matched **case-insensitively**.
        If no tags are given, *every* tag matching ``<...>`` / ``</...>`` /
        ``</>`` is removed.

    Returns
    -------
    str
        Text with the specified (or all) tags stripped; inner content kept.

    Examples
    --------
    >>> clearHtmlLikeTags("<AR1> curvy, fat, </>" )
    ' curvy, fat, '

    >>> clearHtmlLikeTags("<all> red hair\\norange_hair, \\n</all>")
    ' red hair\\norange_hair, \\n'

    >>> clearHtmlLikeTags("<AR1> curvy </> <AR2> slim </>", "<AR1>")
    ' curvy  <AR2> slim </>'
    """
    if not text:
        return text

    if tags:
        # Build a pattern that matches only the requested opening tags
        # and their corresponding closing tags (named or short </>).
        names = [re.escape(t.strip("<>")) for t in tags]
        names_pattern = "|".join(names)
        pattern = re.compile(
            r"<(?:" + names_pattern + r")>"          # opening tags
            r"|</(?:" + names_pattern + r")>"         # named closing tags
            r"|</>",                                  # short closing tag
            re.IGNORECASE,
        )
    else:
        # Remove any tag: <word...>, </word...>, or </>
        pattern = re.compile(r"</?\w*>", re.IGNORECASE)

    return pattern.sub("", text)


def clearHtmlLikeTagsWithContent(text: str, *tags: str) -> str:
    """
    Remove HTML-like tags **together with all content between them** from
    *text*.

    Supported closing forms
    -----------------------
    * Named:  ``</AR1>``, ``</ALL>``, etc.
    * Short:  ``</>``  (closes the nearest open tag)

    Parameters
    ----------
    text : str
        Source text that may contain HTML-like tags with content to discard.
    *tags : str
        Optional whitelist of opening tags whose blocks should be removed,
        e.g. ``"<AR1>"``, ``"<ALL>"``.
        Tag names are matched **case-insensitively**.
        If no tags are given, every block matching ``<tag>...</tag>`` or
        ``<tag>...</>`` is removed.

    Returns
    -------
    str
        Text with the specified (or all) tag blocks removed entirely.

    Examples
    --------
    >>> clearHtmlLikeTagsWithContent("<AR1> curvy, fat, </>  outside")
    '  outside'

    >>> clearHtmlLikeTagsWithContent(
    ...     "<AR1> a </> <AR2> b </> keep",
    ...     "<AR1>"
    ... )
    ' <AR2> b </> keep'
    """
    if not text:
        return text

    if tags:
        names = [re.escape(t.strip("<>")) for t in tags]
        names_pattern = "|".join(names)
        # Match <TAG> ... </TAG> or <TAG> ... </>
        pattern = re.compile(
            r"<(?:" + names_pattern + r")>"           # opening tag
            r".*?"                                     # content (non-greedy)
            r"(?:</(?:" + names_pattern + r")>|</>)",  # named or short close
            re.IGNORECASE | re.DOTALL,
        )
    else:
        pattern = re.compile(
            r"<(\w+)>.*?(?:</\1>|</>)",
            re.IGNORECASE | re.DOTALL,
        )

    return pattern.sub("", text)


def clearLineBreaks(text: str) -> str:
    """
    Remove all newline characters from *text*, returning a single flat string.

    Both ``\\n`` and ``\\r\\n`` (Windows) line endings are removed.

    Example
    -------
    >>> clearLineBreaks("red hair\\nblue eyes\\n")
    'red hairblue eyes'
    """
    if not text:
        return text
    return text.replace("\r\n", "").replace("\r", "").replace("\n", "")


def htmlTagsContentList(
    text: str,
    tags: list[str] | set[str],
    min_length: int | None = None,
    comment_prefix: str = "//",
) -> list[str | None]:
    """
    Extract and clean the inner content of HTML-like tags, merging all
    occurrences of the same tag name into one string.

    For each tag name the collected content is processed with:
    ``clearCommentedLines → clearLineBreaks → formatTags``

    Parameters
    ----------
    text : str
        Source text containing HTML-like tagged blocks.
    tags : list or set of str
        Tag names to extract, e.g. ``["AR1", "AR2"]`` or ``{"AR1", "AR2"}``.
        Names are matched case-insensitively and may be given with or without
        angle brackets (``"AR1"`` and ``"<AR1>"`` are both accepted).
    min_length : int or None
        Minimum length of the returned list.  Slots beyond the number of
        found tags are filled with ``None``.  If ``None``, the list length
        equals the number of tags requested.
    comment_prefix : str
        Passed through to ``clearCommentedLines``.  Defaults to ``"//"``.

    Returns
    -------
    list[str | None]
        One entry per requested tag (in the order given).  Each entry is the
        cleaned, merged content string, or ``None`` if that tag had no content.

    Example
    -------
    Input text::

        <AR1>orange_hair, medium_hair,</>
        <AR1>
        curvy, fat,
        </>
        <AR2>armpits_hyperpigmentation
        </>

    ``htmlTagsContentList(text, ["AR1", "AR2"], min_length=5)`` returns::

        [
            "orange_hair, medium_hair, curvy, fat, ",
            "armpits_hyperpigmentation, ",
            None,
            None,
            None,
        ]
    """
    # Normalise tag names — strip angle brackets if present.
    normalised = [t.strip("<>").strip() for t in tags]

    result: list[str | None] = []

    for name in normalised:
        # Build a pattern for <NAME>...</NAME> or <NAME>...</>
        name_esc = re.escape(name)
        pattern = re.compile(
            r"<" + name_esc + r">"
            r"(.*?)"
            r"(?:</" + name_esc + r">|</>)",
            re.IGNORECASE | re.DOTALL,
        )
        chunks: list[str] = []
        for m in pattern.finditer(text):
            raw = m.group(1) or ""
            cleaned = clearCommentedLines(raw, comment_prefix)
            cleaned = clearLineBreaks(cleaned)
            cleaned = formatTags(cleaned)
            if cleaned:
                chunks.append(cleaned)

        if chunks:
            result.append("".join(chunks))
        else:
            result.append(None)

    # Pad to min_length with None if requested.
    if min_length is not None:
        while len(result) < min_length:
            result.append(None)

    return result


def getHtmlTagContent(
    text: str,
    tag: str,
    comment_prefix: str = "//",
) -> str:
    """
    Return the cleaned inner content of all occurrences of *tag* merged into
    one flat string.

    Processing pipeline per occurrence:
    ``clearCommentedLines → clearLineBreaks → formatTags``

    Parameters
    ----------
    text : str
        Source text containing the tagged block(s).
    tag : str
        Tag name to extract, e.g. ``"AR1"`` or ``"ALL"``.
        May be given with or without angle brackets.
    comment_prefix : str
        Passed through to ``clearCommentedLines``.  Defaults to ``"//"``.

    Returns
    -------
    str
        Cleaned, merged content of all matching blocks, or ``""`` if the tag
        is not found.

    Example
    -------
    Input::

        <AR1>
        curvy, fat, deep_skin, wide_hips,
        narrow_waist,
        </>

    ``getHtmlTagContent(text, "AR1")`` returns::

        "curvy, fat, deep_skin, wide_hips, narrow_waist, "
    """
    name = tag.strip("<>").strip()
    name_esc = re.escape(name)
    pattern = re.compile(
        r"<" + name_esc + r">"
        r"(.*?)"
        r"(?:</" + name_esc + r">|</>)",
        re.IGNORECASE | re.DOTALL,
    )
    chunks: list[str] = []
    for m in pattern.finditer(text):
        raw = m.group(1) or ""
        cleaned = clearCommentedLines(raw, comment_prefix)
        cleaned = clearLineBreaks(cleaned)
        cleaned = formatTags(cleaned)
        if cleaned:
            chunks.append(cleaned)
    return "".join(chunks)


def insertStringToListItems(
    items: list[str | None],
    string: str,
) -> list[str | None]:
    """
    Prepend *string* to every non-``None`` item in *items*.

    ``None`` entries are passed through unchanged.  If *string* is empty,
    the list is returned unchanged.

    Parameters
    ----------
    items : list[str | None]
        Source list, typically the output of ``htmlTagsContentList``.
    string : str
        String to prepend to each non-None item.

    Returns
    -------
    list[str | None]
        New list with *string* prepended to every non-None entry.

    Example
    -------
    >>> insertStringToListItems(["red hair, ", None, "blue eyes, "], "1girl, ")
    ["1girl, red hair, ", None, "1girl, blue eyes, "]
    """
    if not string:
        return items
    return [
        string + item if item is not None else string
        for item in items
    ]


def createImpactWildcard(items: list[str | None]) -> str:
    """
    Build an Impact Pack wildcard string from a list of prompt strings.

    The output always starts with ``[LAB]`` on its own line, followed by one
    line per non-``None`` item in the format ``[ARx]<content>``, where *x* is
    the 1-based index of the item in the list (regardless of whether earlier
    items were ``None``).

    ``None`` items are skipped — no ``[ARx]`` line is emitted for them.

    Parameters
    ----------
    items : list[str | None]
        Typically the output of ``insertStringToListItems`` or
        ``htmlTagsContentList``.  Up to 5 items are expected (AR1–AR5),
        but the function works with any length.

    Returns
    -------
    str
        Multi-line wildcard string ready for the Impact Pack node.

    Example
    -------
    >>> createImpactWildcard(["red hair, ", None, "blue eyes, ", None, None])
    '[LAB]\\n[AR1]red hair, \\n[AR3]blue eyes, '
    """
    lines = ["[LAB]"]
    for i, item in enumerate(items, start=1):
        if item is not None:
            lines.append(f"[AR{i}]{item}")
    return "\n".join(lines)


def clearCommentedLines(text: str, comment_prefix: str = "//") -> str:
    """
    Remove every line that starts with *comment_prefix* (after stripping
    leading whitespace from the line).

    The match is prefix-only: a space after the prefix is optional and does
    not change whether the line is treated as a comment.  Only full-line
    comments are removed; inline comments (prefix in the middle of a line)
    are left untouched.

    Parameters
    ----------
    text : str
        The raw prompt text, potentially containing commented-out lines.
    comment_prefix : str
        The string that marks a commented line.  Defaults to ``"//"`` which
        is the default value used by the *keybinding_extra* ComfyUI
        extension (setting key ``keybinding_extra.comment_prefix``).

    Returns
    -------
    str
        The text with all commented lines removed.  The newline structure of
        the remaining lines is preserved unchanged.

    Example
    -------
    Input (prefix = "//")::

        //upper teeth only
        // large areolae,   huge_breasts, blue eyes ,
        long hair, red hair

    Output::

        long hair, red hair
    """
    if not text or not comment_prefix:
        return text

    lines = text.splitlines(keepends=True)
    kept: list[str] = []
    for line in lines:
        # Strip only leading whitespace for the prefix check.
        stripped = line.lstrip()
        if stripped.startswith(comment_prefix):
            continue
        kept.append(line)

    return "".join(kept)
