import yaml
import os
from langchain.chains import LLMChain
from langchain.llms import OpenAI


def load_chain(chain_file: str):
    with open(chain_file, "r") as file:
        chain = yaml.safe_load(file)
    return chain


def create_chain(chain_file: str):
    chain = load_chain(chain_file)
    llm = OpenAI(temperature=0.9, model_name="gpt-3.5-turbo")
    chain = LLMChain(llm=llm, prompt=chain["prompt"], output_key=chain["output_key"])
    return chain


if __name__ == "__main__":
    chain_file = os.path.join(os.getcwd(), "chain.yaml")
    chain = create_chain(chain_file)
    print(chain.run("What is the capital of France?"))
