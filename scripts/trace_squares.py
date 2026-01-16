"""
Begin with an input file found in input/outline.svg, which contains a single line of arbitrary
shape. Trace the line by "replaying" its positions as the center point of a square that we will
draw in successive iterations before reaching the end of the line. In each iteration, move the
origin point along the line a small amount and then conect the existing line to the position of one
of the corners of the square with its center. The square should have side length equal to the
shape's longest dimension (width or height) divided by 30. Start at the top left corner and rotate
around the corners in each iteration.
Output the result as an SVG.
"""

from pathlib import Path

from msnextdraw.svg_utils import (
    Point,
    get_bounding_box,
    insert_element_into_svg,
    load_svg_polygon,
    points_to_polyline_svg,
    save_svg,
)


def get_square_corners(center: Point, side_length: float) -> list[Point]:
    """
    Get the four corners of a square centered at the given point.
    Returns corners in order: top-left, top-right, bottom-right, bottom-left.
    """
    half = side_length / 2
    return [
        Point(center.x - half, center.y - half),  # Top-left
        Point(center.x + half, center.y - half),  # Top-right
        Point(center.x + half, center.y + half),  # Bottom-right
        Point(center.x - half, center.y + half),  # Bottom-left
    ]


def trace_line_with_squares(
    line_points: list[Point],
    square_side: float,
) -> list[Point]:
    """
    Trace along a line, connecting to rotating corners of a square centered at each point.

    Args:
        line_points: The points forming the input line/path
        square_side: The side length of the square

    Returns:
        A list of points forming the traced path
    """
    traced_path = []
    corner_index = 0  # Start at top-left corner

    for point in line_points:
        # Get corners of square centered at current point
        corners = get_square_corners(point, square_side)

        # Add the current corner to the path
        traced_path.append(corners[corner_index])

        # Rotate to next corner (0 -> 1 -> 2 -> 3 -> 0 -> ...)
        corner_index = (corner_index + 1) % 4

    return traced_path


def trace_squares_on_path(
    input_path: str = "input/outline.svg",
    output_path: str = "output/trace_squares.svg",
    stroke_color: str = "blue",
    stroke_width: float = 0.5,
):
    """
    Load an SVG with a single line/path, trace it with rotating square corners,
    and save the result with both the original shape and the traced path.
    """
    # Load SVG and extract the path points
    svg_content, line_points = load_svg_polygon(input_path)

    print(f"Parsed path with {len(line_points)} points")

    # Calculate bounding box to determine square size
    min_x, min_y, max_x, max_y = get_bounding_box(line_points)
    width = max_x - min_x
    height = max_y - min_y
    longest_dimension = max(width, height)
    square_side = longest_dimension / 30

    print(f"Bounding box: width={width:.2f}, height={height:.2f}")
    print(f"Square side length: {square_side:.2f}")

    # Generate the traced path
    traced_path = trace_line_with_squares(line_points, square_side)
    print(f"Generated traced path with {len(traced_path)} points")

    # Create the polyline SVG string
    polyline_svg = points_to_polyline_svg(traced_path, stroke_color, stroke_width)

    # Insert into SVG and save
    new_content = insert_element_into_svg(svg_content, polyline_svg)
    save_svg(output_path, new_content)

    print(f"Saved output to {output_path}")


def main():
    """Main function to run the trace squares algorithm."""
    # Get the project root directory
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent

    input_file = project_root / "input" / "outline.svg"
    output_file = project_root / "output" / "trace_squares.svg"

    trace_squares_on_path(
        input_path=str(input_file),
        output_path=str(output_file),
        stroke_color="blue",
        stroke_width=0.3,
    )


if __name__ == "__main__":
    main()
