# ChainFactory: Run Structured LLM Inference with Easy Parallelism (`chainfactory-py 0.0.12`)
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
### Chain Links
A chain link is a single unit in your workflow, defined using the `@chainlink` directive:

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

Example - a 3 step chain:
```yaml
@chainlink generator --     # runs once
@chainlink reviewer ||      # runs multiple times in parallel, number of runs is determined by output of the previous link
@chainlink summarizer --    # runs once to summarize the output of the previous parallel link
```

## Cool Features

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

### 2. Weird Snack Combo Generator + Parallel Filter + Email Writera

```yaml
@chainlink
purpose: Generate {num} combinations of snacks that go well with each other. Generate {num} such combinations.
def:
  SnackCombo:
    items: list[str]
    comment: str?
out:
  combos: list[Combo]

@chainlink ||a # runs {num} instance in parallel
purpose: Given a snack combination, sarcastically comment on why it's the weirdest snack combination ever.
in:
  combos.element.items: str
out:
  res: list[SnackCombo]
```
examples/WeirdSnackCombo.fctr

```yaml
@chainlink extends WeirdSnackCombos.fctr
purpose: Write a satirical article about the provided trivial subject bringing the demise of modern society.
mask:
  variables:
    - res.element.items
    - res.element.comment
out:
    article: str
```
examples/Article.fctra

When the above file is loaded, the only input required is the number of combos to generate. The system will automatically generate the prompt template and execute the chain - at the end, we get a satirical article about the weird snack combos.


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
- Use parallel chains for whenever the order or execution is unimportant.
- End with sequential chains for summarization and getting a final text / object output.

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
The system automatically caches generated prompts, and masks. Improving performance for repeated runs of the same chains.

## Conclusion
ChainFactory makes it easy to create complex LLM workflows without writing code. Its simple syntax, automatic prompt generation, and smart features let you focus on what matters - designing great AI workflows.

Remember that this is just an overview - experiment with the examples to discover more possibilities!

## Getting Help
- Check the examples folder for more patterns
- Use the built-in validation to catch errors early
- Break complex chains into smaller, reusable pieces
- Ping me directly on email: garkotipankaj@gmail.com
