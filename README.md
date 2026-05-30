# medical-literature-ai

> **PubMed query or paper abstracts → AI-synthesized evidence summary.** Consensus, controversies, clinical implications, evidence grade, research gaps. Integrates directly with PubMed API.

[![PyPI](https://img.shields.io/pypi/v/medical-literature-ai?style=flat)](https://pypi.org/project/medical-literature-ai/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

⚠️ For research and informational purposes. Always consult clinical guidelines and specialists for medical decisions.

## Quickstart

```bash
pip install medical-literature-ai

# Search PubMed directly
python -m medical_literature_ai "metformin cardiovascular outcomes type 2 diabetes"

# From your own abstracts file
python -m medical_literature_ai abstracts.txt --query "effect of X on Y"
```

## What it synthesizes

- **Evidence grade** A–D with explanation
- **Key findings** with strength (strong/moderate/weak/conflicting) and effect sizes
- **Consensus** — areas of consistent evidence
- **Controversies** — active debates with both sides and current resolution
- **Clinical implications** — actionable recommendations with strength ratings
- **Research gaps** — unanswered questions
- **Safety signals** — any concerns raised across studies
- **Plain language summary** — patient-readable version

## License
MIT © [Alper Nabil Gabra Zakher](https://github.com/AlperNab)
