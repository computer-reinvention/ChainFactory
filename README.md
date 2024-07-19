# ChainFactory: Mass manufacture your LLM chains.

## Overview

`ChainFactory` is a utility to build LLM chains by configuration instead of code. The chains produces this way are reproducible and easy to manage i.e read, edit and share. The created chains can be exported as Python code and used in your projects without any mod. Additionally, you can pass the YAML configuration to `ChainFactoryEngine` to use them on the fly.

This allows a very interesting pattern where you can create chains during runtime and combine their outputs to do interesting things that are not possible with the standard code defined chains.

## Features

TBD

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/pankajgarkoti/ChainFactory.git
   ```

2. Install the required packages:
   ```bash
   poetry install
   ```

3. Set up environment variables:
   ```bash
   export OPENAI_API_KEY="sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
   ```

# The ChainFactory Specification
**Draft 002**

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
    type: template # possible values are template, auto
    purpose: null # can be provided to auto generate the prompt template if the input variables are given
    template: | # the purpose and type fields are ignored if the template is provided
        Write a haiku about {topic}

# shorthand for the above
prompt: |
    Write a haiku about {topic}

# additionally, the following shorthand can be used for auto mode
purpose: "to generate haikus" # the file should not contain the prompt field if the purpose field is at the top level

```

### Out
The `out` keyword defines part of the .fctr file that defines the output structure of the chain. The `out` section contains attributes for the desired output structure. Not defining the out section means that the chain output is to be a single string with no enforced structure.

Example Usage:
``` yaml
out:
    haikus : list[Haiku] # using the Haiku model defined in the def section
```

## Contact
For questions or feedback, please create an issue or contact [garkotipankaj@gmail.com](mailto:garkotipankaj@gmail.com).
