# ChainFactory: Run Structured LLM Inference with Easy Parallelism (`chainfactory-py 0.0.10`)

## Overview

`ChainFactory` is a utility to build LLM chains by configuration instead of code. The chains produced this way are reproducible and easy to manage i.e read, edit and share.
The chains can be executed using ChainFactoryEngine - making it possible to parallelize the execution wherever required.
Besides the engine, ChainFactory also plans to eventually support transpilation to Python and JavaScript clients in the near future.

**Side Note**: This allows a very interesting pattern where you can create chains during runtime and combine their outputs to do interesting things that are not possible with the standard code defined chains.

## Installation
Using `pip` or [https://python-poetry.org/](poetry) as follows:

   ```bash
   pip3 install chainfactory-py
   ```

   ```bash
   poetry add chainfactory-py
   ```

Make sure your OpenAI API key is set up in the environment variables:

   ```bash
   export OPENAI_API_KEY="sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
   ```

## The Roadmap & TODOs

- [x] implement defined reusable types
- [x] accept direct kwargs in engine call
- [x] implement bells and whistles for the prompt section
- [x] implement default values
- [x] implement field descriptions
- [x] syntax: serial execution using @chainlink /name/ sequential
- [x] basic documentation and walkthrough
- [x] syntax: parallel execution using @chainlink /name/ ||
  - [x] data piping and variable matching
  - [x] sequential to parallel handover (split)
  - [x] parallel execution in threadpool
  - [x] parallel to parallel handover (map)
  - [x] parallel to sequential handover (reduce)
- [ ] python transpilation
- [ ] typescript transpilation

# The ChainFactory Specification
**Draft 004**

## File Structure
A `.fctr` file is mostly written in  `.yaml` syntax. Multiple steps can be defined in a single file by separating them with a `@chainlink [name] [type]` directive.

- Specify the Prompt Template or list the Inputs (field: purpose + in or prompt)
- Define output models (keyword: def)
- Specify the Outputs (keyword: out)

## Typing
The typing system takes direct inspiration from Python's type annotations with some added syntax to add descriptions. The following atomic types are supported:

- str
- int
- float
- bool

Additionally, the following data structures are supported:
- list
- dict

The syntax for typing a field is as follows:

`[name]: [type][?] = [default_value] % [description]`

The order in which the description and default value are specified is not important. Both the description and the default value are optional. `?` marks the field as optional.

The `?` symbol right after a type (without spaces) indicates that the field is optional. If a field has a RHS value that is not a valid type, ChainFactory will assume that the field type is `str` and the RHS is a default value.

Custom types can be defined under the `def` field of the .fctr file.

### Definitions
The def section is the part of the .fctr file that defines custom types to be used in rest of the file.

Example Usage:
``` yaml
def:
  Haiku:
    haiku: str
    explanation: str % the explanation for the haiku. must be 2 sentences minimum. # passed as field description to the model
    topic: str
```

The models defined in the `def` section can be used with other inbuilt types and other defined models to enforce complex output structures.
MARK
### Prompt
The prompt template related options can be set under this section. The following fields are defined:

- type: template # can be template, auto. the template is generated automatically based on the purpose of the chain in the auto mode.
- purpose: null # a string that describes the purpose of the chain. this can be used for auto generating the prompt template.
- template: | # the template to use for the prompt. 

Example Usage:
``` yaml
prompt:
  type: template # possible values are template, auto.
  purpose: null # can be provided to auto generate the prompt template if the input variables are given
  template: | # the purpose and type fields are ignored if the template is provided
    Write a haiku about {topic}
```

Usually you would use a shorthand for the above as follows:
```
prompt: Write a haiku about {topic}
```

Additionally, the following shorthand can be used for auto mode:
```
purpose: "to generate haikus" # the file should contain the in field
```
### In
This section defines the input variables for this chain. It is only required when the prompt is set to `auto` mode. ChainFactory will automatically generate a prompt using `purpose` and the input variables for the chain on the first invocation.

Example Usage:
``` yaml
purpose: "to generate haikus"

in:
  num: int
  topic: str
```

On running the chain containing the above definition, this prompt template is generated on the first invocation and used for the subsequent invocations. It is not cached and will be regenerated for every Factory object:

``` txt
Generate {num} haikus on the topic of {topic}. Each haiku should follow the traditional 5-7-5 syllable structure.
```

The benefit of using this approach is not that apparent when we have a small number of inputs. However, as the number of input variables goes up, defining the purpose in a single sentence and just listing the inputs is quite helpful and keeps the chain definition clean.

**Side Note**: In future, the generated prompt can be automatically optimized using something like `DSpy` - which would then make this way of defining the chain superior than writing prompts manually for all cases.

### Out
The `out` keyword defines the output structure of the chain. You can refer to the models defined in the `def` section to create consistent and well-typed output structures. If the `out` section is not defined, the chain output is assumed to be a single string with no enforced structure.

Example Usage:
``` yaml
out:
  haikus : list[Haiku] # using the Haiku model defined in the def section
```

## Usage

The completed `.fctr` file for generating haikus looks like this: 

``` yaml
# file: haiku.fctr
def:
  Haiku:
    haiku: str
    explanation: str
    topic: str
prompt: Write {num} haiku(s) about {topic}
out:
  haikus : list[Haiku]
```

This file can be loaded directly into the `ChainFactoryEngine`. This is a driver class which creates the `Factory` from `haiku.fctr` and then uses the `Factory` to create a `LangChain` `RunnableSerializable` chain internally using a dynmically created pydantic model to force the model output into the desired structure.
An instance of the `ChainFactoryEngine` can then be directly called like a function. Any input variables can be passed as kwargs and are directly passed to the underlying chains.

``` python
from chainfactory import ChainFactoryEngine

engine = ChainFactoryEngine.from_file("haiku.fctr")
results = engine(topic="Python", num=3) # this call will execute the chain and any subsequent chains after that
```

Executing the above generates 3 haikus and their explanations as expected:

``` txt
Silent code it weaves,
Serpentine logic unfolds,
Errors shed like skin.
Explanation: This haiku captures the elegance and efficiency of Python programming, likening it to a snake shedding its skin to symbolize the ease of debugging and refining code.


Indentation rules,
Whitespace guides the coder's hand,
Python's zen revealed.
Explanation: This haiku highlights Python's unique use of indentation and whitespace to structure code, reflecting the language's philosophy of simplicity and readability.


Libraries abound,
Endless tools at your command,
Python's power grows.
Explanation: This haiku emphasizes the vast array of libraries and tools available in Python, showcasing its versatility and the growing strength of its ecosystem.
```

## Defining and Executing a Multi-Step Chain

This is where the `@chainlink` directive comes into play. Recall that the syntax for using the directive is as follows:

`@chainlink [name] [type]`

Both the parameters are optional. Name can be any string without spaces and type can be either `sequential` or `parallel`. If the name is not provided, the chain name will be a random UUID. The default value for type is *sequential*. 

Since ChainFactory can execute chains in parallel or sequentially, there is a need to define the rules which this propagation of execution should follow.

The following transition interfaces are formed based on the chain execution type. It is easier to refer to them if we consider chains as analogous to lens in optical physics.

1. (sequential -> sequential)
    - This is the transition interface when the output of a sequential chain is passed into the next chain.
    - Input variables are matched on the basis of the names and only the matching variables are passed as the input to the next chain.
    - You can refer to internal fields using . access syntax as with JavaScript objects.
    - This interface is analogous to a single ray of light changing mediums. We will call this a `linear` transition.

2. (sequential -> parallel)
    - This is the transition interface when the output of a sequential chain is passed into multiple instances of the next chain. The construction of the input follows the following simple rule:
        - The number of parallel computations is determined by the length of the first iterable field found in the previous chain output (`n`).
        - The outputs from the sequential chain are split into `n` similar but not identical inputs for parallel chain's instances.
        - Any non-iterable variable from the previous chain can be used as an input variable simply in this one as before.
    - In optics, a concave lens essentially spreads the light coming from a single source into multiple parallel beams (if the object is at focus). 
    - Thus, keeping the optical analogy, we will call this a `concave` transition.

3. (parallel -> parallel)
    - This is a transition interface when the output of a parallel chain is passed into an equal number of instances of the next chain.
    - Name based filtering still applies.
    - This interface is analogous to a bundle of light transitioning from 1 medium to another. We will call this a `planar` transition.

4. (parallel -> sequential)
    - This is a transition interface when the outputs of multiple instances of the last chain is used to create a single output.
    - This interface is the most complex one of the four.
    - A field called `mask` is used to specify how to represent the element from the previous chain output in this chain's prompt. This is basically a string template.
    - Analogous to a convex lens focusing a bundle of parallel beams into a single point. We will call this a `convex` transition.


The above rules, once implemented, can be used to create complex chains which can be executed in parallel or sequentially just by specifying the transition type. Let's start with a simple example.

### Sequential -> Sequential Transition

``` yaml
# Example of a linear chain interface
@chainlink haiku-generator
prompt: Write {num} haiku(s) about {topic}. Use the standard 5-7-5 syllable pattern.
def:
  Haiku:
    haiku: str the haiku text
    explanation: str? 
    topic: str % the original topic

out:
  haikus : list[Haiku]

@chainlink haiku-critic
prompt: |
  Write a short and concise review for each the following haikus.

  {haikus}

  Consider the following:
    - Creativity and Originality
    - Clarity and Structure
    - Emotional Impact
    - Relevance and Cultural Significance

    Write a review of the above haikus.
def:
  HaikuReview:
    review: str % The review of the haiku. 
    haiku: str % The haiku text provided as input.
out:
  reviews: list[HaikuReview]
```

Note how the `@chainlink` directive is used to define the chain with multiple steps. The `haikus` field is present in both the `generator` and `critic` chains. ChainFactory will automatically match the input variables and pass them to the respective chains. The following diagram shows the execution.

``` txt

<input>           ------------------------- the initial values. (topic, num in this case)
    |
    | 
[haiku-generator] ------------------------- (generate `num` haiku in 1 inference)
    |
    |
(filter)          ------------------------- output is filtered to only retain relevant fields. sequential -> sequential linking.
    |
    |
[haiku-critic]    ------------------------- (generate `num` reviews in 1 inference)
    |
    |
<output>          ------------------------- the output is a haiku-critic.out instance


Note: Filtering makes sure that only the input_variables of the subsequent chain are included from the previous chain output.

```

### Sequential -> Parallel Transition
As stated this transition involves creation of multiple instances of the next chain and initiating them in parallel.

``` yaml
@chainlink haiku-generator
prompt: Write {num} haiku(s) about {topic}. Use the standard 5-7-5 syllable pattern.
def:
  Haiku:
    haiku: str
    explanation: str
out:
  topic: str % the original topic. required.
  haikus : list[Haiku]

# a concave transition between the two chainlinks

@chainlink haiku-critic ||
purpose: critical analysis of a haiku in 3 to 5 sentences
in:
  topic: str
  haikus.element.haiku: str
  haikus.element.explanation: str
out:
  review: str % concise literary analysis of this haiku.
  haiku: str % original haiku text. required.
```

Pay attention to the `element` syntax to refer to the interal fields of the element in the iterable from previous chain output. The `critic` chain will now be executed on each of the haiku separately.
ChainFactory will automatically initiate len(haikus) instances of the `critic` chain in parallel and pass the filtered inputs to each of them.

Here's the flow diagram:

``` txt

<input>           ------------------------- the initial values. (topic, num in this case)
    |
    |
[haiku-generator] ------------------------- (generate `num` haiku in 1 inference)
    |
    |
(filter)
    |
    |
(split)           ------------------------- output is used to prepare `num` inputs for next step. sequential -> parallel linking.
    |
    |
[haiku-critic]    ------------------------- parallel (`num` inferences simultaneously in threadpool)
    |
    |
<output>          ------------------------- the output is a list of haiku-critic.out model instances

Note: Splitting means creating `num` separate inputs that will be passed to `num` simultaneous instances of the subsequent chain. Filtering is automatically applied.

```

### Parallel -> Parallel Transition

This transition again acts on the elements of iterable fields from the previous chain outputs. We can add a validation step to the above example to demonstrate this transition.

``` yaml
@chainlink haiku-generator
prompt: Write {num} haiku(s) about {topic}. Use the standard 5-7-5 syllable pattern.
def:
  Haiku:
    haiku: str
    explanation: str
out:
  topic: str % the original topic. required.
  haikus : list[Haiku]

# a concave transition between the two chainlinks

@chainlink haiku-critic ||
purpose: critical analysis of a haiku in 3 to 5 sentences
in:
  topic: str
  haikus.element.haiku: str
  haikus.element.explanation: str
out:
  review: str % concise literary analysis of this haiku.
  haiku: str % original haiku text. required.

# a planar transition between two parallel chainlinks

@chainlink validator ||
purpose: validate if critical review of a haiku is sensible
in:
  haiku-critic.element.haiku: str % the haiku text
  haiku-critic.element.review: str % ai generated review of the haiku
out:
  valid: bool % true if the review is sensible, false otherwise. required.
  haiku: str % verbatim haiku text. required.
  review: str % verbatim review text. required.
  reasoning: str % reasoning for your decision. required.
```

Note how the validation chain refers to the previous chain output using the `chain-name.element` syntax. Here's the flow diagram:

``` txt

<input>           ------------------------- the initial values. (topic, num in this case)
  |
  |
[haiku-generator] ------------------------- (generate `num` haiku in 1 inference)
  |
  |
(split)           ------------------------- output split into `num` inputs for next step. sequential -> parallel linking.
  |
  |
[haiku-critic]    ------------------------- parallel (`num` inferences simultaneously in threadpool)
  |
  |
(map)             ------------------------- output elements mapped into inputs for next step. parallel -> parallel linking.
  |
  |
[validator]       ------------------------- parallel (`num` inferences simultaneously in threadpool)
  |
  |
<output>          ------------------------- the output is a list of validator.out model instances

Note: Mapping is a slightly complex form of filtering. It is applied on all elements of previous chain's output at once.

```

### Parallel -> Sequential Transition
This is the most important transition as most use cases require a single output at the end of the chain. This involves providing a mask to tell ChainFactory which how the elements of the previous chain output will show up in the final prompt. Prepare yourself for haiku-ception. We ask the system to generate a haiku on its business of generating haikus.


``` yaml
@chainlink haiku-generator
prompt: Write {num} haiku(s) about {topic}. Use the standard 5-7-5 syllable pattern.
def:
  Haiku:
    haiku: str
    explanation: str
out:
  topic: str % the original topic. required.
  haikus : list[Haiku]

# a concave transition between the two chainlinks

@chainlink haiku-critic ||
purpose: critical analysis of a haiku in 3 to 5 sentences
in:
  topic: str
  haikus.element.haiku: str
  haikus.element.explanation: str
out:
  review: str % concise literary analysis of this haiku.
  haiku: str % original haiku text. required.

# a planar transition between two parallel chainlinks

@chainlink validator ||
purpose: validate if critical review of a haiku is sensible
in:
  haiku-critic.element.haiku: str % the haiku text
  haiku-critic.element.review: str % ai generated review of the haiku
out:
  valid: bool % true if the review is sensible, false otherwise. required.
  haiku: str % verbatim haiku text. required.
  review: str % verbatim review text. required.
  reasoning: str % reasoning for your decision. required.

# and here's the final convex transition - necessary to merge output elements from the parallel chainlinks 

@chainlink summarizer --
purpose: create a humorous haiku describing the haiku generation and reviewing system based on your observations
mask: 
  type: auto
  variables: 
    - validator.element.haiku
    - validator.element.review
    - validator.element.valid
out:
  generator_haiku: str
  generator_haiku_explanation: str
  reviewer_haiku: str
  reviewer_haiku_explanation: str
```

Here's the flow diagram. We finally have 3 transitions and 4 chainlinks.

``` txt

<input>                    ------------------------- the initial values. (topic, num in this case)
  |
  |
[haiku-generator]          ------------------------- generate `num` haiku in 1 inference
  |
  |
(split)                    ------------------------- output split into `num` inputs for next step. sequential -> parallel linking.
  |
  |
[haiku-critic]             ------------------------- `num` inferences simultaneously in threadpool
  |
  |
(map)                      ------------------------- output elements mapped into inputs for next step. parallel -> parallel linking.
  |
  |
[validator]                ------------------------- `num` inferences simultaneously in threadpool
  |
  |
(reduce)                   ------------------------- output elements reduced into a single input for next step. parallel -> sequential linking.
  |
  |
[summarize-activity]       ------------------------- 1 single inference converts `num` inputs into a single output.
  |
  |
<output>                   ------------------------- the output is a list of summarize-activity.out model instances


Note: Reduction is the coalescence of the all the elements of parallel chain's output into a single input for the next chainlink. This is necessary to come back to sequential execution.

```

This completes an introduction to the syntax and different transitions involved in chains. Using these as basic building blocks, we can create complex chains with multiple steps and multiple transitions with parallelism naturally integrated into them.


## Feedback and Contact
For questions or feedback, please create an issue or contact [garkotipankaj@gmail.com](mailto:garkotipankaj@gmail.com).
