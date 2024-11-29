import json
from chainfactory import Engine, EngineConfig

engine_config = EngineConfig()

# ============================================================================ #
#                                                                              #
#                             Constants et. al.                                #
#                                                                              #
# ============================================================================ #

MOCK_EMAIL = "Hi John, Hope you're doing well! I'm reaching out to let you know that I will be in your city next week. Let's catch up over coffee. @Mavy EA can arrange. Best, Jane jane.doe@email.com (555) 123-4567"

MOCK_HANDLERS = {
    "confirm_suggested_time_slot": lambda **kwargs: {
        **kwargs,
        "action": "confirm_suggested_time_slot",
    },
    "reschedule_existing_meeting": lambda **kwargs: {
        **kwargs,
        "action": "reschedule_existing_meeting",
    },
    "cancel_existing_meeting": lambda **kwargs: {
        **kwargs,
        "action": "cancel_existing_meeting",
    },
    "suggest_time_slots_for_meeting": lambda **kwargs: {
        **kwargs,
        "action": "suggest_time_slots_for_meeting",
    },
}

CONFIDENCE_LEVELS = {
    "extreme": 0,
    "high": 1,
    "medium": 2,
    "low": 3,
    "none": 4,
}


class LowConfidenceException(Exception):
    pass


@engine_config.register_tool  # brand new decorator
def display_classification(**kwargs):
    classification = kwargs["classification"]
    print("\n\n======= Classification =======")
    print(
        f"Action: {classification['label']},\nConfidence: {classification['confidence']},\nSnippet: {classification['snippet']}"
    )
    print("===============================")

    return kwargs


@engine_config.register_tool  # brand new decorator
def confidence_filter(**kwargs):
    classification = kwargs["classification"]
    if CONFIDENCE_LEVELS[classification["confidence"]] >= 2:
        raise LowConfidenceException(
            f"Need higher confidence to continue taking action for {classification['label']}."
        )

    return kwargs


# ============================================================================ #
#                                                                              #
#                             Business Logic                                   #
#                                                                              #
# ============================================================================ #


@engine_config.register_tool  # brand new decorator
def take_action(**kwargs):
    classification = kwargs["classification"]
    res = MOCK_HANDLERS[classification["label"]](classification=classification)
    kwargs.update(res)
    return kwargs


@engine_config.register_tool
def logdump(**kwargs):
    print("========== LOGDUMP ============")
    print(kwargs)
    print("===============================")
    with open("logdump.json", "w") as f:
        json.dump(kwargs, f)

    kwargs.update({"logdump": True})
    return kwargs


classification_engine = Engine.from_file("examples/classify.fctr", config=engine_config)

if __name__ == "__main__":
    classification_engine(text=MOCK_EMAIL, labels=list(MOCK_HANDLERS.keys()))
