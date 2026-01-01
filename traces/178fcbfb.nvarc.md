<rules_summary>
For each non-zero number at (x, y) in the input, the output has row x filled with that number and column y filled with that number.
</rules_summary>
<input_generation>
Input grids of varying sizes are provided. The transformation maintains relationships between input and output dimensions.
</input_generation>
<solution_steps>
1. Iterate through the input grid.
2. If a cell contains a non-zero number 'n' at (x, y), fill row x and column y of the output grid with 'n'.
</solution_steps>
<key_insight>
The output has the same dimensions as the input.
</key_insight>
<puzzle_concepts>
- color_mapping
- filling
</puzzle_concepts>
