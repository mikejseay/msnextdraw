"""
Begin with an input file found in input/outline.svg, which contains a single line of arbitrary
shape. Trace the line by "replaying" its positions as the center point of a square that we will
draw in successive iterations before reaching the end of the line. In each iteration, move the
origin point along the line a small amount and then conect the existing line to the position of one
of the corners of the square with its center. Start at the top left corner and rotate around the
corners.
Output the result as an SVG.
"""
