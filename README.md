
## Introduction

Principle Alignment is a Python package that helps you align your AI models with ethical principles. It uses a pre-trained language model to analyze text inputs and determine whether they violate any predefined principles. 

The package supports multiple language models, including OpenAI and DeepSeek. You can define your own principles or use a set of predefined principles to check for violations in your AI models. 

Principle Alignment is designed to be easy to use and integrate into your existing workflows, making it simple to ensure that your AI models are aligned with ethical principles.

Use the output of the alignment to improve your AI models, identify potential ethical issues, and build trust with your users.

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


## Usage (Serving Version)


Create a `.env` file with your API configurations:

```bash
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

test the server:

```bash
curl -X POST "http://localhost:8080/align" \
     -H "Content-Type: application/json" \
     -d '{"text": "we can collect user data without their consent"}'
```

output:

```json
{"is_violation":true,
"violated_principle":"2. Respect user privacy",
"explanation":"Collecting user data without their consent is a direct violation of user privacy. Users have the right to know what data is being collected and how it will be used. Failing to obtain consent undermines their autonomy and trust."}
```

## Usage (Detail Version)


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
    "violated_principle": "1. [Radical Inclusion] Anyone may be a part of Burning Man. We welcome and respect the stranger. No prerequisites exist for participation in our community.",
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
    "violated_principle": null,
    "explanation": null
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

