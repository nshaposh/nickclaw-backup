---
name: data-science-stack
description: Bootstrap the Python data science stack (pandas, matplotlib, scipy, etc.) in the Hermes venv
version: 1.0.0
metadata:
  hermes:
    tags: [data-science, python, pandas, matplotlib, jupyter]
    related_skills: [jupyter-live-kernel]
---

# Data Science Stack Setup

## Overview
This environment is a Hermes agent running in a Python venv. To do data science work, the venv needs pip bootstrapped and libraries installed.

## Bootstrapping pip

```bash
python3 -m ensurepip
```

Then use `python3 -m pip install` for all package operations.

## Installing the full data science stack

```bash
python3 -m pip install pandas openpyxl pdfplumber matplotlib seaborn numpy scipy plotly
```

## What each package does

| Package | Purpose |
|---------|---------|
| pandas | DataFrames, CSV/Excel read/write, data manipulation |
| openpyxl | Excel (.xlsx) file support |
| pdfplumber | PDF text and table extraction |
| matplotlib | Core plotting and charts |
| seaborn | Statistical visualizations on top of matplotlib |
| numpy | Numerical computing, arrays, linear algebra |
| scipy | Scientific computing, statistics, optimization |
| plotly | Interactive HTML charts |

## Verification

```python
import pandas as pd
import matplotlib.pyplot as plt
import pdfplumber
import openpyxl
import numpy as np
import scipy
import seaborn as sns
import plotly.express as px

print("All libraries imported successfully")
```

## Key limitations

- pip is NOT pre-installed — must run `ensurepip` first
- No GPU support in this environment
- For heavy ML workloads, consider Modal or a cloud GPU instance
