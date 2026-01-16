"""
Begin with an input file found in input/outline.svg, which contains a single enclosed arbitrary
shape. Fill the shape with a sine wave using the following procedure.
First, pick an angle along which to plot the sine wave (in this case, the angle should be 90
degrees, in other words the sine wave should oscillate around a vertical axis.)
Second, find the center point of the input shape along the perpendicular angle, and center the
midpoint of the sine wave on this center point.
Third, draw a sine wave along the vertical axis and have its amplitude be modulated by the envelope
of the input shape. In other words, the sine wave should "fill" the input shape. Perhaps this can
be done by first measuring the envelope (extent) of the shape away from the vertical axis on either
side, then using this to modulate the sine wave.
"""

import math
from pathlib import Path

from msnextdraw.svg_utils import (
    Point,
    compute_centroid,
    get_bounding_box,
    insert_element_into_svg,
    load_svg_polygon,
    points_to_polyline_svg,
    save_svg,
)


def find_horizontal_extent_at_y(polygon: list[Point], y: float) -> tuple[float, float] | None:
    """
    Find the horizontal extent (min_x, max_x) of the polygon at a given y coordinate.
    This is done by finding all intersections of a horizontal line at y with the polygon edges.
    Returns None if the line doesn't intersect the polygon.
    """
    intersections = []
    n = len(polygon)

    for i in range(n):
        p1 = polygon[i]
        p2 = polygon[(i + 1) % n]

        # Check if the edge crosses the y coordinate
        if (p1.y <= y <= p2.y) or (p2.y <= y <= p1.y):
            # Avoid division by zero for horizontal edges
            if abs(p2.y - p1.y) < 1e-10:
                # Horizontal edge at y level - add both endpoints
                intersections.append(p1.x)
                intersections.append(p2.x)
            else:
                # Calculate x at intersection
                t = (y - p1.y) / (p2.y - p1.y)
                x = p1.x + t * (p2.x - p1.x)
                intersections.append(x)

    if not intersections:
        return None

    return (min(intersections), max(intersections))


def generate_sine_wave_fill(
    polygon: list[Point],
    frequency: float = 0.1,
    num_samples: int = 500,
    amplitude_scale: float = 0.9,
) -> list[Point]:
    """
    Generate a sine wave that fills the shape.

    The sine wave oscillates around a vertical axis (the horizontal center of the shape),
    with its amplitude modulated by the horizontal extent of the shape at each y position.

    Args:
        polygon: The polygon defining the shape boundary
        frequency: The frequency of the sine wave (cycles per unit)
        num_samples: Number of sample points along the vertical axis
        amplitude_scale: Scale factor for amplitude (0-1, where 1 uses full width)

    Returns:
        List of points forming the sine wave path
    """
    # Get bounding box
    min_x, min_y, max_x, max_y = get_bounding_box(polygon)

    # Calculate center x (the vertical axis around which sine wave oscillates)
    centroid = compute_centroid(polygon)
    center_x = centroid.x

    # Generate points along the vertical axis from top to bottom
    path = []
    height = max_y - min_y

    for i in range(num_samples):
        # Current y position (from top to bottom)
        t = i / (num_samples - 1)
        y = min_y + t * height

        # Find the horizontal extent at this y
        extent = find_horizontal_extent_at_y(polygon, y)

        if extent is None:
            continue

        left_x, right_x = extent

        # Calculate maximum amplitude at this y (half the width, scaled)
        max_amplitude = ((right_x - left_x) / 2) * amplitude_scale

        # Calculate sine value at this y
        # The sine wave oscillates along the vertical axis
        sine_value = math.sin(2 * math.pi * frequency * (y - min_y))

        # Calculate x position: center + sine * amplitude
        x = center_x + sine_value * max_amplitude

        # Clamp x to be within the shape bounds (with small margin)
        x = max(left_x + 0.5, min(right_x - 0.5, x))

        path.append(Point(x, y))

    return path


def fill_shape_with_sine_wave(
    input_path: str = "input/outline.svg",
    output_path: str = "output/fill_sine.svg",
    frequency: float = 0.05,
    num_samples: int = 500,
    amplitude_scale: float = 0.9,
    stroke_color: str = "blue",
    stroke_width: float = 0.5,
):
    """
    Load an SVG with a single enclosed shape, generate a sine wave fill,
    and save the result with both the original shape and the sine wave path.

    Args:
        input_path: Path to input SVG file
        output_path: Path to output SVG file
        frequency: Frequency of the sine wave
        num_samples: Number of sample points for the sine wave
        amplitude_scale: Scale factor for amplitude (0-1)
        stroke_color: Color of the sine wave stroke
        stroke_width: Width of the sine wave stroke
    """
    # Load SVG and extract polygon
    svg_content, polygon = load_svg_polygon(input_path)

    print(f"Parsed polygon with {len(polygon)} points")
    print(f"Centroid: {compute_centroid(polygon)}")
    print(f"Bounding box: {get_bounding_box(polygon)}")

    # Generate the sine wave fill
    sine_path = generate_sine_wave_fill(
        polygon,
        frequency=frequency,
        num_samples=num_samples,
        amplitude_scale=amplitude_scale,
    )
    print(f"Generated sine wave with {len(sine_path)} points")

    # Create the polyline SVG string
    polyline_svg = points_to_polyline_svg(sine_path, stroke_color, stroke_width)

    # Insert into SVG and save
    new_content = insert_element_into_svg(svg_content, polyline_svg)
    save_svg(output_path, new_content)

    print(f"Saved output to {output_path}")


def main():
    """Main function to run the sine wave fill."""
    # Get the project root directory
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent

    input_file = project_root / "input" / "outline.svg"
    output_file = project_root / "output" / "fill_sine.svg"

    fill_shape_with_sine_wave(
        input_path=str(input_file),
        output_path=str(output_file),
        frequency=0.1,  # Adjust for more/fewer waves
        num_samples=1000,
        amplitude_scale=0.85,  # Use 85% of available width
        stroke_color="pink",
        stroke_width=0.3,
    )


if __name__ == "__main__":
    main()
