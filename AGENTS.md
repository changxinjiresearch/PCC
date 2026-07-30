# PCC Research Project
## AGENTS.md
Version: 2.0

---

# Mission

This repository is the long-term research implementation of the PCC medical image segmentation project.

The objective is to transform one large historical Kaggle notebook into a clean, modular, reproducible, publication-quality research codebase without changing scientific behaviour.

Scientific correctness always has higher priority than code cleanliness.

---

# Repository Authority

The scientific authority is:

archive/pcc-experiments.ipynb

This notebook represents the historical scientific record.

Never rewrite it.

Never simplify it.

Never reorganize it.

Never delete it.

Never auto-format it.

Never use it as the primary development target.

It is READ ONLY.

---

# Migration Authority

Migration is controlled ONLY by

docs/migration_manifest.md

Only migrate modules that already exist inside the manifest.

Never guess migration order.

Never invent module names.

Never invent notebook cell mappings.

If required information is missing:

STOP

Ask the user.

---

# One Module Rule

Exactly ONE migration module per task.

Never migrate multiple modules together.

Each migration must finish before another begins.

A migration is complete only after:

1. implementation
2. verification
3. regression testing
4. user approval

Only then may the next module begin.

---

# Scientific Behaviour

Never intentionally change

• algorithms
• mathematical equations
• thresholds
• preprocessing
• random seeds
• augmentation
• evaluation metrics
• Dice calculations
• IoU calculations
• pathology logic
• correction logic
• PCC equations
• EIA equations

unless explicitly instructed.

Behaviour preservation is mandatory.

---

# Layer Policy

Current project contains multiple historical research layers.

Examples include

Layer 1

Layer 2

Layer 2R

Layer 3

Historical implementations must never be deleted.

If multiple implementations exist:

mark historical versions clearly

identify the final authoritative implementation

never silently replace one with another.

---

# Kaggle Policy

Never

submit notebooks

start GPU training

overwrite outputs

delete datasets

modify Kaggle settings

unless explicitly instructed.

Never perform expensive computation automatically.

---

# Archive Policy

Everything inside

archive/

is permanent.

Never modify.

Never rename.

Never overwrite.

Never delete.

---

# Repository Layout

Source code

src/

Experiments

experiments/

Configurations

configs/

Documentation

docs/

Tests

tests/

Outputs

outputs/

Research artifacts

artifacts/

Historical notebooks

archive/

---

# Coding Policy

Prefer

small modules

deterministic behaviour

explicit dependencies

clear function names

typed interfaces when appropriate

Avoid

magic numbers

global mutable state

duplicated implementations

hidden side effects

unnecessary abstractions

---

# Documentation Policy

Every module should explain

Purpose

Inputs

Outputs

Dependencies

Scientific assumptions

Expected behaviour

Known limitations

If a scientific decision is non-obvious,

document WHY,

not only WHAT.

---

# Testing Policy

Every migrated module requires verification.

Minimum checks:

syntax validation

unit test

light regression test

behaviour comparison

If numerical outputs differ unexpectedly,

STOP.

Report the difference.

Never silently accept behaviour drift.

---

# Regression Policy

Whenever possible compare against

historical notebook outputs

stored metrics

saved predictions

locked evaluation cases

Scientific equivalence is preferred over implementation similarity.

---

# Experiment Policy

Experiments must be reproducible.

Never hard-code machine-specific paths.

Prefer configuration files.

Keep experiment outputs separated from source code.

Never overwrite historical experiment results.

---

# Git Policy

Small commits only.

One logical change per commit.

Never mix unrelated work.

Commit messages should describe scientific intent rather than implementation details.

---

# Security Policy

Never expose credentials.

Never print API keys.

Never access secrets unnecessarily.

Never modify files outside this repository.

Never perform destructive operations without approval.

---

# AI Assistant Behaviour

Before changing any source code:

Explain

• what will change

• why it changes

• notebook authority

• affected files

• verification strategy

Wait for user approval.

Do not continue automatically.

---

# Communication Style

When reporting work:

Use concise technical language.

Clearly distinguish

Observation

Assumption

Decision

Verification

Remaining work

Never hide uncertainty.

If unsure,

say so.

---

# Final Objective

The final repository should become

publication quality

fully reproducible

modular

well documented

easy to review

easy to extend

easy to reproduce

while preserving the scientific behaviour of the original PCC research notebook.
