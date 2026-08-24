# Carrier warning

The current FunctionalArbors detour changes path length by two lattice cells.  Because v0.5 previously measured roughly five simulation frames of edge-delay per lattice edge, a single detour may produce a large carrier-phase move at the existing carrier omega.  That is useful for cancellation, but it may also make the reachable coefficient set coarse.

Therefore sweep carrier frequency only after freezing a default Gate 0.  Do not tune omega to individual mixing matrices.  Report how source-purity changes with omega as a post-hoc expressivity map.
