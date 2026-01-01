<rules_summary>
For each non-zero cell in the input, create new cells around it. The value of the new cells depend on the value of the initial cell. If the initial cell has a value of '1', create '7' around it. If the initial cell has a value of '2', create '4' around it. If the initial cell has a value of '6', create '8' around it. If the initial cell has a value of '8', create '4' around it.
</rules_summary>
<input_generation>
Input grids are provided as examples. The transformation rule must be inferred from the training examples.
</input_generation>
<solution_steps>
1. Iterate over all the cells of input grid.
2. For each cell, check if it is non-zero.
3. If cell is non-zero, create new cells with specific values based on the initial cell around the cell (up, down, left, right).
</solution_steps>
<key_insight>
Some cells with non-zero values are surrounded by 0 values in the input.
</key_insight>
<puzzle_concepts>

</puzzle_concepts>
