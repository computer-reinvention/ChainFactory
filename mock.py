from chainfactory import Engine
from langchain.globals import set_debug, set_verbose

set_debug(True)
set_verbose(True)

if __name__ == "__main__":
    haiku_review_engine = Engine.from_file(
        "examples/haiku_generate_review.fctr"
    )  # this is a sequential chain. Step 1 generates and step 2 haikus and step 2 generates a review for each haiku.
    res = haiku_review_engine(topic="Python", num=2)

    for rev in res.reviews:
        print("Haiku:")
        print(rev.haiku)
        print("Review:")
        print(rev.review)
        print("\n")
