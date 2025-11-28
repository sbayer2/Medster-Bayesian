# MDB - Medster with Bayesian Reasoning

**M**edster **B**ayesian **D**iagnostics - An experimental clinical case analysis agent integrating Bayesian reasoning algorithms with autonomous task planning.

## Overview

MDB extends the Medster architecture with probabilistic clinical reasoning. This fork explores Bayesian inference methods for diagnostic uncertainty quantification, differential diagnosis ranking, and clinical decision support under uncertainty.

**Parent Project**: [Medster](https://github.com/sbayer2/Medster) - Autonomous Clinical Case Analysis Agent

## What's Different from Medster?

MDB introduces **Bayesian reasoning capabilities** while preserving Medster's proven multi-agent architecture:

- **Probabilistic Differential Diagnosis** - Bayesian networks for ranked differentials with likelihood ratios
- **Uncertainty Quantification** - Explicit modeling of diagnostic uncertainty and confidence intervals
- **Prior-Posterior Updating** - Dynamic revision of diagnostic probabilities as new evidence emerges
- **Test Selection Optimization** - Information-theoretic test ordering based on expected information gain
- **Risk Stratification** - Bayesian risk models combining clinical scores with patient-specific priors

## Core Architecture

MDB retains Medster's 4-phase execution loop with Bayesian enhancements:

1. **Planning Module** - Task decomposition with probabilistic reasoning steps
2. **Action Module** - Tool selection guided by information gain metrics
3. **Validation Module** - Confidence-aware task completion checks
4. **Synthesis Module** - Bayesian posterior synthesis for clinical recommendations

## Experimental Features (In Development)

- [ ] Bayesian network construction from FHIR data
- [ ] Likelihood ratio computation for diagnostic tests
- [ ] Prior elicitation from epidemiological data
- [ ] Posterior probability visualization
- [ ] Sensitivity analysis for diagnostic uncertainty
- [ ] Integration with clinical decision rules (Bayes + Wells, CURB-65, etc.)

## Requirements

- Python 3.10+
- Anthropic API key (for Claude Sonnet 4.5)
- Coherent Data Set (shared with Medster installation)
- Optional: MCP medical analysis server

## Installation

1. Clone this repository:
```bash
git clone <mdb-repo-url>
cd MDB
```

2. Install dependencies:
```bash
# Using pip
pip install -e .

# Or if you have uv
uv sync
```

3. Configure environment:
```bash
cp env.example .env
```

4. Edit `.env` file:
```bash
# Required: Anthropic API key
ANTHROPIC_API_KEY=sk-ant-your_key_here

# Path to Coherent Data Set (can share with Medster installation)
COHERENT_DATA_PATH=/Users/sbm4_mac/Desktop/Medster/coherent_data/fhir
COHERENT_DICOM_PATH=/Users/sbm4_mac/Desktop/Medster/coherent_data/dicom
COHERENT_DNA_PATH=/Users/sbm4_mac/Desktop/Medster/coherent_data/dna
COHERENT_CSV_PATH=/Users/sbm4_mac/Desktop/Medster/coherent_data/csv

# Optional: MCP server
MCP_SERVER_URL=https://your-mcp-server-url
MCP_DEBUG=true
```

## Usage

Run the interactive CLI:
```bash
python -m medster.cli
```

Or using the entry point:
```bash
medster-agent
```

### Example Queries (Bayesian Mode)

**Probabilistic Differential:**
```
mdb>> Patient: 58yo male, chest pain, troponin 0.8, new T-wave inversions.
      Generate Bayesian differential with likelihood ratios.
```

**Diagnostic Test Selection:**
```
mdb>> Given these symptoms and pre-test probability of PE, which test
      maximizes information gain: D-dimer, CT-PE, or V/Q scan?
```

**Risk Quantification:**
```
mdb>> Calculate posterior probability of STEMI given these ECG findings,
      cardiac markers, and clinical presentation.
```

## Data Sources

### Coherent Data Set (Shared)
MDB uses the same 9GB Coherent Data Set as Medster:
- FHIR resources (1,278 patients)
- DICOM imaging (298 brain MRI scans)
- Genomic data (889 CSV files)
- ECG waveforms
- Clinical notes

**Download**: https://synthea.mitre.org/downloads

**Citation**:
> Walonoski J, et al. The "Coherent Data Set": Combining Patient Data and Imaging in a Comprehensive, Synthetic Health Record. Electronics. 2022; 11(8):1199.

## Development Status

**Current Phase**: Initial development and algorithm integration

This is an **experimental research project** exploring Bayesian methods in clinical AI agents. Features are under active development and not yet production-ready.

## Safety & Disclaimer

**IMPORTANT**: MDB is for research and educational purposes only.

- Experimental Bayesian algorithms require extensive validation
- Not intended for clinical decision-making without expert physician review
- Probability estimates are research-grade, not clinically validated
- Always verify findings with appropriate clinical resources and judgment

## Architecture Details

MDB preserves Medster's multi-agent loop while adding probabilistic reasoning:

**Safety Mechanisms** (inherited from Medster):
- Global step limit: 20 steps
- Per-task step limit: 5 steps
- Loop detection
- Critical value flagging

**Bayesian Enhancements** (in development):
- Prior probability databases
- Likelihood ratio libraries
- Posterior computation engines
- Uncertainty propagation
- Information gain calculators

## Repository Structure

```
MDB/
├── src/medster/          # Core agent code (inherited from Medster)
├── src/bayesian/         # Bayesian reasoning modules (NEW - planned)
├── coherent_data/        # Shared with Medster via .env paths
├── dexter-reference/     # Original Dexter architecture reference
└── .env                  # Configuration (points to shared data)
```

## Relationship to Medster

MDB is a **development fork** of Medster for Bayesian algorithm experimentation:

- **Codebase**: Forked from Medster (maintains architectural compatibility)
- **Data**: Shares Coherent Data Set with Medster (no duplication)
- **Git**: Independent repository (different research direction)
- **Goal**: Explore probabilistic reasoning while preserving Medster's proven agent architecture

Changes tested in MDB may be backported to Medster if successful.

## License

MIT License (inherited from Medster)

## Acknowledgments

- [Medster](https://github.com/sbayer2/Medster) - Parent project providing the autonomous agent architecture
- [Dexter](https://github.com/virattt/dexter) by @virattt - Original multi-agent loop architecture
- [SYNTHEA](https://synthetichealth.github.io/synthea/) - Synthetic patient data
- [Coherent Data Set](https://synthea.mitre.org/downloads) - Multimodal medical research dataset

## Contributing

This is an experimental research project. Contributions welcome for:
- Bayesian network implementations
- Likelihood ratio databases
- Prior probability sources
- Diagnostic test information gain metrics
- Validation studies

---

**Note**: This is a research project exploring Bayesian methods in autonomous medical AI agents. All clinical applications require expert validation and are not suitable for direct patient care.
