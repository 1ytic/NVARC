<rules_summary>
Replace the 5s with 2s in the output, but only in locations where the corresponding or immediately adjacent locations contain a 5 in the input.
</rules_summary>
<input_generation>
Input grids of varying sizes are provided. The transformation maintains relationships between input and output dimensions.
</input_generation>
<solution_steps>
1. Iterate through the input grid.
2. If a cell in the input grid contains a 5, set the corresponding cell in the output grid to 2.
3. If a cell adjacent to a 5 in the input contains a 5, set the corresponding adjacent cell in the output grid to 2. Otherwise retain values from the input grid.
</solution_steps>
<key_insight>
The input and output grids have the same dimensions.
</key_insight>
<puzzle_concepts>
- color_mapping
</puzzle_concepts>
