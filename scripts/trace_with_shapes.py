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

import math
from pathlib import Path

from msnextdraw.svg_utils import (
    Point,
    get_bounding_box,
    insert_element_into_svg,
    load_svg_polygon,
    points_to_polyline_svg,
    save_svg,
)


def resample_points(points: list[Point], spacing: float = 1.0) -> list[Point]:
    """
    Resample a list of points to create equally spaced points along the path.

    Args:
        points: The original list of points
        spacing: The desired distance between consecutive resampled points

    Returns:
        A new list of points with equal spacing along the path
    """
    if len(points) < 2:
        return points.copy()

    resampled = [points[0]]
    remaining_distance = spacing

    for i in range(len(points) - 1):
        p1 = points[i]
        p2 = points[i + 1]

        # Calculate segment length
        dx = p2.x - p1.x
        dy = p2.y - p1.y
        segment_length = math.sqrt(dx * dx + dy * dy)

        if segment_length == 0:
            continue

        # Direction vector (normalized)
        dir_x = dx / segment_length
        dir_y = dy / segment_length

        # Current position along this segment
        current_pos = 0.0

        # Walk along this segment, placing points at equal intervals
        while current_pos + remaining_distance <= segment_length:
            current_pos += remaining_distance
            new_x = p1.x + dir_x * current_pos
            new_y = p1.y + dir_y * current_pos
            resampled.append(Point(new_x, new_y))
            remaining_distance = spacing

        # Update remaining distance for next segment
        remaining_distance -= segment_length - current_pos

    # Optionally add the last point if it's not too close to the previous one
    last_original = points[-1]
    last_resampled = resampled[-1]
    dist_to_last = math.sqrt(
        (last_original.x - last_resampled.x) ** 2 + (last_original.y - last_resampled.y) ** 2
    )
    if dist_to_last > spacing * 0.5:
        resampled.append(last_original)

    return resampled


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


def get_circle_points(center: Point, radius: float, num_points: int = 12) -> list[Point]:
    """
    Get points evenly distributed around a circle centered at the given point.

    Args:
        center: The center of the circle
        radius: The radius of the circle
        num_points: Number of points around the circle

    Returns:
        List of points around the circle, starting from the top and going clockwise
    """
    points = []
    for i in range(num_points):
        # Start from top (-pi/2) and go clockwise
        angle = -math.pi / 2 + (2 * math.pi * i / num_points)
        x = center.x + radius * math.cos(angle)
        y = center.y + radius * math.sin(angle)
        points.append(Point(x, y))
    return points


def trace_line_with_shapes(
    line_points: list[Point],
    shape_size: float,
    use_circle: bool = False,
    circle_points: int = 12,
) -> list[Point]:
    """
    Trace along a line, connecting to rotating positions of a shape centered at each point.

    Args:
        line_points: The points forming the input line/path
        shape_size: The side length (for square) or diameter (for circle)
        use_circle: If True, use circle positions; if False, use square corners
        circle_points: Number of points around the circle (only used if use_circle=True)

    Returns:
        A list of points forming the traced path
    """
    traced_path = []
    position_index = 0

    num_positions = circle_points if use_circle else 4

    for point in line_points:
        if use_circle:
            # Get points around circle (radius = shape_size / 2)
            positions = get_circle_points(point, shape_size / 2, circle_points)
        else:
            # Get corners of square
            positions = get_square_corners(point, shape_size)

        # Add the current position to the path
        traced_path.append(positions[position_index])

        # Rotate to next position
        position_index = (position_index + 1) % num_positions

    return traced_path


def trace_with_shapes_on_path(
    input_path: str = "input/outline.svg",
    output_path: str = "output/trace_with_shapes.svg",
    stroke_color: str = "blue",
    stroke_width: float = 0.5,
    use_circle: bool = False,
    circle_points: int = 12,
):
    """
    Load an SVG with a single line/path, trace it with rotating shape positions,
    and save the result with both the original shape and the traced path.

    Args:
        input_path: Path to the input SVG file
        output_path: Path to save the output SVG file
        stroke_color: Color of the traced line
        stroke_width: Width of the traced line
        use_circle: If True, use circle positions; if False, use square corners
        circle_points: Number of points around the circle (only used if use_circle=True)
    """
    # Load SVG and extract the path points
    svg_content, line_points = load_svg_polygon(input_path)

    print(f"Parsed path with {len(line_points)} points")

    # Calculate bounding box to determine shape size
    min_x, min_y, max_x, max_y = get_bounding_box(line_points)
    width = max_x - min_x
    height = max_y - min_y
    longest_dimension = max(width, height)
    shape_size = longest_dimension / 30

    print(f"Bounding box: width={width:.2f}, height={height:.2f}")
    shape_type = "circle" if use_circle else "square"
    print(f"Shape: {shape_type}, size: {shape_size:.2f}")

    # Resample points to have equal spacing
    resampled_points = resample_points(line_points, spacing=1.0)
    print(f"Resampled to {len(resampled_points)} evenly spaced points")

    # Generate the traced path
    traced_path = trace_line_with_shapes(
        resampled_points, shape_size, use_circle=use_circle, circle_points=circle_points
    )
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
    output_file = project_root / "output" / "trace_with_shapes.svg"

    trace_with_shapes_on_path(
        input_path=str(input_file),
        output_path=str(output_file),
        stroke_color="blue",
        stroke_width=0.3,
        use_circle=True,  # Set to False for square corners
        circle_points=12,
    )


if __name__ == "__main__":
    main()
