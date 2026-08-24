# Gate 0 scope warning

FA-BSS0 is deliberately a **single-carrier small-signal demixing gate**.  Its main score uses the frozen morphology's complex transfer vector at `carrier_omega`; the current held-out calculation therefore tests new source amplitudes through that measured transfer model, not a full broadband time-domain separation problem.

Do not report a Gate-0 pass as "FunctionalArbors separates speech" or even as general temporal BSS.

A stronger follow-up must drive slowly varying independent source envelopes through the actual v0.5 time-step dynamics, demodulate the soma, account for physical delay, and score the frozen output against withheld sources.  After that, widen the source bandwidth and move to a frequency-dependent/convolutive problem where IVA/AuxIVA becomes the serious digital opponent.
