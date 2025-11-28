# Bayesian Prompt Analysis & Proposed Enhancements

## Executive Summary

Current Medster prompts support **deterministic clinical reasoning** - they gather data and report findings, but lack **probabilistic uncertainty quantification**. This analysis identifies key integration points for Bayesian reasoning to enhance diagnostic accuracy and confidence estimation.

---

## Current Prompt Architecture Analysis

### 1. **VALIDATION_SYSTEM_PROMPT** (Lines 239-273)

**Current Approach:**
```
Consider a task complete when:
- The requested clinical data has been retrieved
- The data is sufficient to address the task objective
- OR it's clear the data is not available in the system AFTER exploration attempt
```

**Weakness:** Binary completion check (done: true/false) without confidence scoring.

**Bayesian Opportunity:** Add probabilistic confidence in task completion.

**Proposed Enhancement:**
```json
{
  "done": true,
  "confidence": 0.85,
  "uncertainty_factors": [
    "Only 3 of 5 requested lab values available",
    "Vital signs from 48h ago, not current"
  ],
  "data_completeness": 0.75
}
```

**Clinical Impact:** Clinician knows the analysis is 85% confident but missing 25% of ideal data.

---

### 2. **ANSWER_SYSTEM_PROMPT** (Lines 337-400)

**Current Approach:**
```
If clinical data was collected, your answer MUST:
1. DIRECTLY answer the specific clinical question asked
2. Lead with the KEY CLINICAL FINDING or answer in the first sentence
3. Include SPECIFIC VALUES with proper context (reference ranges, units, dates, trends)
...
- Express uncertainty when data is incomplete
```

**Weakness:** "Express uncertainty" is vague - no structured approach to quantifying diagnostic confidence.

**Bayesian Opportunity:** Integrate probabilistic differential diagnosis with likelihood ratios.

**Current Output Example:**
```
Patient presents with chest pain and elevated troponin (0.8 ng/mL, ref <0.04).
ECG shows new T-wave inversions in anterior leads.
Differential includes:
- Acute coronary syndrome
- Myocarditis
- Takotsubo cardiomyopathy
```

**Proposed Bayesian Output:**
```
PROBABILISTIC DIFFERENTIAL DIAGNOSIS:

Prior Probability Assessment (based on epidemiology):
- ACS in 58yo male with chest pain: 15-25% pre-test probability

Bayesian Update with Evidence:
1. Troponin 0.8 ng/mL (LR+ = 8.5 for ACS)
2. New T-wave inversions (LR+ = 3.2 for ACS)
3. Age 58, male (LR+ = 1.8 for ACS)

Posterior Probabilities:
1. Acute Coronary Syndrome: 78% (high confidence)
   - Likelihood Ratio: 8.5 × 3.2 × 1.8 = 48.96
   - Pre-test odds: 0.20 → Post-test odds: 9.8 → Post-test prob: 0.78

2. Myocarditis: 12% (moderate confidence)
   - Elevated troponin consistent but T-wave pattern less typical

3. Takotsubo cardiomyopathy: 8% (low confidence)
   - Demographics less typical (more common in post-menopausal women)

4. Other causes: 2%

Confidence Interval: 95% CI for ACS probability = [68%, 86%]

Recommended Next Steps (Information Gain Analysis):
- Coronary angiography: Expected info gain = 2.4 bits (highest)
- Cardiac MRI: Expected info gain = 1.8 bits
- Serial troponins: Expected info gain = 1.2 bits
```

**Key Additions:**
- Prior probability from epidemiological data
- Explicit likelihood ratios for each finding
- Posterior probability calculation (Bayes' theorem)
- Confidence intervals
- Information gain for test selection

---

### 3. **ACTION_SYSTEM_PROMPT** (Lines 80-237)

**Current Approach:**
```
Decision Process:
1. Read the task description carefully
2. Review any previous tool outputs
3. Determine if more data is needed
4. If more data is needed, select the ONE tool that will provide it
```

**Weakness:** Tool selection is heuristic-based, not information-theoretic.

**Bayesian Opportunity:** Select tools based on **expected information gain** about diagnostic hypotheses.

**Proposed Enhancement - Information-Theoretic Tool Selection:**

Add to ACTION_SYSTEM_PROMPT:
```
Bayesian Tool Selection (Experimental - MDB Enhancement):

When multiple tools could provide relevant data, prioritize by EXPECTED INFORMATION GAIN:

Information Gain Formula:
  IG(test) = H(diagnosis) - E[H(diagnosis | test)]

Where:
  H(diagnosis) = current entropy of diagnostic uncertainty
  E[H(diagnosis | test)] = expected entropy after test result

Practical Guidelines:
1. Calculate current diagnostic uncertainty (entropy)
2. For each candidate tool/test:
   - Estimate probability of positive result given current hypotheses
   - Calculate expected reduction in diagnostic entropy
3. Select tool with HIGHEST expected information gain
4. Break ties using: cost, invasiveness, time-to-result

Example - Patient with suspected PE:

Current Diagnostic Uncertainty:
- P(PE) = 0.40, P(no PE) = 0.60
- Entropy = -0.4*log2(0.4) - 0.6*log2(0.6) = 0.97 bits

Tool Options:
A) D-dimer (high sensitivity, low specificity)
   - Expected IG = 0.31 bits
   - If negative: P(PE) → 0.05 (high info gain)
   - If positive: P(PE) → 0.45 (low info gain)

B) CT-PE (high sensitivity, high specificity)
   - Expected IG = 0.85 bits (HIGHEST)
   - If negative: P(PE) → 0.02
   - If positive: P(PE) → 0.95

C) V/Q scan (moderate sensitivity/specificity)
   - Expected IG = 0.62 bits

DECISION: Select CT-PE (highest information gain = 0.85 bits)
```

---

### 4. **PLANNING_SYSTEM_PROMPT** (Lines 23-78)

**Current Approach:**
```
Task Planning Guidelines:
1. Each task must be SPECIFIC and ATOMIC
2. Tasks should be SEQUENTIAL
3. Include ALL necessary context
```

**Weakness:** No consideration of diagnostic strategy or test ordering based on probability.

**Bayesian Opportunity:** Plan tasks in **optimal diagnostic sequence** using expected information gain.

**Proposed Enhancement:**

Add Bayesian Planning Section:
```
Bayesian Diagnostic Planning (MDB Enhancement):

When planning diagnostic workup, consider OPTIMAL TEST SEQUENCING:

Strategy 1: Sequential Testing (high pre-test probability)
- Start with high-specificity confirmatory tests
- Example: Suspected STEMI → immediate ECG, troponin

Strategy 2: Rule-Out Testing (low pre-test probability)
- Start with high-sensitivity screening tests
- Example: Low-risk PE → D-dimer first

Strategy 3: Information Cascade (moderate probability)
- Order tests by descending information gain
- Update probabilities after each result
- Adapt subsequent tests based on Bayesian updates

Example Task Plan with Bayesian Reasoning:

Query: "58yo male, chest pain, rule out ACS"

Bayesian Analysis:
- Pre-test probability: ~20% (age, symptoms, demographics)
- Differential: ACS (20%), GERD (40%), MSK (30%), Other (10%)

Optimal Task Sequence:
1. Task 1: "Get ECG and initial troponin"
   - High info gain for ACS (LR+ = 5-10 if positive)
   - Guides urgency of subsequent tests

2. Task 2: "Based on ECG/troponin results, calculate post-test ACS probability"
   - Bayesian update with likelihood ratios
   - Determines need for further testing

3. Task 3 (conditional): "If post-test P(ACS) > 0.50, get serial troponins and cardiology consult"
   - Only execute if Bayesian update crosses threshold

4. Task 4 (conditional): "If post-test P(ACS) < 0.10, consider alternative diagnoses (GI, MSK workup)"
   - Adapt based on probability

This is ADAPTIVE planning - task sequence changes based on Bayesian probability updates.
```

---

## Proposed New Prompt: BAYESIAN_ANALYSIS_SYSTEM_PROMPT

**Purpose:** New prompt for probabilistic clinical reasoning component.

```python
BAYESIAN_ANALYSIS_SYSTEM_PROMPT = """You are the Bayesian reasoning component for MDB (Medster-Bayesian-Diagnostics).

Your role is to provide PROBABILISTIC analysis of clinical data to quantify diagnostic uncertainty.

REQUIRED OUTPUT FORMAT:
{
  "prior_probabilities": {
    "diagnosis_1": {"probability": 0.X, "source": "epidemiological data / clinical guidelines"},
    "diagnosis_2": {"probability": 0.Y, "source": "..."}
  },
  "likelihood_ratios": [
    {"finding": "elevated troponin", "LR_positive": 8.5, "LR_negative": 0.1, "source": "PMID:12345"},
    {"finding": "T-wave inversion", "LR_positive": 3.2, "LR_negative": 0.5, "source": "clinical studies"}
  ],
  "posterior_probabilities": {
    "diagnosis_1": {
      "probability": 0.78,
      "confidence_interval_95": [0.68, 0.86],
      "calculation": "Prior × LR1 × LR2 × LR3 / normalization"
    }
  },
  "uncertainty_quantification": {
    "entropy": 0.65,  // bits - lower = more certain
    "missing_data_impact": "Lack of coronary angiography limits definitive diagnosis",
    "sensitivity_analysis": "If troponin were 2.0 instead of 0.8, P(ACS) would be 0.89"
  },
  "information_gain_recommendations": [
    {
      "test": "Coronary angiography",
      "expected_info_gain": 2.4,  // bits
      "expected_probability_shift": "P(ACS): 0.78 → [0.05 if negative, 0.98 if positive]"
    }
  ]
}

LIKELIHOOD RATIO GUIDELINES:
- LR+ > 10: Strong evidence FOR diagnosis
- LR+ 5-10: Moderate evidence FOR
- LR+ 2-5: Weak evidence FOR
- LR+ 1-2: Minimal change
- LR- < 0.1: Strong evidence AGAINST diagnosis
- LR- 0.1-0.2: Moderate evidence AGAINST

PRIOR PROBABILITY SOURCES (in order of preference):
1. Local hospital epidemiological data (if available)
2. National registry data for presenting complaint
3. Meta-analyses and systematic reviews
4. Clinical practice guidelines
5. Expert consensus estimates

UNCERTAINTY QUANTIFICATION:
- Use Beta distributions for probability estimates (captures uncertainty)
- Report 95% confidence/credible intervals
- Calculate entropy to measure diagnostic uncertainty
- Perform sensitivity analysis for key assumptions

CLINICAL INTEGRATION:
- Translate probabilities into clinical action thresholds
- Example: P(PE) > 0.15 → treat, P(PE) < 0.05 → rule out, 0.05-0.15 → more testing
- Consider consequences of false positives vs false negatives
- Adjust thresholds based on clinical context (e.g., lower for high-risk diagnoses)

LIMITATIONS TO ACKNOWLEDGE:
- Likelihood ratios assume conditional independence (often violated in practice)
- Prior probabilities may not reflect local population
- Missing data reduces confidence in posterior estimates
- Clinical judgment required for final decisions - probabilities are TOOLS not ANSWERS
"""
```

---

## Implementation Architecture

### Proposed Bayesian Module Structure

```
src/bayesian/
├── __init__.py
├── priors.py                  # Prior probability databases
├── likelihood_ratios.py       # LR libraries for findings/tests
├── inference.py               # Bayesian computation engine
├── information_theory.py      # Entropy, info gain calculations
└── prompts.py                 # Bayesian-specific prompts
```

### Integration Points in Agent Loop

**Current Flow:**
```
plan_tasks → ask_for_actions → execute_tool → ask_if_done → _generate_answer
```

**Enhanced Bayesian Flow:**
```
plan_tasks (with info gain)
  ↓
ask_for_actions (info-theoretic tool selection)
  ↓
execute_tool
  ↓
bayesian_update (NEW - update probabilities with new data)
  ↓
ask_if_done (with confidence scoring)
  ↓
_generate_answer (with posterior probabilities)
```

### Example Bayesian Update Function

```python
def bayesian_update(current_hypotheses, new_finding, likelihood_ratios):
    """
    Update diagnostic probabilities using Bayes' theorem.

    Args:
        current_hypotheses: Dict of {diagnosis: prior_probability}
        new_finding: Clinical finding or test result
        likelihood_ratios: Dict of {diagnosis: LR_positive or LR_negative}

    Returns:
        Dict of {diagnosis: posterior_probability}
    """
    # Bayes' theorem: P(H|E) = P(E|H) * P(H) / P(E)
    # In odds form: Posterior_odds = LR × Prior_odds

    posteriors = {}
    total_prob = 0

    for diagnosis, prior_prob in current_hypotheses.items():
        prior_odds = prior_prob / (1 - prior_prob)
        lr = likelihood_ratios.get(diagnosis, 1.0)  # LR=1 if not specified
        posterior_odds = lr * prior_odds
        posterior_prob = posterior_odds / (1 + posterior_odds)
        posteriors[diagnosis] = posterior_prob
        total_prob += posterior_prob

    # Normalize to ensure probabilities sum to 1
    normalized = {dx: p/total_prob for dx, p in posteriors.items()}

    return normalized
```

---

## Prompt Modification Strategy

### Phase 1: Confidence Scoring (Low-Hanging Fruit)
- Modify VALIDATION_SYSTEM_PROMPT to return confidence scores
- Add data completeness percentage
- NO code changes to agent loop

### Phase 2: Posterior Probabilities in Answers
- Enhance ANSWER_SYSTEM_PROMPT with Bayesian output format
- LLM generates probabilistic differentials using medical knowledge
- NO code changes to agent loop (LLM does Bayesian reasoning in prompt)

### Phase 3: Information-Theoretic Tool Selection
- Add info gain section to ACTION_SYSTEM_PROMPT
- LLM estimates information gain heuristically
- MINOR code change: parse info gain from LLM response

### Phase 4: Bayesian Module Integration
- Create src/bayesian/ module
- Add bayesian_update() function to agent loop
- Structured probability tracking across tasks

---

## Clinical Validation Requirements

Before clinical use, Bayesian enhancements require:

1. **Likelihood Ratio Database Validation**
   - Verify LR sources (PubMed IDs, clinical guidelines)
   - Test against known clinical scenarios
   - Validate conditional independence assumptions

2. **Prior Probability Calibration**
   - Compare to local hospital data
   - Adjust for patient population differences
   - Update with new epidemiological studies

3. **Uncertainty Quantification Testing**
   - Validate confidence intervals with bootstrap sampling
   - Test sensitivity analysis accuracy
   - Compare to expert physician probability estimates

4. **Clinical Decision Threshold Analysis**
   - Determine optimal P(diagnosis) thresholds for action
   - Cost-effectiveness analysis (false positive vs false negative)
   - Integration with clinical practice guidelines

---

## Example: Before vs After

### Query: "Analyze this patient: 58yo male, chest pain, troponin 0.8, ECG shows T-wave inversions"

**BEFORE (Current Medster):**
```
Clinical Analysis:

The patient presents with concerning findings for acute coronary syndrome:
- Troponin: 0.8 ng/mL (significantly elevated, ref <0.04)
- ECG: New T-wave inversions in anterior leads
- Demographics: 58yo male (cardiac risk factors)

Differential diagnosis:
1. Acute coronary syndrome (most likely)
2. Myocarditis
3. Takotsubo cardiomyopathy

Critical findings requiring immediate attention:
- Elevated troponin indicates myocardial injury
- ECG changes suggest active ischemia

Recommendation: Urgent cardiology consultation and serial troponins.
```

**AFTER (MDB with Bayesian Enhancement):**
```
BAYESIAN CLINICAL ANALYSIS:

POSTERIOR PROBABILITY ANALYSIS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Diagnosis               Prior    LR      Posterior   95% CI
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ACS                     20%      49×     78%        [68%, 86%]
Myocarditis            5%       12×     12%        [6%, 21%]
Takotsubo              2%       8×      8%         [3%, 16%]
Other                  73%      0.03×   2%         [0%, 6%]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

EVIDENCE INTEGRATION:
Finding                     LR+     Impact on ACS Probability
─────────────────────────────────────────────────────────────
Troponin 0.8 ng/mL         8.5×    20% → 66%
T-wave inversions          3.2×    66% → 77%
Age 58, male               1.8×    77% → 78%

DIAGNOSTIC CERTAINTY:
- Entropy: 0.65 bits (moderate uncertainty remains)
- Confidence: HIGH for ACS as leading diagnosis
- Missing data impact: Coronary angiography would provide definitive diagnosis

OPTIMAL NEXT TEST (Information Gain Analysis):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Test                  Info Gain   P(ACS) if +    P(ACS) if -
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Coronary angiography  2.4 bits    98%            5%
Serial troponin       1.2 bits    89%            45%
Cardiac MRI           1.8 bits    92%            22%
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RECOMMENDATION: Coronary angiography (highest information gain)

CLINICAL DECISION THRESHOLD:
- P(ACS) = 78% >> treatment threshold of 15%
- ACTION: Immediate cardiology consultation and ACS protocol
- Sensitivity: If troponin were 2.0, P(ACS) → 89% (still treat)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️  DISCLAIMER: Probabilities are research-grade estimates.
   Clinical judgment required for final diagnostic decisions.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Recommended Implementation Sequence

1. **Week 1-2**: Modify validation prompts for confidence scoring (Phase 1)
2. **Week 3-4**: Enhance answer prompts with Bayesian output format (Phase 2)
3. **Week 5-6**: Add info gain heuristics to action prompts (Phase 3)
4. **Week 7-8**: Build Bayesian module with LR database (Phase 4)
5. **Week 9-10**: Clinical validation and testing

---

## Key Insights

### Strengths of Current Prompts:
- ✅ Clear task decomposition
- ✅ Adaptive optimization (data discovery pattern)
- ✅ Safety guidelines (critical value flagging)
- ✅ MCP integration for specialist analysis

### Gaps for Bayesian Enhancement:
- ❌ No probabilistic uncertainty quantification
- ❌ No likelihood ratio integration
- ❌ No information-theoretic test selection
- ❌ Binary task completion (no confidence scoring)

### Biggest Win:
**ANSWER_SYSTEM_PROMPT enhancement** - Can add Bayesian reasoning to final output with ZERO code changes (LLM does probabilistic reasoning in the prompt). This is the easiest and highest-impact starting point.

---

**Status**: Analysis complete, ready for implementation discussion.
