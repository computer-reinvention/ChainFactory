# ChainFactory: Run Structured LLM Inference with Easy Parallelism (`chainfactory-py 0.0.14`)

## Introduction
ChainFactory is a powerful system for creating complex, multi-step LLM workflows using a simple YAML-like syntax. It allows you to connect multiple prompts in a chain, with outputs from one step feeding into inputs of subsequent steps. The most important feature is the reduced reliance on exact wording of the prompts and easy parallel execution in intermediate steps.

## Key Features
- Sequential and parallel chain execution
- Automatic prompt generation from purpose statements
- Type-safe outputs with Pydantic models
- Chain inheritance and reusability
- Smart input/output mapping between chain links
- Hash based caching for prompts generated from purpose statements and masks for convex transitions.

## Basic Concepts
### ChainLinks
A chain-link is a single unit in your workflow, defined using the `@chainlink` directive:

```yaml
@chainlink my-first-chain
prompt: Write a story about {topic}
out:
    story: str
```

### Sequential vs Parallel Execution
You can specify how chain links execute:
- Sequential (`--` or `sequential`): Links run one after another
- Parallel (`||` or `parallel`): Links run simultaneously for multiple inputs

*Example:* A 3 step chain.
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

### 2. Chain Inheritance
Reuse existing chains with `@extends`:

```yaml
@extends examples/base_chain.fctr
@chainlink additional_step
```

### 3. Smart Input/Output Mapping
The system automatically maps outputs to inputs between chain links using dot notation:

```yaml
in:
  previous_chain.element.field: str
```

### 4. Type Safety
Define your output structures:

```yaml
def:
  Haiku:
    text: str
    explanation: str?    # optional field
out:
  haikus: list[Haiku]
```

## Real-World Examples

### 1. Haiku Generator and Reviewer
```yaml
@chainlink haiku-generator
prompt: Write {num} haiku(s) about {topic}
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

## Best Practices

1. **Use Purpose Statements**
When possible, let the system generate prompts using clear one-liner purpose statements.

2. **Type Everything**
Define input/output types for better reliability:
```yaml
def:
  MyType:
    field1: str
    field2: int?
```

3. **Chain Structure - General Workflows**
- Start with sequential chains for initial processing.
- Use parallel chains for whenever the order or execution is unimportant and iterables are involved.
- End with sequential chains or a final tool call for summarization and getting a final text / object output.

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
The system automatically caches generated prompts, and masksi by hashing them and storing them under `.chainfactory/cache`. So even though the prompt template is generated dynamically in purpose based prompting, it only needs to be done whenever the purpose or the inputs change.

*Side Note*: It is recommended to commit the `.chainfactory/cache` folder to your codebase's version control system.

### Tools
Tools are callables that can be used in a similar way to a chain-link. Any function to be used for this purpose can have an arbitrary number of arguments but should always return a dict.

```yaml
@chainlink generator
purpose: generate haiku
in:
	topic: str
out:
	haiku: str % the complete haiku text. required.

@tool websearch
in:
	topic: str # becomes a kwarg to the registered tool

```

*Note:* If a tool  called `websearch` is not registered with the engine config, initialization will fail.

If defined in a parallel chainlink, the tool will run once corresponding to each instance of the chainlink. If the code causes some side effects and repeating the action is not safe, please only use `@tool` directive in a sequential context. Most of the places where tool use makes sense are things such as fetching data from an API or a database.

You can register tools using the `register_tool` and `register_tools` method of the `EngineConfig` class.

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
- `tools`: A dictionary of tools that can be used from the .fctr files.


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
    print_trace=True,
    prompt_between_executions=True
)
config.register_tool(websearch) # register a tool or multiple using the register_tools method
engine = Engine.from_file("examples/haiku.fctr", config)
```


## Conclusion
ChainFactory makes it easy to create complex LLM workflows without writing code. Its simple syntax, automatic prompt generation, and smart features let you focus on what matters - designing great AI workflows.

Remember that this is just an overview - experiment with the examples to discover more possibilities!

## Getting Help
- Check the examples folder for common patterns
- Break complex chains into smaller, reusable pieces
- Ping me directly on email: garkotipankaj [at] gmail.com
