from chainfactory import Engine
from langchain.globals import set_debug, set_verbose

set_debug(True)
set_verbose(True)


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
    Demonstrates how to create and execute a parallel chain.
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


if __name__ == "__main__":
    haiku_and_review_parallel(topic="motorcycles", num=3)
    # haiku_and_review_sequential(topic="Fruits", num=3)
