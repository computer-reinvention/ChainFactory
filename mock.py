from chainfactory import Engine
from langchain.globals import set_debug, set_verbose

set_debug(False)
set_verbose(False)


def haiku_and_review_sequential(topic="Python", num=2):
    """
    Demonstrates how to create and execute a sequential chain.
    """
    haiku_review_engine = Engine.from_file(
        "examples/haiku_generate_review.fctr"
    )  # this is a sequential chain. Step 1 generates and step 2 reviews all of them sequentially at onve
    res = haiku_review_engine(topic=topic, num=num)

    for rev in res.reviews:
        print("Haiku:")
        print(rev.haiku)
        print("Review:")
        print(rev.review)
        print("\n")


def haiku_and_review_parallel(topic="Python", num=2):
    """
    Demonstrates how to create a chain with 2 steps and these types of links:

    <input>
        |
    [haiku-generator] ------------------------- (generate `num` haiku in 1 inference)
        |
    (split)           ------------------------- output is split `num` inputs for next step. sequential -> parallel linking.
        |
    [haiku-critic]    ------------------------- parallel (`num` inferences simultaneously in threadpool)
        |
    <output>          ------------------------- the output is a list of haiku-critic.out model instances


    Args:
        topic (str, optional): The topic of the haiku. Defaults to "Python".
        num (int, optional): The number of haikus to generate. Defaults to 2.
    """
    haiku_review_engine = Engine.from_file(
        "examples/haiku_generate_review_parallel.fctr"
    )  # this chain has a parallel step. Step 1 generates haikus and step 2 reviews each of them parallely
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

    <input>
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

    Args:
        topic (str, optional): The topic of the haiku. Defaults to "Python".
        num (int, optional): The number of haikus to generate. Defaults to 2.
    """
    haiku_review_engine = Engine.from_file(
        "examples/haiku_generate_review_validate.fctr"
    )

    res = haiku_review_engine(topic=topic, num=1)

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


if __name__ == "__main__":
    haiku_generate_review_validate(topic="adderall", num=6)
