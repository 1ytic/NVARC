<rules_summary>
For each row, if the row contains 7, the output row is all 0s. If a row contains 6, output row values equal to 8 where original was 0.
</rules_summary>
<input_generation>
Input grids of varying sizes are provided. The transformation maintains relationships between input and output dimensions.
</input_generation>
<solution_steps>
1. Iterate over each row of the input grid.
2. If a row contains the number 7, set all values in the corresponding output row to 0.
3. If a row contains the number 6, then replace all 0 values in the corresponding input row with 8 in the output row.
4. Keep all other rows as zero in output grid.
</solution_steps>
<key_insight>
Input and output grids have the same dimensions.
</key_insight>
<puzzle_concepts>
- color_mapping
- filling
</puzzle_concepts>
