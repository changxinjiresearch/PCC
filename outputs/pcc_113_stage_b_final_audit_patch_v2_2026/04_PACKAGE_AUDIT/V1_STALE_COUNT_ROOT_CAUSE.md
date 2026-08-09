# V1 stale ZIP count root cause

The immutable V1 external summary and the V1 ZIP directory both report 112 files. The immutable V1 `POST_UNPACK_VALIDATION_REPORT.md` reports 111. That value is stale metadata produced before the final package file was included in the final packaging sequence; it does not alter any scientific file or result. V2 counts its ZIP directory dynamically after creation and records the final count in its release summary.
