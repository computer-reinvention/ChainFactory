from pprint import pprint
from typing import Any
from chainfactory import Engine, EngineConfig
from chainfactory.core.tools import ToolContext


config = EngineConfig(pause_between_executions=True)


@config.register_tool
def display_classification(ctx: ToolContext):
    print(ctx.input)
    classification = ctx.input
    formatted_output = (
        f"Label: {classification.label}\n"
        f"Text: {classification.text}\n"
        f"Snippet: {classification.snippet}\n"
        f"Confidence: {classification.confidence}"
    )
    print("=============")
    print(formatted_output)
    print("=============")
    ctx.output.display = formatted_output


@config.register_tool
def confidence_filter(ctx: ToolContext) -> dict[str, Any]:
    classification = ctx.input.classification
    confidence_threshold = ctx.kwargs.get("confidence_threshold", "medium")
    confidence_levels = ["none", "low", "medium", "high", "extreme"]
    if confidence_levels.index(classification.confidence) >= confidence_levels.index(
        confidence_threshold
    ):
        return ctx.get_output()
    else:
        raise ValueError("Confidence threshold not met")


@config.register_tool
def take_action(ctx: ToolContext):
    classification = ctx.input.classification
    if classification.label == "meeting":
        ctx.output.action = "Schedule a meeting"
    elif classification.label == "email":
        ctx.output.action = "Draft an email"
    else:
        ctx.output.action = "No action required"

    return ctx


@config.register_tool
def logdump(ctx: ToolContext) -> dict[str, Any]:
    import logging

    logger = logging.getLogger(__name__)
    logger.info("Input: %s", ctx.kwargs)
    logger.info("Output: %s", ctx.get_output())

    return ctx.get_output()


def main():
    classify = Engine.from_file("examples/classify.fctr", config=config)
    classify(text="I am a robot.", labels=["Bot", "Human"])


if __name__ == "__main__":
    main()
