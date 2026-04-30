"""Theory-of-mind and social relationship modeling.

Each agent maintains a lightweight model of every other agent it has
interacted with: an estimate of that agent's disposition, a trust score,
and a recursive belief about what that agent believes about *them*
(depth-1 theory of mind, which is sufficient to drive emergent cooperation
and reputation dynamics without the combinatorial blowup of deeper
