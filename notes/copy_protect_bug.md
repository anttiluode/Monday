# v0.5 integration note: `copy()` does not preserve terminal protection

While adapting FA-BSS0 I noticed that `FreeBinaryArbor.copy()` copies `body`, `morph`, and `mature`, but not the post-bootstrap `protect` mask.  The bootstrap marks the reached source terminal cells as protected; a copied trained arm therefore appears to retain only the soma protection initialized by the constructor.

This predates Monday and also affects the existing v0.5 training pattern (`base.copy()`).  FA-BSS0 should explicitly re-protect the current terminals after copying so source endpoints cannot silently drift during a matched-arm comparison.  FunctionalArbors itself should be checked separately before changing its frozen ledger.
