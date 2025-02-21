

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


## Usage


Prepare the client and model


```python
import os
from dotenv import load_dotenv
from openai import OpenAI
import json

from principle_alignment import Alignment


load_dotenv() # Load environment variables from .env file

openai_client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
    base_url=os.environ.get("OPENAI_BASE_URL"),
)

model = "gpt-4o-mini"
```

initialize the alignment object

```python
alignment = Alignment(client=openai_client, model=model,verbose=False)
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

