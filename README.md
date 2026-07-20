# Slop Auditor

## Introduction
In academic papers the devil is in the detail. When using LLM's there is a risk this detail is lost, due to the inherent nature of generalising natural language over a finite number of parameters or weights. In this work, we aim to automatically screen LLM outputto double check for any "loss of nuance".

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
