# Target construction synthetic test report

Scope: synthetic arrays only; no 115-patient method output was read. Tests lock `T = (future_mask > 0.5) AND NOT (current_mask > 0.5)`, bool output, strict shape equality, threshold behavior, empty-target failure policy, and the prohibition on registration/resampling. The final result is populated from the saved protocol pytest output.

Result: PASS. Verified by saved pytest output; relevant checks protocol tests 21–22 pass.
