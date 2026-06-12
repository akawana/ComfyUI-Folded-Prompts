import os
import json
import traceback

from comfy_api.latest import ComfyExtension, io


def _merge_before(before_text: str, main_text: str) -> str:
    before_text = before_text or ""
    main_text   = main_text   or ""
    if before_text and main_text:
        return before_text.rstrip("\n") + "\n" + main_text.lstrip("\n")
    return before_text or main_text


def _build_output_text(pf_json: str, text: str, before_text: str) -> str:
    if not pf_json or not pf_json.strip():
        return _merge_before(before_text, text or "")

    try:
        tree = json.loads(pf_json)
    except Exception as e:
        print(f"[FPFoldedPrompts] Failed to parse pf_json: {e}")
        return _merge_before(before_text, text or "")

    try:
        result_lines = []

        def walk(items_list, parent_area="ALL"):
            for item in items_list:
                itype    = item.get("type")
                area     = item.get("area", "ALL") or "ALL"
                current_area = parent_area if parent_area != "ALL" else area

                if itype == "folder":
                    walk(item.get("children") or [], current_area)
                elif itype == "line":
                    if not bool(item.get("enabled", True)):
                        continue
                    raw_line = item.get("text", "")
                    eff_area = current_area
                    if eff_area and eff_area != "ALL":
                        result_lines.append(f"<{eff_area}>{raw_line}</>")
                    else:
                        result_lines.append(raw_line)

        walk(tree.get("items") or [], parent_area="ALL")
        final_text = "\n".join(result_lines)
    except Exception as e:
        print(f"[FPFoldedPrompts] Error building output: {e}")
        traceback.print_exc()
        final_text = text or ""

    return _merge_before(before_text, final_text)


class FPFoldedPrompts(io.ComfyNode):

    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="FPFoldedPrompts",
            display_name="FP Folded Prompts",
            category="AK/Folded Prompts",
            description=(
                "Builds prompt text from a collapsible folder tree. "
                "All UI is implemented in JS."
            ),
            inputs=[
                io.String.Input(
                    "text",
                    default="",
                    multiline=True,
                ),
                io.String.Input(
                    "pf_json",
                    default="",
                    multiline=False,
                    optional=True,
                    tooltip="Internal: tree JSON. Managed by JS.",
                ),
                io.String.Input(
                    "pf_node_id",
                    default="",
                    multiline=False,
                    optional=True,
                    tooltip="Internal: node id. Managed by JS.",
                ),
                io.String.Input(
                    "before_text",
                    default="",
                    multiline=True,
                    force_input=True,
                    optional=True,
                ),
            ],
            outputs=[
                io.String.Output(display_name="text"),
            ],
            hidden=[io.Hidden.unique_id],
        )

    @classmethod
    def execute(
        cls,
        text: str = "",
        pf_json: str = "",
        pf_node_id: str = "",
        before_text: str = "",
    ) -> io.NodeOutput:
        unique_id = str(cls.hidden.unique_id) if cls.hidden else ""

        # Save pf_json to file if node_id present
        if pf_json and pf_node_id:
            try:
                data_dir = os.path.join(os.path.dirname(__file__), "..", "pf_data")
                os.makedirs(data_dir, exist_ok=True)
                filename = os.path.join(data_dir, f"pf_{pf_node_id}.json")
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(pf_json)
            except Exception as e:
                print(f"[FPFoldedPrompts] Failed to save JSON: {e}")

        result = _build_output_text(pf_json, text, before_text)
        return io.NodeOutput(result)


class FPFoldedPromptsExtension(ComfyExtension):
    async def get_node_list(self) -> list[type[io.ComfyNode]]:
        return [FPFoldedPrompts]


async def comfy_entrypoint() -> FPFoldedPromptsExtension:
    return FPFoldedPromptsExtension()


NODE_CLASS_MAPPINGS = {
    "FPFoldedPrompts": FPFoldedPrompts,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "FPFoldedPrompts": "FP Folded Prompts",
}
