# ChainFactory: Mass manufacture your LLM chains.

## Overview

`ChainFactory` is a utility to build LLM chains by configuration instead of code. The chains produces this way are reproducible and easy to manage i.e read, edit and share. The created chains can be exported as Python code and used in your projects without any mod. Additionally, you can pass the YAML configuration to `ChainFactoryEngine` to use them on the fly.

This allows a very interesting pattern where you can create chains during runtime and combine their outputs to do interesting things that are not possible with the standard code defined chains.


## Installation from PyPI
1. using `pip` as follows:

   ```bash
   pip3 install chainfactory-py

   ```

   Or if you are using `poetry` as the package manager the command would be: `poetry add chainfactory-py@latest`
    

2. The setup is not yet tested with `anthropic` API but it should most likely work. If it does not, please create an issue and I will try to fix it. Or if you are feeling adventurous, feel free to contribute with code :). Currently, ChainFactory will not work if the env variables do not contain this env var.

   ```bash
   export OPENAI_API_KEY="sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
   ```

# The ChainFactory Specification
**Draft 003**

## Structure
A .fctr file is a YAML file with 1 major distinction - it can contain duplicate fields in the top level mapping.

- Specify the Prompt or list the Inputs (keyword: prompts & in)
- Define Models (keyword: def)
- Specify the Outputs (keyword: out)

## Typing
The typing system takes direct inspiration from Python's type annotations. The only difference is that the type system is stricter and more limited. The following atomic types are supported:

- str
- int
- float
- bool
- list
- dict

It is possible to define custom types in the `def` section of the .fctr file. The syntax for typing a field is as follows:

`[name]: [type][?]=[default_value]`

The `?` symbol right after a type (without spaces) indicates that the field is optional. If a field has a RHS value that is not a valid type, ChainFactory will assume that the field type is `str` and the RHS is a default value.

### Definitions
The def section is the part of the .fctr file that defines custom types to be used in rest of the file.

Example Usage:
``` yaml
def:
    Haiku:
        haiku: str
        explanation: str
        topic: str
```

The models defined in the `def` section can be used to compose the desired output structure of the chain.

### Prompt
The prompt template related options can be set under this section. Attributes of the `prompt` section are:

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
prompt: |
    Write a haiku about {topic}
```

Additionally, the following shorthand can be used for auto mode:
```
purpose: "to generate haikus" # the file should not contain the prompt field if the purpose field is at the top level
```
### In
This section defines the input variables for this chain. It is only requred when the prompt is set to `auto` mode. ChainFactory will automatically generate a prompt using `purpose` and the input variables for the chain on the first invocation.

Example Usage:
``` yaml
purpose: "to generate haikus"

in:
    num : int
    topic : str
```

On running the chain containing the above definition, this prompt template is generated on the first invocation and used for the subsequent invocations. It is not cached and will be regenerated for every Factory object:

``` txt
Generate {num} haikus on the topic of {topic}. Each haiku should follow the traditional 5-7-5 syllable structure.
```

The benefit of using this approach is not that apparent when we have a small number of inputs. However, when we reach the >5 input variables teritory just defining a 1 line purpose and the input varables is like magic.

### Out
The `out` keyword defines part of the .fctr file that defines the output structure of the chain. The `out` section contains attributes for the desired output structure - it can refer to the models defines in the def section to creae more complex outputs. Not defining the out section means that the chain output is to be a single string with no enforced structure.

Example Usage:
``` yaml
out:
    haikus : list[Haiku] # using the Haiku model defined in the def section
```

## Usage

The complete `.fctr` file for generating haikus using a prompt template looks like this: 
``` yaml
# file: haiku.fctr
def:
    Haiku:
        haiku: str
        explanation: str
        topic: str

prompt: |
    Write {num} haiku(s) about {topic}

out:
    haikus : list[Haiku]
```

Executing the above chain can be done as follows:

``` python
from chainfactory.interfaces import ChainFactoryEngine

engine = ChainFactoryEngine.from_file("haiku.fctr")

generated_haikus = engine(topic="Python", num=3)
```

The following code generates 3 haikus and their explanations as expected:

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


## Feedback and Contact
For questions or feedback, please create an issue or contact [garkotipankaj@gmail.com](mailto:garkotipankaj@gmail.com).
