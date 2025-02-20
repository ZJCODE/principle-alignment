

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

