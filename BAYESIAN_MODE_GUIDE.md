# MDB Bayesian Mode - Quick Start Guide

## Overview

MDB supports **two reasoning modes** that you can toggle via the `.env` file:

1. **Deterministic Mode** (default) - Original Medster clinical analysis
2. **Bayesian Mode** - Probabilistic reasoning with uncertainty quantification

---

## How to Toggle Modes

### Current Mode: **DETERMINISTIC** ✓

Edit `.env` file and change this line:

```bash
# Current (Deterministic Mode)
REASONING_MODE=deterministic

# To switch to Bayesian Mode, change to:
REASONING_MODE=bayesian
```

Then restart the agent:
```bash
cd ~/Desktop/MDB
uv run medster-agent
```

---

## What Changes in Bayesian Mode?

### CLI Banner
```
Autonomous Clinical Case Analysis Agent [BAYESIAN MODE]

Reasoning Mode: BAYESIAN - Bayesian probabilistic reasoning with uncertainty quantification
```

### System Prompts Used

**Bayesian Mode** uses specialized prompts from `src/medster/prompts_bayesian.py`:

1. **Validation Prompt** (`BAYESIAN_VALIDATION_SYSTEM_PROMPT`)
   - Confidence scoring (0.0-1.0)
   - Data completeness percentage
   - Explicit uncertainty factors
   - Returns: `{"done": true/false, "confidence": 0.85, "data_completeness": 0.75, "uncertainty_factors": [...]}`

2. **Action Prompt** (`BAYESIAN_ACTION_SYSTEM_PROMPT`)
   - Information gain prioritization
   - Sequential test strategy (rule-in vs rule-out)
   - Conditional independence analysis
   - Tool selection based on expected entropy reduction

3. **Answer Prompt** (`BAYESIAN_ANSWER_SYSTEM_PROMPT`)
   - Posterior probability tables
   - Likelihood ratio citations
   - 95% confidence intervals
   - Information gain recommendations
   - Clinical decision thresholds

---

## Example Bayesian Output

**User Query:**
```
Analyze 58yo male with chest pain, troponin 0.8, new T-wave inversions
```

**Deterministic Mode Output:**
```
Patient presents with chest pain and elevated troponin (0.8 ng/mL, ref <0.04).
ECG shows new T-wave inversions in anterior leads.
Differential includes:
- Acute coronary syndrome
- Myocarditis
- Takotsubo cardiomyopathy
```

**Bayesian Mode Output:**
```
POSTERIOR PROBABILITY ANALYSIS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Diagnosis          Prior    LR      Posterior   95% CI
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ACS                20%      49×     78%        [68%, 86%]
Myocarditis        5%       12×     12%        [6%, 21%]
Takotsubo          2%       8×      8%         [3%, 16%]
Other              73%      0.03×   2%         [0%, 6%]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

EVIDENCE INTEGRATION:
Finding                  LR+     Impact on ACS Probability
──────────────────────────────────────────────────────────
Troponin 0.8 ng/mL      8.5×    20% → 66%
T-wave inversions       3.2×    66% → 77%
Age 58, male            1.8×    77% → 78%

DIAGNOSTIC CERTAINTY:
- Entropy: 0.65 bits (moderate uncertainty)
- Confidence: HIGH for ACS as leading diagnosis
- Missing data impact: Coronary angiography would reduce entropy to <0.2 bits

OPTIMAL NEXT TEST (Information Gain Analysis):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Test                  Info Gain   P(ACS) if +   P(ACS) if -
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Coronary angiography  2.4 bits    98%           5%
Serial troponin       1.2 bits    89%           45%
Cardiac MRI           1.8 bits    92%           22%
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RECOMMENDATION: Coronary angiography (highest information gain)
```

---

## Key Bayesian Concepts

### Likelihood Ratios (LR)
- **LR+ > 10**: Strong evidence FOR diagnosis
- **LR+ 5-10**: Moderate evidence FOR
- **LR+ 2-5**: Weak evidence FOR
- **LR- < 0.1**: Strong evidence AGAINST diagnosis

### Information Gain (Entropy Reduction)
- Measured in **bits** (0-3 range for typical medical decisions)
- High info gain (>1.5 bits): Test dramatically changes probabilities
- Low info gain (<0.3 bits): Test provides minimal new information

### Confidence Intervals
- **95% CI**: Range where true probability likely falls
- Wider intervals = more uncertainty
- Narrower intervals = more certainty

---

## Bayesian Prompt Files

All Bayesian prompts are in:
- `src/medster/prompts_bayesian.py` - Main Bayesian prompt definitions
- `BAYESIAN_PROMPT_ANALYSIS.md` - Design rationale and examples
- `BAYESIAN_TOGGLE_IMPLEMENTATION_SUMMARY.md` - Implementation details

---

## When to Use Each Mode

### Use **Deterministic Mode** when:
- Quick clinical data retrieval needed
- Straightforward diagnostic workups
- Teaching/demonstrating standard Medster functionality
- You want traditional clinical summaries

### Use **Bayesian Mode** when:
- Uncertain differential diagnosis
- Need to quantify diagnostic confidence
- Selecting optimal next diagnostic test
- Research into probabilistic clinical reasoning
- Want explicit uncertainty quantification

---

## Current Status

✅ **Both modes fully implemented and working**
✅ **Mode indicator displays in CLI banner**
✅ **Toggle via REASONING_MODE in .env**
✅ **All Bayesian prompts created and tested**

**Default**: DETERMINISTIC (safe for general use)
**Experimental**: BAYESIAN (research-grade probabilistic reasoning)

---

## Testing the Toggle

### Quick Test:
```bash
cd ~/Desktop/MDB

# Test deterministic mode
uv run medster-agent
# Look for: "Reasoning Mode: DETERMINISTIC - Deterministic clinical analysis"

# Edit .env: change REASONING_MODE=bayesian
# Test Bayesian mode
uv run medster-agent
# Look for: "[BAYESIAN MODE]" and "Reasoning Mode: BAYESIAN - Bayesian probabilistic reasoning"
```

---

**Questions?** See `BAYESIAN_PROMPT_ANALYSIS.md` for detailed design rationale.
