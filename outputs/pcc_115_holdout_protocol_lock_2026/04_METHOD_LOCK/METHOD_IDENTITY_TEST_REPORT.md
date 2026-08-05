# Method identity test report

Static and synthetic tests lock all eight methods. Full PCC constants are compared with the 40-case authority, the full `run_variant` branch is numerically compared with canonical `apply_pcc`, and AST inspection requires exactly one `smoothing` conditional. Fixed, Naive and four EIA parameter constants are asserted directly from authoritative source modules. No real 115-patient data is used.

Result: PASS. Verified by saved pytest output; relevant checks protocol tests 18–20 and 42 pass.
