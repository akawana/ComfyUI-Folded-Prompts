from comfy_execution.graph import ExecutionBlocker
from comfy_api.latest import ComfyExtension, io


class ExecutionBlockerBreaker(io.ComfyNode):

    _prev_values: dict = {}

    @classmethod
    def define_schema(cls) -> io.Schema:
        template = io.MatchType.Template("value")
        return io.Schema(
            node_id="ExecutionBlockerBreaker",
            display_name="Execution Blocker Breaker",
            category="AK/Utils",
            description=(
                "Breaks ExecutionBlocker propagation at merge points. "
                "If the input is an ExecutionBlocker, returns the last known real value. "
                "If the input is a real value, caches it and passes it through."
            ),
            inputs=[
                io.MatchType.Input("value", template=template, lazy=True),
            ],
            outputs=[
                io.MatchType.Output(template=template, display_name="value"),
            ],
            hidden=[io.Hidden.unique_id],
        )

    @classmethod
    def check_lazy_status(cls, value=None, **kwargs) -> list[str]:
        if value is None:
            return ["value"]
        return []

    @classmethod
    def execute(cls, value=None, **kwargs) -> io.NodeOutput:
        unique_id = str(cls.hidden.unique_id) if cls.hidden else ""
        if value is None or isinstance(value, ExecutionBlocker):
            cached = cls._prev_values.get(unique_id)
            print(f"[ExecutionBlockerBreaker] id={unique_id} got blocker → returning cached type={type(cached).__name__}")
            return io.NodeOutput(cached)
        cls._prev_values[unique_id] = value
        print(f"[ExecutionBlockerBreaker] id={unique_id} got real value type={type(value).__name__} → passing through")
        return io.NodeOutput(value)


class ExecutionBlockerBreakerExtension(ComfyExtension):
    async def get_node_list(self) -> list[type[io.ComfyNode]]:
        return [ExecutionBlockerBreaker]


async def comfy_entrypoint() -> ExecutionBlockerBreakerExtension:
    return ExecutionBlockerBreakerExtension()


NODE_CLASS_MAPPINGS = {
    "ExecutionBlockerBreaker": ExecutionBlockerBreaker,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ExecutionBlockerBreaker": "Execution Blocker Breaker",
}
