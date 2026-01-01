<rules_summary>
For each contiguous region of a non-zero value, replace it with the most frequent neighboring non-zero value, excluding zero itself.
</rules_summary>
<input_generation>
Input grids are provided as examples. The transformation rule must be inferred from the training examples.
</input_generation>
<solution_steps>
1. Identify contiguous regions of each non-zero value in the input grid.
2. For each region, find the neighboring non-zero values (excluding zero itself).
3. Determine the most frequent neighboring non-zero value.
4. Replace all values in the region with this most frequent neighboring value.
5. Leave zero values unchanged.
</solution_steps>
<key_insight>
Regions of a consistent non-zero value in the input are transformed.
</key_insight>
<puzzle_concepts>
- color_mapping
- connected
</puzzle_concepts>
