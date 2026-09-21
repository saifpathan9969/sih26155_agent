# Mission Report
**Goal:** Audit all network configurations and identify critical security compliance violations.
**Summary:** Processed 2/2 devices · Unknown patterns: 1 · Critical: 0 · High: 0 · Medium: 0 · Low: 1

## Findings by device
- **arista_eos_test.conf**: 1 failing checks out of 20 evaluated
  - CIS-LOG-02 (low) — logging.syslog.buffer_size
- **paloalto_test.conf**: 0 failing checks out of 20 evaluated

## Human review requests (grouped)
1. Vendor palo_alto_panos — pattern seen on 1 device(s): paloalto_test.conf — status: rejected
   Raw: set rulebase security rules ADMIN-SSH log-end yes
