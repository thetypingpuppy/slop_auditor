# Slop Auditor

## Introduction
In academic papers the devil is in the detail. When using LLM's there is a risk this detail is lost, due to the inherent nature of generalising natural language over a finite number of parameters or weights. In this work, we aim to automatically screen LLM output to double check for any "loss of nuance".

## Method

In machine learning, there is a concept called ensemble learning. The idea is that, given lots of models trained for the same objective, some aggregration of their results is overall more accurate than if used individually. A simple consensus mechanism could be arithmetic mean.

Even better is heterogenous ensemble learning, that combines different models of different *types*.

Here was add a non-LLM based system for detecting logical contradiction in natural language, a cross-encoder known as nli-deberta-v3-large.

The steps are:
1. Parse pdf for section headers based on font size (not a universal approach by any means but seems to work for DSC papers).
2. Extract markdown of pdf, by section.
3. Request a Google Gemini summary of each section, using the previous query/queries as context.
4. Store all the above in a dictionary with headers as keys, and fields for the original text and LLM summary.
5. For every sentence in every section, compare to every sentence of the Gemini summary. Flag any contradictions.

The idea of storing the text by section is that, it may be useful to search Conclusions or Abstracts between different papers for contradictions. Where there are contradictions and a lack of consensus, it may be a good indicator there is room for scientific advacement.

## Example

```
REFERENCE: MPC is an effective solution to the workspace and cueing problem.

  CONTRADICTS

 LLM: The MPC remains idle, allowing the CWF signal to pass through unchanged.
```

In this particular case both these statements are true. In the proposed method, the MPC is used only for a subset of its functionality, so it remains idle a lot of the time. Unlike an LLM, the contradiction detection method used can not consider the context of the whole article.

Indeed, the summary from the LLM is pretty decent, *reflecting well on Gemini's capabilities*:
```
This text outlines a proposed **hybrid motion cueing philosophy** for simulators, designed to combine the practical simplicity of **Classical Washout Filters (CWF)** with the robust workspace-constraint handling of **Model Predictive Control (MPC)**.

### The Core Problem
Current industry-standard CWFs suffer from poor workspace management—relying on "clipping" which introduces motion discontinuities or complex, degradation-prone soft-limiting.
Conversely, full-scale MPC approaches are mathematically intensive, simulator-specific, and difficult for industry practitioners to tune.

### The Proposed Solution:
"MPC-as-a-Filter" - the authors propose a modular architecture that separates the **workspace limiter** from the simulator’s **kinematics**.

### World-Space Limiting
Limiting is performed on driver states (position, velocity, acceleration) in an inertial world coordinate system. This makes the algorithm universal, allowing a single limiter to be applied to any simulator regardless of its physical degrees of freedom.

### Mapping via Look-up Tables (LUTs)
Because analytical models for complex simulator workspaces are often intractable, the authors propose using LUTs or Piecewise Affine Functions (PWAs) to map allowable motion limits based on the current configuration. These can be generated mathematically or through empirical testing.   

### The MPC Limiter
A lightweight, simplified MPC is appended to the standard CWF output.

### Normal Operation
The MPC remains idle, allowing the CWF signal to pass through unchanged.

### Constraint Violation
If a limit is approached, the MPC modifies the signal to maintain feasibility.

### Stability/Recovery
A Proportional-Derivative (PD) controller acts as a closed-loop system to gently steer the simulator back to the CWF reference trajectory once the violation risk has passed.

### Key Advantages
**Ease of Tuning:** Unlike full MPC, this "MPC-as-a-filter" requires minimal parameter tuning. The practitioner only needs to set a **prediction horizon** (to choose between "hard" or "soft" clipping) and prioritize weights (placing workspace safety above acceleration fidelity).

**Unified Workflow:** Simulator facilities managing diverse hardware can use a single, standardized limiting strategy.

**Performance:** It prioritizes "consistency"—a trait highly valued by elite drivers—by ensuring the simulator behaves like a standard CWF during normal driving, only intervening when physical constraints are truly at risk.'
```
