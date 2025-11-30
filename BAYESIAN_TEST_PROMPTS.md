# Bayesian Mode Test Prompts

These prompts test **meta-cognitive optimization** (better tool selection, smarter stopping), NOT output formatting.

---

## ✅ What Bayesian Mode SHOULD Do

**Behind the scenes (invisible to user):**
1. **ACTION phase** - Select tools with highest information gain
2. **VALIDATION phase** - Track confidence and stop when certainty is high enough
3. **ANSWER phase** - Produce normal clinical synthesis (NOT probability tables)

**Measurable improvements:**
- Fewer tool calls to reach same conclusion (efficiency)
- Better tool selection sequence (information gain prioritization)
- Higher confidence validation scores
- More complete data gathering before stopping

---

## 🎯 Test Prompt #1: Tool Selection Efficiency

**Prompt:**
```
Find all patients with diabetes and analyze their most recent HbA1c control. 
Identify patients with poor control (HbA1c > 8%) and summarize medication patterns.
```

**What to observe (Bayesian vs Deterministic):**

**Deterministic mode might:**
1. Call `list_patients` (all patients)
2. Call `get_patient_conditions` for each patient to find diabetes
3. Call `get_patient_labs` for each diabetic patient
4. Filter HbA1c > 8%
5. Call `get_medication_list` for poor control patients
→ Many redundant calls

**Bayesian mode should:**
1. Call `generate_and_run_analysis` ONCE with optimized code to:
   - Load only diabetic patients (filter early)
   - Get HbA1c for diabetics only
   - Filter HbA1c > 8% in code
   - Get medications for filtered set only
→ Fewer API calls, higher information gain per call

**Expected improvement:** 50%+ reduction in tool calls

---

## 🎯 Test Prompt #2: Sequential Test Optimization

**Prompt:**
```
Patient presents with chest pain. I need a comprehensive cardiac workup 
including troponin, ECG findings, and risk stratification. Get all relevant data.
```

**What to observe (Bayesian vs Deterministic):**

**Deterministic mode might:**
- Get labs → Get vitals → Get clinical notes → Get imaging (breadth-first)
- Equal weight to all data sources

**Bayesian mode should:**
- Prioritize troponin FIRST (highest LR+ for ACS, ~8-10)
- If troponin normal: STOP or pivot to alternative diagnosis
- If troponin elevated: Get ECG next (independent information)
- If both abnormal: High confidence, minimal additional testing needed
→ Information gain drives sequential decisions

**Expected improvement:** Smarter stopping (don't gather low-value data after diagnosis clear)

---

## 🎯 Test Prompt #3: Confidence-Based Stopping

**Prompt:**
```
Review patient demographics and current medications. Tell me if there are any 
concerning drug interactions.
```

**What to observe:**

**Deterministic mode:**
- Get demographics → Get medications → Check interactions → DONE
- Validation: Binary "done: true/false"

**Bayesian mode:**
- Get demographics → Get medications → Check interactions
- Validation: "done: true, confidence: 0.95, data_completeness: 1.0"
- Stops early if confidence > 0.9 threshold
- Continues if confidence < 0.7 (incomplete data)

**Expected improvement:** Explicit confidence tracking prevents premature stopping

---

## 🎯 Test Prompt #4: Population Analysis Optimization

**Prompt:**
```
Analyze 100 patients for prevalence of hypertension and average blood pressure control. 
Break down by age groups (<50, 50-65, >65).
```

**What to observe (Bayesian vs Deterministic):**

**Deterministic mode might:**
- Sequential patient processing (patient 1 → patient 2 → ...)
- Separate tool calls for conditions + vitals for each patient

**Bayesian mode should:**
- Use `generate_and_run_analysis` with batch processing
- Single vectorized operation across 100 patients
- Efficient filtering and grouping in generated code
→ Massive parallelization gain

**Expected improvement:** 10x+ speedup for batch operations

---

## 🎯 Test Prompt #5: Missing Data Adaptation

**Prompt:**
```
Get patient's renal function including creatinine, eGFR, and urinalysis. 
Assess for chronic kidney disease staging.
```

**What to observe:**

**Deterministic mode:**
- Get labs → If creatinine missing, report "data not available" → STOP

**Bayesian mode:**
- Get labs → If creatinine missing, check:
  * Validation: "done: false, confidence: 0.4, data_completeness: 0.33"
  * Uncertainty factors: ["Creatinine not available", "Cannot calculate eGFR"]
- ACTION: Try alternative approach (historical labs, calculated from other values)
- Validation: Re-assess confidence after alternative approach
→ Adaptive data gathering

**Expected improvement:** Higher data completeness before stopping

---

## 📊 How to Measure Bayesian Optimization

Run the same prompt in both modes and compare:

**Efficiency Metrics:**
```
Deterministic Mode:
- Tool calls: 15
- Steps: 8
- Time: ~45 seconds
- Confidence: N/A (binary done/not done)

Bayesian Mode:
- Tool calls: 6 (-60%)
- Steps: 4 (-50%)  
- Time: ~20 seconds (-55%)
- Confidence: 0.92 (explicit tracking)
```

**Quality Metrics:**
```
Deterministic Mode:
- Data completeness: Unknown
- Missing critical values: 2
- Redundant data gathered: Yes

Bayesian Mode:
- Data completeness: 0.85 (tracked)
- Missing critical values: 0 (adaptive gathering)
- Redundant data gathered: No (info gain filtering)
```

---

## 🚀 Recommended Test Sequence

1. **Start simple:** Test Prompt #3 (drug interactions) - easy to compare
2. **Measure efficiency:** Test Prompt #4 (population analysis) - clear speedup
3. **Test adaptation:** Test Prompt #5 (missing data) - confidence tracking
4. **Complex scenario:** Test Prompt #2 (sequential testing) - smart stopping
5. **Full optimization:** Test Prompt #1 (diabetes analysis) - all features

---

## ⚠️ What NOT to Expect

**DON'T expect:**
- ❌ Probability tables in output
- ❌ Likelihood ratio citations in final answer
- ❌ Information gain tables
- ❌ Entropy calculations in user-facing text

**DO expect:**
- ✅ Fewer tool calls to reach same conclusion
- ✅ Better tool selection sequence (high-value first)
- ✅ Explicit confidence tracking in validation
- ✅ Normal clinical synthesis in final answer
- ✅ Smarter stopping criteria (confidence-based)

---

## 🔬 The Bayesian Advantage

**Medster in Deterministic Mode:**
- "Train conductor" follows fixed schedule
- Calls tools in standard order
- Stops when checklist complete
- No confidence tracking

**Medster in Bayesian Mode:**
- "Adaptive navigator" optimizes route
- Calls highest-information-gain tools first
- Stops when confidence threshold reached
- Tracks uncertainty throughout

**Result:** Same destination, more efficient journey, higher quality synthesis.

---

**Try it!** Run any of these prompts and watch the tool selection sequence in Bayesian mode.
