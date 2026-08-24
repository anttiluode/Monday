"""Tiny integration helper for FA-BSS0.

Call `reprotect_terminals(model)` immediately after `base.copy()` when using
FunctionalArbors v0.5, whose current copy() does not preserve the post-bootstrap
terminal protection mask.
"""


def reprotect_terminals(model):
    for which in (0, 1):
        p = model.source_terminal(which)
        if p is not None:
            model.protect[p] = True
    return model
