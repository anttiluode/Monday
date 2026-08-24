# CONV0 control note

Before the first run, the shuffled-frequency control is frozen to a deterministic reversal of the nine target directions:

```text
[0,1,2,3,4,5,6,7,8] -> [8,7,6,5,4,3,2,1,0]
```

This is intentionally not optimized after looking at arbor behavior. It flips the direction of the target phase progression while keeping exactly the same set of target vectors.
