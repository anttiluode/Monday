# FA-BSS0 score and attackers

For a frozen morphology, estimate terminal-to-soma complex gains `H1, H2` at the carrier.  With source mixing matrix `A`, compute `G = [H1, H2] @ A`.

Primary supervised capability score:

`purity = |G_target|^2 / (|G_target|^2 + |G_other|^2 + eps)`.

Also report:

- target leakage ratio `|G_other/G_target|`;
- angular distance between normalized physical `H` and the ideal demixing row from `inv(A)`;
- soma gain, to reject trivial near-zero solutions;
- source-path lengths and measured impulse/phasor delays;
- held-out waveform correlation after freezing anatomy.

Attackers/controls:

1. exact matrix inverse (upper bound for instantaneous noiseless mixing);
2. two-complex-weight optimizer constrained only by output energy normalization;
3. FastICA on the same mixtures;
4. reward-shuffle morphology;
5. anti-reward morphology;
6. geometry-only random search with the same mutation budget.

Do not progress to a blind ICA objective unless the supervised morphology gate passes and the measured physical transfer function explains the separation.
