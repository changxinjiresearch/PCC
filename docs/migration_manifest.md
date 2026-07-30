# PCC Scientific Migration Manifest
Version: 2.0

---

# Purpose

This document defines the official migration order for the PCC research repository.

The objective is to transform the historical Kaggle notebook into a modular research codebase while preserving scientific behaviour.

The notebook remains the scientific authority until every migration module has been verified.

---

# General Rules

Every migration must satisfy ALL conditions:

✓ One module only

✓ Behaviour preserved

✓ Regression verified

✓ User approval obtained

Only then may the next module begin.

---

# Migration Status

Each module has one of:

Pending

In Progress

Verified

Completed

Deferred

Historical

---

# Scientific Layers

Layer 1

Current tumour segmentation

Layer 2

Longitudinal prediction

Layer 2R

Final publication-grade PCC implementation

Layer 3

Mechanistic evaluation

Research Operations

Utilities, visualization, reporting and archival

---

# Official Migration Order

---

## Order 1

Module

Dataset Identity

Scientific Layer

Infrastructure

Purpose

Create deterministic dataset discovery and identity utilities.

Includes

dataset roots

case discovery

patient identifiers

file validation

Destination

src/data/dataset_identity.py

Verification

Locked dataset returns identical patient list.

Migration: Completed

Scientific verification: Pending

The canonical locked cohort is still required to confirm that the patient
list is identical.

---

## Order 2

Module

Dataset Loader

Scientific Layer

Infrastructure

Purpose

Load MRI studies and associated metadata.

Destination

src/data/dataset_loader.py

Verification

Loaded case count equals notebook.

Migration: Completed

Scientific verification: Pending

The authoritative cohort is still required to confirm that the loaded case
count equals the notebook.

---

## Order 3

Module

Preprocessing

Scientific Layer

Infrastructure

Purpose

Implement preprocessing exactly matching notebook behaviour.

Destination

src/preprocessing/preprocessing.py

Verification

Pixel-wise comparison against notebook outputs.

Migration: Completed

Scientific verification: Pending

Pixel-wise comparison against outputs from the canonical locked cohort is
still required.

---

## Order 4

Module

Fixed Baseline

Scientific Layer

Layer 1

Purpose

Rebuild independent baseline segmentation.

Destination

src/models/fixed_baseline.py

Verification

Dice and IoU reproduce notebook.

Migration: Completed

Scientific verification: Pending

Regression against the real five-fold checkpoints and canonical locked
cohort is still required. Synthetic checkpoint tests do not complete this
scientific verification.

---

## Order 5

Module

Naive Self-tightening

Scientific Layer

Layer 1

Purpose

Reproduce naïve correction baseline.

Destination

src/models/naive_self_tightening.py

Verification

Metrics agree with notebook.

Status

Pending

---

## Order 6

Module

PCC Core

Scientific Layer

Layer 2R

Purpose

Implement the final PCC correction algorithm.

Destination

src/models/pcc.py

Verification

Locked-case regression.

Status

Pending

---

## Order 7

Module

EIA Methods

Scientific Layer

Layer 2R

Purpose

Implement all EIA comparison methods.

Destination

src/models/eia.py

Verification

Historical comparison reproduced.

Status

Pending

---

## Order 8

Module

Evaluation Metrics

Scientific Layer

Layer 2R

Purpose

Centralize Dice, IoU and evaluation utilities.

Destination

src/evaluation/metrics.py

Verification

Metric outputs identical.

Status

Pending

---

## Order 9

Module

Visualization

Scientific Layer

Research Operations

Purpose

Generate publication-quality figures.

Destination

src/visualization/

Verification

Figures regenerated from saved predictions.

Status

Pending

---

## Order 10

Module

Statistical Analysis

Scientific Layer

Research Operations

Purpose

Generate statistical tables and reports.

Destination

src/statistics/

Verification

Statistics equal notebook.

Status

Pending

---

## Order 11

Module

Experiment Pipeline

Scientific Layer

Research Operations

Purpose

Create reproducible experiment orchestration.

Destination

experiments/

Verification

Smoke test passes.

Status

Pending

---

## Order 12

Module

Artifact Management

Scientific Layer

Research Operations

Purpose

Manage outputs, metadata and checkpoints.

Destination

src/utils/artifacts.py

Verification

Artifacts generated correctly.

Status

Pending

---

## Order 13

Module

Publication Pipeline

Scientific Layer

Research Operations

Purpose

Generate publication tables and figures directly from saved experiment outputs.

Destination

src/publication/

Verification

Publication outputs regenerated without rerunning training.

Status

Pending

---

# Mandatory Verification

Every migration must perform:

1. Syntax validation

2. Unit testing

3. Behaviour comparison

4. Numerical regression

5. Documentation update

6. User approval

No migration skips verification.

---

# Behaviour Priority

Correct scientific behaviour is always more important than code elegance.

Whenever behaviour changes unexpectedly:

STOP

Report the difference.

Do not continue.

---

# Completion Criteria

Migration completes only when:

✓ Every module is Completed

✓ Notebook behaviour is reproduced

✓ Repository is fully modular

✓ All regression tests pass

✓ Documentation is complete

At that point the repository becomes the new implementation authority.
