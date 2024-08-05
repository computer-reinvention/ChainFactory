import uuid
import json
import pprint
import traceback

import json
from typing import List, Dict, Literal, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from langchain.pydantic_v1 import BaseModel, Field
from langchain_community.vectorstores.faiss import FAISS
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.chains import LLMChain
from langchain.prompts import (
    MaxMarginalRelevanceExampleSelector,
    SemanticSimilarityExampleSelector,
    FewShotPromptTemplate,
    PromptTemplate,
)
from langchain.schema.runnable import RunnableSerializable

situations = [
    "Mavy, recommend some morning (my time) slots for next week please.",
    "Mavy, could you recommend some times for next week (Tuesday, Wednesday, or Thursday) for me, Pamela, Aaron, and Roger to meet?",
    "Mavy, could you find some available time slots next week for a one-hour meeting between 9 AM and 12 PM my time?"
    "Mavy, please recommend two possible times for a 45-minute meeting with John, Sarah, and Mike next Wednesday and Friday afternoon my time",
    "Mavy, I need a 30-minute slot for a meeting with the marketing team on Tuesday or Thursday next week between 2 PM and 4 PM my time. The participants are Anna, Jake, and myself",
    "Mavy, can you suggest some time slots for a 90-minute meeting next Wednesday morning with the finance team, including Emily, David, and Susan?",
    "Mavy, please find a 45-minute slot next Thursday for a meeting with the development team. The times should be convenient for both our time zones (PST and CET).",
    "Mavy, recommend a 60-minute slot next Tuesday or Wednesday that works for both my schedule and Jane's schedule (she's in EST).",
    "Mavy, I need a 30-minute meeting slot for next week Monday or Tuesday between 1 PM and 3 PM my time, ensuring no overlap with existing meetings.",
    "Mavy, suggest a few time slots for a 60-minute meeting next week with the sales team, avoiding the 2 PM to 4 PM window on Thursday",
    "Mavy, find a 90-minute slot for a meeting with the leadership team in the second week of October. The meeting should be between 10 AM and 1 PM my time.",
    "Mavy, could you recommend some time slots for a 60-minute meeting with the product team during the second week of October, avoiding any overlapping time blocks?",
    "Mavy, I need a 30-minute slot for a meeting with Alex, Chris, and Jordan next week. Alex is available in the mornings only, and Chris has a meeting on Wednesday afternoon.",
    "Mavy, can you find a 45-minute slot for a meeting with the design team (Laura, Matt, and myself) next Thursday or Friday, considering Matt is in EST and has a 3-hour block blocked off each afternoon?",
    "Mavy, can you look at the time blocks sent by Sam in ET and find a 30-minute slot within those blocks for a meeting with the HR team next week?",
    "Mavy, review the time blocks shared by Alex (ET) and suggest a 60-minute slot for a meeting with the IT team next Tuesday or Wednesday.",
    "Mavy, I need a 45-minute meeting slot next week that works for me, Daniel, and Priya. Daniel is available on Monday and Wednesday mornings, and Priya can do Tuesday and Thursday afternoons. Please avoid overlapping with my existing meetings.",
    "Mavy, suggest a few 30-minute slots for a meeting with the core team next week, considering I'm in PST, Rachel is in EST, and Thomas is in CET. Ensure the slots do not overlap with any of our current meetings.",
]

tz_situations = [
    "Mavy, recommend some morning slots for next week in my time zone (Central European Time).",
    "Mavy, could you recommend some times for next week (Tuesday, Wednesday, or Thursday) for me, Pamela, Aaron, and Roger to meet? Please consider London time for scheduling.",
    "Mavy, could you find some available time slots next week for a one-hour meeting between 9 AM and 12 PM Tokyo time?",
    "Mavy, please recommend two possible times for a 45-minute meeting with John, Sarah, and Mike next Wednesday and Friday afternoon, considering Eastern Standard Time.",
    "Mavy, I need a 30-minute slot for a meeting with the marketing team on Tuesday or Thursday next week between 2 PM and 4 PM Pacific Standard Time. The participants are Anna, Jake, and myself.",
    "Mavy, can you suggest some time slots for a 90-minute meeting next Wednesday morning with the finance team, including Emily, David, and Susan, keeping in mind Singapore time?",
    "Mavy, please find a 45-minute slot next Thursday for a meeting with the development team. Consider both PST (USA) and CET (Europe) for timing.",
    "Mavy, recommend a 60-minute slot next Tuesday or Wednesday that works for both my schedule and Jane's schedule, taking into account that she's in New York.",
    "Mavy, I need a 30-minute meeting slot for next week Monday or Tuesday between 1 PM and 3 PM Sydney time, ensuring no overlap with existing meetings.",
    "Mavy, suggest a few time slots for a 60-minute meeting next week with the sales team, avoiding the 2 PM to 4 PM window on Thursday in Central European Summer Time.",
    "Mavy, find a 90-minute slot for a meeting with the leadership team in the second week of October, scheduled between 10 AM and 1 PM India Standard Time.",
    "Mavy, could you recommend some time slots for a 60-minute meeting with the product team during the second week of October, considering Central European Time and avoiding any overlapping time blocks?",
    "Mavy, I need a 30-minute slot for a meeting with Alex, Chris, and Jordan next week. Alex is available in the mornings only, and Chris has a meeting on Wednesday afternoon, considering Eastern Standard Time.",
    "Mavy, can you find a 45-minute slot for a meeting with the design team (Laura, Matt, and myself) next Thursday or Friday, considering that Matt is in New York and has a 3-hour block blocked off each afternoon?",
    "Mavy, can you look at the time blocks sent by Sam in Eastern Time and find a 30-minute slot within those blocks for a meeting with the HR team next week?",
    "Mavy, review the time blocks shared by Alex in Eastern Time and suggest a 60-minute slot for a meeting with the IT team next Tuesday or Wednesday.",
    "Mavy, I need a 45-minute meeting slot next week that works for me, Daniel, and Priya. Daniel is available on Monday and Wednesday mornings, and Priya can do Tuesday and Thursday afternoons. Please consider IST for timing and avoid overlapping with my existing meetings.",
    "Mavy, suggest a few 30-minute slots for a meeting with the core team next week, considering I'm in Los Angeles, Rachel is in New York, and Thomas is in Berlin. Ensure the slots do not overlap with any of our current meetings.",
]


def convert_to_jsonl(
    filename: str,
    input_key: str = "input",
    output_key: str = "output",
) -> str:
    """
    Convert a JSON file to a JSONL file.
    """
    with open(filename, "r") as f:
        data = json.load(f)

    outfile = filename.replace(".json", ".jsonl")

    with open(outfile, "w") as f:
        for item in data:
            messages = [
                {
                    "role": "system",
                    "content": """Instructions:
- Analyze the input and extract all timezones
- Identify and list all explicit timezone references mentioned in the email.
- Convert named timezones to their respective abbreviations.
""",
                },
                {"role": "user", "content": f"""Input: {item[input_key]}"""},
                {
                    "role": "assistant",
                    "content": f"""{item[output_key]}""",
                },
            ]

            f.write(
                json.dumps(
                    {
                        "messages": messages,
                    }
                )
                + "\n"
            )

    return outfile


def random_situation_getter_factory(situations: list[str]) -> Callable:
    """
    Generate an example for a randomly chosen situation
    """

    def _inner():
        nonlocal situations

        return situations.pop()

    return _inner


def load_from_json(filename: str, keyname: str | None = None) -> List[Dict]:
    """
    Load examples from a JSON file, this is a one time load initially.
    """
    with open(filename, "r") as f:
        return json.load(f)


def create_example_selector(
    examples: List[Dict],
    selector_type: Literal["semantic", "mmr"] = "semantic",
    k: int = 4,
    fetch_k: int = 20,
) -> SemanticSimilarityExampleSelector | MaxMarginalRelevanceExampleSelector:
    """
    Create an example selector from a list of incremental examples.

    Args:
    examples: List of example dictionaries
    selector_type: Type of selector to use ("semantic" or "mmr")
    k: Number of examples to select
    fetch_k: Number of examples to fetch (only used for MMR)

    Returns:
    An instance of SemanticSimilarityExampleSelector or MaxMarginalRelevanceExampleSelector
    """
    embeddings = OpenAIEmbeddings()

    if selector_type == "semantic":
        return SemanticSimilarityExampleSelector.from_examples(
            examples=examples,
            embeddings=embeddings,
            vectorstore_cls=FAISS,
            k=k,
            input_keys=["input"],
        )
    elif selector_type == "mmr":
        return MaxMarginalRelevanceExampleSelector.from_examples(
            examples=examples,
            embeddings=embeddings,
            vectorstore_cls=FAISS,
            k=k,
            fetch_k=fetch_k,
            input_keys=["input"],
        )
    else:
        raise ValueError("Invalid selector_type. Choose 'semantic' or 'mmr'.")


def create_chain(
    prompt: FewShotPromptTemplate, model: ChatOpenAI
) -> RunnableSerializable:
    """
    This function creates a chain from the given prompt, model, and example selector.
    """
    return prompt | model


def create_prompt(
    selector: SemanticSimilarityExampleSelector | MaxMarginalRelevanceExampleSelector,
) -> FewShotPromptTemplate:
    """
    This function creates a prompt from the initial examples.
    """
    prefix = """You are an expert synthetic data creation system.
Given some examples, you must create new datum that is distinct from all the given example data but tackles the same problem.

The current example needs to be similar to the following, but it must be distinct from all the examples.

Input: {input}
"""

    return FewShotPromptTemplate(
        example_selector=selector,
        example_prompt=PromptTemplate.from_template(
            "Input: {input}\nOutput: {output}\n"
        ),
        prefix=prefix,
        suffix="Generate the example_input, example_output pairs. Go!",
        input_variables=["input"],
    )


situation_getter = random_situation_getter_factory(tz_situations)


def generate_examples(n: int, chain: LLMChain) -> List[BaseModel]:
    """
    Generate n examples from a chain
    """
    situation = situation_getter()
    with ThreadPoolExecutor() as executor:
        futures = [
            executor.submit(chain.invoke, {"input": situation}) for _ in range(n)
        ]
        return [future.result() for future in as_completed(futures)]


def run_reject_accept_loop(examples: list) -> tuple[list, list]:
    """
    Runs the reject-accept loop on the given examples.
    """
    accepted_examples = []
    rejected_examples = []

    for example in examples:
        print("=" * 14)
        pprint.pprint(example)
        print("=" * 14)

        accept = input("Accept? (y/n): ")

        if "y" in accept.lower() or accept.lower() == "":
            accepted_examples.append(
                {
                    "input": example["example_input"],
                    "output": example["example_output"],
                }
            )
        else:
            rejected_examples.append(
                {
                    "input": example["example_input"],
                    "output": example["example_output"],
                }
            )

    return accepted_examples, rejected_examples


def dump_examples(filename: str, examples: list[dict]):
    """
    Dumps the examples to a file.
    """
    with open(filename, "w") as file:
        json.dump(examples, file)


def print_stats(good_examples: list[dict], bad_examples: list[dict], counter: int):
    """
    Prints the statistics about the current set.
    """
    print(
        f"""

===========================
Total Iterations: {counter}
Total Good Examples: {len(good_examples)}
Total Bad Examples: {len(bad_examples)}
Total Accuracy: {len(good_examples) / (len(good_examples) + len(bad_examples))}
===========================

"""
    )


def driver(chunksize: int):
    """
    This function executes the main loop of the driver.
    """
    session_id = uuid.uuid4().hex.split("-")[0]
    initial_examples = load_from_json("te_initial_examples.json")

    class _output(BaseModel):
        example_input: str = Field(description="The input text of the example.")
        example_output: list[str] = Field(
            description="The output part list of timezones."
        )

    model = ChatOpenAI(temperature=0.95, model="gpt-4").with_structured_output(_output)

    counter = 0
    good_examples = []
    bad_examples = []
    while True:
        try:
            counter += 1
            selector = create_example_selector(initial_examples + good_examples)
            prompt = create_prompt(selector)
            chain = create_chain(prompt, model)
            examples = generate_examples(chunksize, chain)
            examples = [example.dict() for example in examples]

            good, bad = run_reject_accept_loop(examples)

            good_examples.extend(good)
            bad_examples.extend(bad)

            dump_examples(f"{session_id}_examples_{counter}.json", examples)
            dump_examples(f"{session_id}_good_examples_{counter}.json", good_examples)
            dump_examples(f"{session_id}_bad_examples_{counter}.json", good_examples)

        except KeyboardInterrupt:
            break
        except Exception:
            traceback.print_exc()
        finally:
            print_stats(good_examples, bad_examples, counter)


if __name__ == "__main__":
    print(convert_to_jsonl("d3948bda268e495a8f308ad4d0d66418_good_examples_5.json"))
