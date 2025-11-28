# MDB Reasoning Mode Toggle - Usage Guide

## Overview

MDB supports two reasoning modes that can be toggled via environment configuration:

1. **Deterministic Mode** (default) - Original Medster prompts
2. **Bayesian Mode** - Probabilistic reasoning with uncertainty quantification

This allows A/B testing and gradual migration to Bayesian enhancements.

---

## Quick Start

### Switch to Bayesian Mode

1. Edit `.env` file:
```bash
REASONING_MODE=bayesian
```

2. Restart MDB:
```bash
cd ~/Desktop/MDB
python -m medster.cli
```

3. Verify mode in startup banner:
```
MEDSTER [BAYESIAN MODE]
Reasoning Mode: BAYESIAN - Bayesian probabilistic reasoning with uncertainty quantification
```

### Switch Back to Deterministic Mode

1. Edit `.env` file:
```bash
REASONING_MODE=deterministic
```

2. Restart MDB

---

## Architecture

### File Structure

```
src/medster/
├── prompts.py                  # Original Medster prompts + toggle logic
├── prompts_bayesian.py         # Bayesian-enhanced prompts (NEW)
├── config.py                   # REASONING_MODE configuration
└── agent.py                    # Uses ACTIVE_* prompts (mode-agnostic)
```

### Toggle Mechanism

The `prompts.py` module exports `ACTIVE_*` prompts based on `REASONING_MODE`:

```python
from medster.config import REASONING_MODE

def get_active_prompts():
    if REASONING_MODE == "bayesian":
        return {
            "mode": "bayesian",
            "validation": BAYESIAN_VALIDATION_SYSTEM_PROMPT,
            "action": BAYESIAN_ACTION_SYSTEM_PROMPT,
            "answer": BAYESIAN_ANSWER_SYSTEM_PROMPT,
        }
    else:
        return {
            "mode": "deterministic",
            "validation": VALIDATION_SYSTEM_PROMPT,
            "action": ACTION_SYSTEM_PROMPT,
            "answer": ANSWER_SYSTEM_PROMPT,
        }

# Exports used by agent
ACTIVE_VALIDATION_PROMPT = get_active_prompts()["validation"]
ACTIVE_ACTION_PROMPT = get_active_prompts()["action"]
ACTIVE_ANSWER_PROMPT = get_active_prompts()["answer"]
```

The `agent.py` module imports and uses these active prompts:
```python
from medster.prompts import (
    ACTIVE_ACTION_PROMPT,
    ACTIVE_VALIDATION_PROMPT,
    ACTIVE_ANSWER_PROMPT,
)

# Agent uses active prompts throughout
ai_message = call_llm(prompt, system_prompt=ACTIVE_ACTION_PROMPT, tools=TOOLS)
```

---

## Differences Between Modes

### Deterministic Mode (Original Medster)

**Validation Output:**
```json
{"done": true}
```

**Answer Format:**
```
Clinical Analysis:

The patient presents with concerning findings for acute coronary syndrome:
- Troponin: 0.8 ng/mL (significantly elevated, ref <0.04)
- ECG: New T-wave inversions in anterior leads

Differential diagnosis:
1. Acute coronary syndrome (most likely)
2. Myocarditis
3. Takotsubo cardiomyopathy

Recommendation: Urgent cardiology consultation and serial troponins.
```

**Characteristics:**
- Binary task completion (done: true/false)
- Qualitative differential ranking ("most likely", "less likely")
- No quantified uncertainty
- Tool selection based on heuristics

### Bayesian Mode

**Validation Output:**
```json
{
  "done": true,
  "confidence": 0.85,
  "data_completeness": 0.75,
  "uncertainty_factors": [
    "Only 3 of 5 requested lab values available",
    "Vital signs from 48h ago, not current"
  ]
}
```

**Answer Format:**
```
BAYESIAN CLINICAL ANALYSIS:

POSTERIOR PROBABILITY ANALYSIS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Diagnosis               Prior    LR      Posterior   95% CI
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ACS                     20%      49×     78%        [68%, 86%]
Myocarditis            5%       12×     12%        [6%, 21%]
Takotsubo              2%       8×      8%         [3%, 16%]
Other                  73%      0.03×   2%         [0%, 6%]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

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
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CLINICAL DECISION THRESHOLD:
- P(ACS) = 78% >> treatment threshold of 15%
- ACTION: Immediate ACS protocol and cardiology consultation

⚠️  DISCLAIMER: Probabilities are research-grade estimates.
   Clinical judgment required for final decisions.
```

**Characteristics:**
- Confidence scoring on all decisions
- Quantified diagnostic probabilities with CIs
- Explicit likelihood ratios and Bayesian updates
- Information-theoretic test selection
- Uncertainty quantification (entropy)

---

## Configuration Reference

### .env Settings

```bash
# Reasoning Mode Configuration
# Options: "deterministic" | "bayesian"
# Default: "deterministic"
REASONING_MODE=deterministic
```

**Valid values:**
- `deterministic` - Original Medster prompts (default, production-tested)
- `bayesian` - Experimental probabilistic reasoning

**Invalid values:** Any other string defaults to deterministic mode with a warning.

---

## Testing Modes

### Test Deterministic Mode

```bash
# Set mode
echo "REASONING_MODE=deterministic" >> .env

# Run agent
python -m medster.cli

# Test query
medster>> Analyze patient with chest pain, elevated troponin 0.8, ECG with T-wave inversions
```

**Expected:**
- No mode indicator in startup (just "Autonomous Clinical Case Analysis Agent")
- Qualitative differential diagnosis
- No probability estimates
- Standard validation (done: true/false only)

### Test Bayesian Mode

```bash
# Set mode
sed -i '' 's/REASONING_MODE=.*/REASONING_MODE=bayesian/' .env

# Run agent
python -m medster.cli

# Test query
medster>> Analyze patient with chest pain, elevated troponin 0.8, ECG with T-wave inversions
```

**Expected:**
- Startup banner shows "[BAYESIAN MODE]"
- Reasoning mode line appears: "Reasoning Mode: BAYESIAN - Bayesian probabilistic reasoning..."
- Quantified posterior probabilities
- Likelihood ratios and evidence integration
- Information gain recommendations
- Confidence intervals

---

## Troubleshooting

### Mode Not Switching

**Problem:** Changed REASONING_MODE in .env but still seeing old mode

**Solutions:**
1. Verify .env file was saved:
   ```bash
   grep REASONING_MODE .env
   ```

2. Restart the agent (config loaded at startup):
   ```bash
   # Exit current session
   medster>> exit

   # Start new session
   python -m medster.cli
   ```

3. Check for dotenv loading:
   ```bash
   cd ~/Desktop/MDB
   python -c "from medster.config import REASONING_MODE; print(REASONING_MODE)"
   ```

### Import Errors

**Problem:** `ImportError: cannot import name 'BAYESIAN_VALIDATION_SYSTEM_PROMPT'`

**Solution:** Check that `prompts_bayesian.py` exists:
```bash
ls src/medster/prompts_bayesian.py
```

If missing, file was not created. Re-create from `BAYESIAN_PROMPT_ANALYSIS.md`.

### Mode Shows But Prompts Don't Match

**Problem:** Banner shows "BAYESIAN MODE" but output looks deterministic

**Diagnostic:**
```bash
# Check if active prompts are loaded
cd ~/Desktop/MDB
python -c "
from medster.prompts import ACTIVE_PROMPTS
print(ACTIVE_PROMPTS['mode'])
print(ACTIVE_PROMPTS['description'])
"
```

**Expected (Bayesian):**
```
bayesian
Bayesian probabilistic reasoning with uncertainty quantification
```

**Expected (Deterministic):**
```
deterministic
Deterministic clinical analysis (original Medster)
```

---

## Development Workflow

### Making Prompt Changes

**To modify deterministic prompts:**
1. Edit `src/medster/prompts.py`
2. Change `VALIDATION_SYSTEM_PROMPT`, `ACTION_SYSTEM_PROMPT`, or `ANSWER_SYSTEM_PROMPT`
3. Restart agent

**To modify Bayesian prompts:**
1. Edit `src/medster/prompts_bayesian.py`
2. Change `BAYESIAN_VALIDATION_SYSTEM_PROMPT`, `BAYESIAN_ACTION_SYSTEM_PROMPT`, or `BAYESIAN_ANSWER_SYSTEM_PROMPT`
3. Set `REASONING_MODE=bayesian` in .env
4. Restart agent

### Adding New Bayesian Features

1. Update `prompts_bayesian.py` with new prompt logic
2. If needed, extend `ACTIVE_PROMPTS` dictionary in `prompts.py`
3. Update agent.py to use new prompt fields
4. Test both modes to ensure no regressions

---

## Comparison Testing

### Side-by-Side Evaluation

To compare outputs from both modes:

```bash
# Create test query file
cat > test_query.txt <<EOF
Analyze patient: 58yo male, chest pain for 2h, troponin 0.8 ng/mL,
ECG shows new T-wave inversions in V2-V4. BP 145/92, HR 95.
What is the differential diagnosis and recommended workup?
EOF

# Test deterministic mode
sed -i '' 's/REASONING_MODE=.*/REASONING_MODE=deterministic/' .env
python -m medster.cli < test_query.txt > deterministic_output.txt

# Test Bayesian mode
sed -i '' 's/REASONING_MODE=.*/REASONING_MODE=bayesian/' .env
python -m medster.cli < test_query.txt > bayesian_output.txt

# Compare
diff deterministic_output.txt bayesian_output.txt
```

### Key Comparison Points

| Feature | Deterministic | Bayesian |
|---------|---------------|----------|
| Differential Ranking | Qualitative | Quantitative (%) |
| Uncertainty | Implicit | Explicit (entropy, CI) |
| Test Selection | Heuristic | Info gain ranked |
| Validation | Binary | Confidence scored |
| Format | Narrative | Structured tables |

---

## Future Enhancements

Planned additions to Bayesian mode:

1. **Likelihood Ratio Database**
   - Curated LR library from clinical studies
   - PMID references for evidence
   - Regular updates from medical literature

2. **Prior Probability Engine**
   - Epidemiological data integration
   - Age/sex/risk factor adjustments
   - Local population calibration

3. **Information Theory Module**
   - Automated entropy calculation
   - Expected value of information (EVOI)
   - Sequential test optimization

4. **Uncertainty Propagation**
   - Monte Carlo simulation for CI estimation
   - Sensitivity analysis automation
   - Probabilistic graphical models

---

## Best Practices

### When to Use Deterministic Mode

- Production clinical workflows (tested, stable)
- Simple case analysis without complex differential
- When you need concise, narrative output
- If you want faster responses (less structured output)

### When to Use Bayesian Mode

- Research and algorithm development
- Complex diagnostic scenarios with high uncertainty
- When explicit probability estimates are needed
- Teaching/education about diagnostic reasoning
- A/B testing new Bayesian features

### Migration Strategy

1. **Phase 1:** Use deterministic for production, Bayesian for testing (current)
2. **Phase 2:** Clinical validation of Bayesian outputs
3. **Phase 3:** Selective Bayesian for high-uncertainty cases
4. **Phase 4:** Bayesian becomes default (if validated)

---

## Support

For toggle-related issues:

1. Check this guide first
2. Review `BAYESIAN_PROMPT_ANALYSIS.md` for prompt design rationale
3. Examine `prompts.py` and `prompts_bayesian.py` for implementation
4. Test with simple queries before complex cases

---

**Last Updated:** 2025-11-28
**MDB Version:** 0.2.0 (Bayesian fork)
