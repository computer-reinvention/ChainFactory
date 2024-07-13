# ChainFactory: Mass manufacture your LLM chains.

## Overview

`ChainFactory` is a utility to build LLM chains by configuration instead of code. The chains produces this way are reproducible and easy to manage i.e read, edit and share. The created chains can be exported as Python and TypeScript clients and used in your projects without any mod. Additionally, you can pass the YAML configuration to `ChainFactoryEngine` to use them on the fly.

This allows a very interesting pattern where you can create chains on runtime and combine their outputs to do interesting things that are not possible with the standard chains.

## Features

Export your chains as Python code and use them as packages in your projects.

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/pankajgarkoti/ChainFactory.git
   ```

2. Install the required packages:
   ```bash
   poetry install --no-root
   ```

3. Set up environment variables:
   ```bash
   export OPENAI_API_KEY="sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
   ```

### Usage

TBD

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contact

For questions or feedback, please contact [garkotipankaj@gmail.com](mailto:garkotipankaj@gmail.com).
