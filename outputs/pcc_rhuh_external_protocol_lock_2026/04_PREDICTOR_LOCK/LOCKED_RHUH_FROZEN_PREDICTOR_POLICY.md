
# Locked RHUH frozen predictor policy

External Stage A may use only the five frozen `CrossCaseSmallUNet(2,1,16)` checkpoints at internal scientific commit `66269681e4417dccabc68ecaa792d76e19aa5856`. All 5/5 checkpoint SHA-256 values match. Current-only p1/p99 normalization, two-channel input order, float32 forward logic, sigmoid, and equal 0.2 fold weights are immutable.

RHUH training, fine-tuning, calibration, checkpoint selection, test-time adaptation, RHUH-specific normalization tuning, and threshold selection are forbidden. No predictor was loaded or executed during this lock.
