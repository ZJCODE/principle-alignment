
## Introduction

Principle Alignment is a Python library that helps you match AI models with your own principles.

It uses a large language model (LLM) to understand these principles through a "cognition-decision-behavior" approach. The library checks text inputs (with plans for multimodal support in the future) to find any possible violations of your principles. Principle Alignment works with different language models, such as OpenAI and DeepSeek, giving you flexibility.

The library is user-friendly and can be easily added to your current workflows, making it easier to align your AI models with those principles.

You can use the results from this alignment process to improve your AI models, spot potential problems, and ensure they follow your principles.

## Installation


### Install from pypi

You can install the package from pypi

```bash
pip install principle-alignment  -i https://pypi.org/simple
```

You can also upgrade the package from pypi

```bash
pip install principle-alignment  --upgrade -i https://pypi.org/simple
```

### Install from source

You can also install the package directly from source:

```bash
pip install .
```

For development installation:

```bash
pip install -e .
```


## Usage ( Used By HTTP Server )

### Serving

Create a `.env` file with your API configurations:

```bash
# Both OpenAI and DeepSeek are supported.
API_KEY=your_api_key
BASE_URL=your_base_url  
MODEL=your_model_name
```


create a `principles.md` file with the principles you want to align with (one per line):

```markdown
1. Do no harm
2. Respect user privacy
3. Be transparent
```

creat a `server.py` file with the following content:

```python
from principle_alignment.serving import start_server

start_server(
    host="127.0.0.1",
    port=8080,
    principles_path="./principles.md", # Path to pre-defined principles file
    env_file=".env", # Path to environment variables file
    verbose=True
)
```


run the server:

```bash
python server.py
```

### Testing


##### Just Align Mode

```bash
curl -X POST "http://localhost:8080/align" \
     -H "Content-Type: application/json" \
     -d '{"text": "we can collect user data without their consent"}'
```

output:

```json
{
  "is_violation": true,
  "violated_principles": [
    "2. Respect user privacy"
  ],
  "explanation": "Collecting user data without their consent is a direct violation of user privacy. Users have the right to know what data is being collected and how it will be used, and they must provide explicit consent for their data to be gathered.",
  "rectification": null
}
```

multi violation example

```bash
curl -X POST "http://localhost:8080/align" \
     -H "Content-Type: application/json" \
     -d '{"text": "we can collect user data without their consent and hurt people by using words"}'
```

output:

```json
{
  "is_violation": true,
  "violated_principles": [
    "1. Do no harm",
    "2. Respect user privacy"
  ],
  "explanation": "The statement indicates an intention to collect user data without consent, which violates the principle of respecting user privacy. Additionally, the mention of hurting people by using words suggests a willingness to cause harm, violating the principle of doing no harm.",
  "rectification": null
}
```

no violation example

```bash
curl -X POST "http://localhost:8080/align" \
     -H "Content-Type: application/json" \
     -d '{"text": "you are so nice"}'
```

output:

```json
{
  "is_violation": false,
  "violated_principles": [],
  "explanation": null,
  "rectification": null
}
```


##### Align And Rectify Mode

```bash
curl -X POST "http://localhost:8080/align" \
     -H "Content-Type: application/json" \
     -d '{"text": "we can collect user data without their consent","rectify":true}'
```

output:

```json
{
  "is_violation": true,
  "violated_principles": [
    "2. Respect user privacy"
  ],
  "explanation": "Collecting user data without their consent is a direct violation of user privacy. Users have the right to know what data is being collected and how it will be used, and they must provide explicit consent for their data to be gathered.",
  "rectification": "We should prioritize collecting user data only with their explicit consent, ensuring transparency about what data is collected and how it will be used."
}
```

## Usage ( Used By Python Code )

Prepare the client and model


```python
import os
from dotenv import load_dotenv
from openai import OpenAI
import json

from principle_alignment import Alignment


load_dotenv() # Load environment variables from .env file

# support openai
openai_client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
    base_url=os.environ.get("OPENAI_BASE_URL"),
)

openai_model = "gpt-4o-mini"

# support deepseek
deepseek_client = OpenAI(
    api_key=os.environ.get("DEEPSEEK_API_KEY"),
    base_url=os.environ.get("DEEPSEEK_BASE_URL"),
)

deepseek_model = "deepseek-chat"

client = openai_client
model = openai_model

# client = deepseek_client
# model = deepseek_model

```

initialize the alignment object

```python
alignment = Alignment(client=client, model=model,verbose=False)
```

let the alignment load and understand the principles


```python
# Load principles from a list
alignment.prepare(principles=["Do no harm", "Respect user privacy"])
```

```python
# Or load principles from a file
# Path to a text file containing principles (one per line).
alignment.prepare(principles_file="principles.md")
```

```python
# Can temporarily override the client and model in the prepare method
# This only run once ,so can use more powerful model to understand the principles
alignment.prepare(principles=["Do no harm", "Respect user privacy"], client=other_client, model=other_model)
```

do the alignment

```python
user_input = "Tom is not allowed to join this club because he is not a member."
result = alignment.align(user_input)
print(json.dumps(result, indent=4))
```

example output

```json
{
    "is_violation": true,
    "violated_principles": [
        "1. [Radical Inclusion] Anyone may be a part of Burning Man. We welcome and respect the stranger. No prerequisites exist for participation in our community."
    ],
    "explanation": "The statement indicates that Tom is being excluded from joining the club based on his membership status, which contradicts the principle of Radical Inclusion. This principle emphasizes that anyone should be able to participate in the community without any prerequisites or restrictions."
}
```

```python
user_input = "You are so nice to me."
result = alignment.align(user_input)
print(json.dumps(result, indent=4))
```

example output

```json
{
    "is_violation": false,
    "violated_principles": [],
    "explanation": null
}
```

do the alignment with rectification

```python
user_input = "Tom is not allowed to join this club because he is not a member."
result = alignment.align_and_rectify(user_input)
print(json.dumps(result, indent=4))
```

example output

```json
{
    "is_violation": true,
    "violated_principles": [
        "1. [Radical Inclusion] Anyone may be a part of Burning Man. We welcome and respect the stranger. No prerequisites exist for participation in our community."
    ],
    "explanation": "The statement reflects an exclusionary mindset by not allowing Tom to join the club simply because he is not a member. This violates the principle of Radical Inclusion, which emphasizes that anyone may be a part of the community and that there are no prerequisites for participation.",
    "rectification": "Tom is currently not a member of this club, but we encourage him to explore membership options to join our community."
}
```


## Package Upload

First time upload

```bash
pip install build twine
python -m build
twine upload dist/*
```

Subsequent uploads

```bash
rm -rf dist/ build/ *.egg-info/
python -m build
twine upload dist/*
```

