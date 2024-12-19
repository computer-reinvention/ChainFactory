# ChainFactory: Structured LLM Inference with Easy Parallelism & Tool Calling (`chainfactory-py 0.0.16`)

## Introduction
ChainFactory is a declarative system for creating complex, multi-step LLM workflows using a simple YAML-like syntax. It allows you to connect multiple prompts in a chain, with outputs from one step feeding into inputs of subsequent steps. The most important feature is the reduced reliance on exact wording of the prompts and easy parallel execution wherever iterables are involved.

## Key Features
- Sequential and parallel chain execution
- Ideal for Split-Map-Reduce workflows.
- Automatic prompt generation from concise purpose statements.
- Type-safe outputs with Pydantic models.
- Chain inheritance and reusability.
- Smart input/output mapping between chain links.
- Hash based caching for intermediate prompts and masks.
- Tool calling for fetching data and performing actions.

## Basic Concepts

### ChainLinks
A chain-link is a single unit in your workflow / chain, defined using the `@chainlink` directive:
```yaml
@chainlink my-first-chain
prompt: Write a story about {topic}
out:
    story: str
```
### Sequential vs Parallel Execution
You can specify how chainlinks execute:
- Sequential (`--` or `sequential`): Links run one after another serially.
- Parallel (`||` or `parallel`): Links run simultaneously for multiple inputs (requires an iterable output from the previous link).
**Example**: A 3 step chain.

```yaml
@chainlink generator --     # runs once
@chainlink reviewer ||      # runs multiple times in parallel, number of runs is determined by output of the previous link which must be or have an iterable
@chainlink summarizer --    # runs once to summarize the output of the previous parallel link
```

## Features

### 1. Purpose-Driven Prompts
Instead of writing prompts manually, let ChainFactory generate them:
```yaml
@chainlink
purpose: generate creative haiku topics
in:
    num: int
out:
    topics: list[str]
```
The system will automatically create an optimal prompt based on the purpose and the input variales before executing the chain.

### 2. Easy Parallelism
If a chainlink output is an iterable or something with an iterable attribute, the next chainlink can operate on each element of the previous one concurrently - drastically improving the performance. To achieve this, we just need to change the link type to  `||` or `parallel`. The `Split-Map-Reduce` kind of workflows benefit the most from `ChainFactory`'s seamless parallelism.
```yaml
@chainlink topic_generator --
purpose: generate creative haiku topics
in:
    num: int
out:
    topics: list[str]

@chainlink haiku_generator || # parallel to generate multiple haikus
purpose: generate a haiku
in:
    topics.element: str
out:
    topic: str
    haiku: str
```

### 3. Chain Inheritance
You can build on top of existing chains using the `@extends` directive. If a flow is common to multiple chains, it can be defined once and reused using `@extends`.
```yaml
@extends examples/base_chain.fctr
@chainlink additional_step
```

### 4. Smart Input/Output Mapping
The system automatically maps outputs to inputs between chain links using dot notation:
```yaml
in:
  previous_chain.element.field: str
```

### 5. Type Safety
The YAML defined output structures are converted to a proper Python class at runtime. The class is then used to validate and type-check the output of the chain-link.
```yaml
def:
  Haiku:
    text: str = default value % description
    explanation: str?    # optional field
out:
  haikus: list[Haiku]
```

## Real-World Examples
### 1. Haiku Generator and Reviewer
```yaml
@chainlink haiku-generator
prompt: Write {num} haiku(s) about {topic} # for small inputs, prompt and purpose do not have much of a difference.
out:
    haikus: list[Haiku]

@chainlink reviewer ||     # parallely review each haiku
purpose: critically analyze each haiku
```

### 2. Checking if an Email Contains a Cancellation Request
```yaml
@chainlink cancellation_request
purpose: return true if a given input email explicitly contains an event cancellation request
in:
	email_body: str
out:
  is_cancellation_request: bool
```

### 3. Classification and Action - Making Decisions and Acting on Them
```yaml
@chainlink classify
purpose: to classify the input text into one of the provided labels
in:
	text: str
	labels: list[str]
def:
  Classification:
    label: str % Most relevant label for the input text.
    text: str % The original input text, verbatim.
    snippet: str % Snippet from input text that justifies the label.
    confidence: Literal["extreme", "high", "medium", "low", "none"] % Your confidence level in the label's accuracy.
out:
	classification: Classification

@tool confidence_filter --
in:
    classification: Classification

@tool take_action --
in:
	classification: Classification
out:
	action: str
    label: str

@chainlink validate --
prompt: Is (Action: {action}) in response to (Text: {text}) valid and reasonable?
out:
    is_valid: bool
    reason: str
```

And here's the python counterpart for above `.fctr` file:
```python
from chainfactory import Engine, EngineConfig
from some.module import TEXT, HANDLERS

engine_config = EngineConfig()

@engine_config.register_tool
def confidence_filter(**kwargs): # gets called first
    """
    Raise an exception if the confidence level is low.
    """
    raise NotImplementedError

@engine_config.register_tool  # brand new decorator
def take_action(**kwargs):
    """
    Call a handler based on the classification by ChainFactory.
    """
    raise NotImplementedError

if __name__ == "__main__":
    classification_engine = Engine.from_file("examples/classify.fctr", config=engine_config)
    classification_engine(text=TEXT, labels=list(HANDLERS.keys()))
```

## Tips:
1. **Use Purpose Statements**
When possible, let the system generate prompts using clear one-liner purpose statements. Do this more often for tasks that do not require domain knowledge.
2. **Type Everything**
Define input/output types for better reliability:
```yaml
def:
  MyType:
    field1: str
    field2: int?
```
**Side Note**: In a .fctr file,  any type defined above the current chain-link is considered a global type.
3. **Chain Structure - General Workflows**
- Start with sequential chains for initial processing.
- Use parallel chains for whenever the order or execution is unimportant and iterables are involved.
- End with sequential chains or a final tool call for summarization and getting a final text / object output.

The above is the Split-Map-Reduce pattern. You can also use `ChainFactory` to just simplify prompt management and execution.
4. **Documentation**
Add field descriptions using `%`. This is not only for readability, but also for the LLM to understand the context of the field. It is basically a part of the prompting process.
```yaml
out:
  review: str % A comprehensive analysis of the text
```

## Advanced Features

### Masks
For parallel-to-sequential transitions, use masks to format data:
```yaml
mask:
  type: auto
  variables:
    - result.field1
    - result.field2
```
A template is automatically generated based on the supplied variables to the mask. This template is used to format the data before passing it to the final chainlink.

### Caching
The system automatically caches generated prompts, and masks by hashing them and storing them under `.chainfactory/cache`. So even though the prompt template is generated dynamically in purpose based prompting, it only needs to be done once in the beginning and then whenever the purpose or the inputs change.
*Side Note*: It is recommended to commit the `.chainfactory/cache` folder to your codebase's version control system.

### Tools
Tools are callables that behave in a similar fashion to chain-links. They are used very similarly to chain-links but with a few key differences:
- They are not defined in a `.fctr` file.
- Tools do not have prompts, puposes, or out sections.
- They are used to fetch data that subsequent chain-links need or to perform an action that uses data from the previous chain-links.
```yaml
@chainlink generator
purpose: generate haiku
in:
	topic: str
out:
	haiku: str % the complete haiku text. required.

@tool websearch 
in:
	topic: str # becomes a kwarg to the registered tool.

# the most minimal tool definition is a single line
@tool another_tool 
```
*Note:* If the tools are not registered with the engine config, initialization of the engine will fail.

If defined in a parallel chainlink, the tool will run once corresponding to each instance of the chainlink. Make sure that your tool is stateless and does not have any side effects that could cause issues due to repeated concurrent executions.

If the code causes some side effects and repeating the action is not safe, please only use `@tool` directive in a sequential context. Most of the places where tool use makes sense are things such as fetching data from an API or a database.

Tools are registered using the `register_tools` method of the `ChainFactoryEngineConfig` class. The singular version of this, `register_tool`  can also be used as a decorator. **Warning**: loading a file with tools fails if the config already does not have a tool registered with the same name.

## Configuring the ChainFactory Engine
The `ChainFactoryEngine` or simply the `Engine` can be configured using the `ChainFactoryEngineConfig` (`EngineConfig`) class. You can control aspects such as the language model used, caching behavior, concurrency, and execution traces using the config class. Below are the configuration options available:

- `model`: Specifies the model to use (default is `"gpt-4o"`).
- `temperature`: Sets the temperature for the model, which controls the randomness of the outputs (default is `0`).
- `cache`: Enables caching of prompts and results (default is `False`).
- `provider`: Defines the provider for the language model, with supported options including `"openai"`, `"anthropic"`, and `"ollama"`.
- `max_tokens`: Specifies the maximum tokens allowed per response (default is `1024`).
- `model_kwargs`: A dictionary of additional keyword arguments to pass to the model.
- `max_parallel_chains`: Sets the maximum number of chains that can execute in parallel (default is `10`).
- `print_trace`: If `True`, enables printing of execution traces (default is `False`).
- `print_trace_for_single_chain`: Similar to `print_trace` but for single chain execution (default is `False`).
- `pause_between_executions`: If `True`, prompts for confirmation before executing the next chain (default is `True`).
- `tools`: A dictionary of tools that can be used from the .fctr files. It's updated using the `register_tools` method of the class.


```python
from chainfactory import Engine, EngineConfig
from some_module import websearch

config = EngineConfig(
    model="gpt-4o",
    temperature=0.7,
    cache=True,
    provider="openai",
    max_tokens=2048,
    max_parallel_chains=5,
    print_trace=False,
    print_trace_for_single_chain=False,
    pause_between_executions=True
)

config.register_tools([websearch]) # register a tool or multiple using the register_tools method

@config.register_tool # works as a decorator
def another_tool(**kwargs):
    return kwargs

engine = Engine.from_file("examples/haiku.fctr", config)
```

## Conclusion
ChainFactory makes it easy to create complex LLM workflows without writing code. Its simple syntax, automatic prompt generation, and smart features let you focus on what matters - designing great AI workflows.

Remember that this is just an overview - experiment with the examples to discover more possibilities!

## Getting Help
- Check the examples folder for common patterns
- Break complex chains into smaller, reusable pieces
- Ping me directly on email: garkotipankaj [at] gmail.com
