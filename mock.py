from pprint import pprint
from chainfactory import Engine
from chainfactory.core.engine.chainfactory_engine import ChainFactoryEngineConfig
from langchain.globals import set_debug, set_verbose

set_debug(False)
set_verbose(False)


def haiku_and_review_sequential(topic="Python", num=2):
    """
    Demonstrates how to create a chain with 2 steps both of which run sequentially.

    <input>           ------------------------- the initial values. (topic, num in this case)
        |
    [haiku-generator] ------------------------- (generate `num` haiku in 1 inference)
        |
    (filter)          ------------------------- output is filtered to only retain relevant fields. sequential -> sequential linking.
        |
    [haiku-critic]    ------------------------- (generate `num` reviews in 1 inference)
        |
    <output>          ------------------------- the output is a haiku-critic.out instance

    Note: Filtering makes sure that only the input_variables of the subsequent chain are retained from the output of the previous chain.

    Args:
        topic (str, optional): The topic of the haiku. Defaults to "Python".
        num (int, optional): The number of haikus to generate. Defaults to 2.
    """
    haiku_review_engine = Engine.from_file("examples/haiku_generate_review.fctr")
    res = haiku_review_engine(topic=topic, num=num)

    for rev in res.reviews:
        print("Haiku:")
        print(rev.haiku)
        print("Review:")
        print(rev.review)
        print("\n")


def haiku_and_review_parallel(topic="Python", num=2):
    """
    Demonstrates how to create a chain with 2 steps one of which runs parallely.

    <input>           ------------------------- the initial values. (topic, num in this case)
        |
    [haiku-generator] ------------------------- (generate `num` haiku in 1 inference)
        |
    (filter)
    (split)           ------------------------- output is split `num` inputs for next step. sequential -> parallel linking.
        |
    [haiku-critic]    ------------------------- parallel (`num` inferences simultaneously in threadpool)
        |
    <output>          ------------------------- the output is a list of haiku-critic.out model instances

    Note: Splitting means creating `num` separate inputs that will be passed to `num` simultaneous instances of the subsequent chain. Filtering is automatically applied.

    Args:
        topic (str, optional): The topic of the haiku. Defaults to "Python".
        num (int, optional): The number of haikus to generate. Defaults to 2.
    """
    haiku_review_engine = Engine.from_file(
        "examples/haiku_generate_review_parallel.fctr"
    )
    res = haiku_review_engine(topic=topic, num=num)

    for item in res:
        print("Haiku:")
        print(item.haiku)
        print("Review:")
        print(item.review)
        print("\n")


def haiku_generate_review_validate(topic="Python", num=2):
    """
    Demonstrates how to create a chain with 3 steps and these types of links:

    <input>           ------------------------- the initial values. (topic, num in this case)
      |
    [haiku-generator] ------------------------- (generate `num` haiku in 1 inference)
      |
    (split)           ------------------------- output split into `num` inputs for next step. sequential -> parallel linking.
      |
    [haiku-critic]    ------------------------- parallel (`num` inferences simultaneously in threadpool)
      |
    (map)             ------------------------- output elements mapped into inputs for next step. parallel -> parallel linking.
      |
    [validator]       ------------------------- parallel (`num` inferences simultaneously in threadpool)
      |
    <output>          ------------------------- the output is a list of validator.out model instances

    Note: Mapping is a slightly complex form of filtering. It is applied on all elements of previous chain's output at once.

    Args:
        topic (str, optional): The topic of the haiku. Defaults to "Python".
        num (int, optional): The number of haikus to generate. Defaults to 2.
    """
    haiku_review_engine = Engine.from_file(
        "examples/haiku_generate_review_validate.fctr"
    )

    res = haiku_review_engine(topic=topic, num=num)

    for item in res:
        print("==================")
        print("Haiku:")
        print(item.haiku)
        print("\n")
        print("Review:")
        print(item.review)
        print("\n")
        print("Validation:", item.valid)
        print("Reason:", item.reasoning)
        print("==================\n\n\n")


def haiku_generate_review_validate_summary(topic="Python", num=2):
    """
    Demonstrates how to create a chain with 3 steps and these types of links:

    <input>                    ------------------------- the initial values. (topic, num in this case)
      |
    [haiku-generator]          ------------------------- generate `num` haiku in 1 inference
      |
    (split)                    ------------------------- output split into `num` inputs for next step. sequential -> parallel linking.
      |
    [haiku-critic]             ------------------------- `num` inferences simultaneously in threadpool
      |
    (map)                      ------------------------- output elements mapped into inputs for next step. parallel -> parallel linking.
      |
    [validator]                ------------------------- `num` inferences simultaneously in threadpool
      |
    (reduce)                   ------------------------- output elements reduced into a single input for next step. parallel -> sequential linking.
      |
    [summarize-activity]       ------------------------- 1 single inference
      |
    <output>                   ------------------------- the output is a list of summarize-activity.out model instances

    Note: Reduction is the coalescence of the all the elements of parallel chain's output into a single input for the next chainlink. This is necessary to come back to sequential execution.

    Args:
        topic (str, optional): The topic of the haiku. Defaults to "Python".
        num (int, optional): The number of haikus to generate. Defaults to 2.
    """
    haiku_review_engine = Engine.from_file(
        "examples/haiku_generate_review_validate_haiku.fctr"
    )

    res = haiku_review_engine(topic=topic, num=num)
    print("==================")
    pprint(res)
    print("==================")


def haiku_generate_review_via_extends(topic="Python", num=2):
    """
    Demonstrates how to create a chain with 3 steps and these types of links:

    <input>                    ------------------------- the initial values. (topic, num in this case)
      |
    [haiku-generator]          ------------------------- generate `num` haiku in 1 inference (inherited using @extends)
      |
    (split)                    ------------------------- output split into `num` inputs for next step. sequential -> parallel linking.
      |
    [haiku-critic]             ------------------------- `num` inferences simultaneously in threadpool
      |
    (map)                      ------------------------- output elements mapped into inputs for next step. parallel -> parallel linking.
      |
    <output>                   ------------------------- the output is a list of summarize-activity.out model instances

    Note: Reduction is the coalescence of the all the elements of parallel chain's output into a single input for the next chainlink. This is necessary to come back to sequential execution.

    Args:
        topic (str, optional): The topic of the haiku. Defaults to "Python".
        num (int, optional): The number of haikus to generate. Defaults to 2.
    """
    haiku_review_engine = Engine.from_file("examples/haiku_extends.fctr")

    res = haiku_review_engine(topic=topic, num=num)

    print("==================")
    pprint(res)
    print("==================")


if __name__ == "__main__":
    haiku_generate_review_via_extends()
