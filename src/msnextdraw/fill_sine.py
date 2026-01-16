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

from dataclasses import dataclass
import math
from pathlib import Path
import re
import xml.etree.ElementTree as ET


@dataclass
class Point:
    """A 2D point."""

    x: float
    y: float

    def __add__(self, other: "Point") -> "Point":
        return Point(self.x + other.x, self.y + other.y)

    def __sub__(self, other: "Point") -> "Point":
        return Point(self.x - other.x, self.y - other.y)

    def __mul__(self, scalar: float) -> "Point":
        return Point(self.x * scalar, self.y * scalar)

    def __rmul__(self, scalar: float) -> "Point":
        return self.__mul__(scalar)


def parse_svg_path(path_d: str) -> list[Point]:
    """
    Parse an SVG path 'd' attribute into a list of points.
    Handles M, m, L, l, H, h, V, v, C, c, S, s, Q, q, T, t, Z, z commands.
    Curves are approximated by sampling points along them.
    """
    points = []
    current = Point(0, 0)
    start = Point(0, 0)

    # Tokenize the path
    tokens = re.findall(r"[MmLlHhVvCcSsQqTtZz]|[-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?", path_d)

    i = 0
    command = None
    last_control = None  # For smooth curves

    def get_number() -> float:
        nonlocal i
        if i < len(tokens):
            val = float(tokens[i])
            i += 1
            return val
        return 0

    def sample_cubic_bezier(p0: Point, p1: Point, p2: Point, p3: Point, samples: int = 10):
        """Sample points along a cubic bezier curve."""
        pts = []
        for t in range(1, samples + 1):
            t_norm = t / samples
            t2 = t_norm * t_norm
            t3 = t2 * t_norm
            mt = 1 - t_norm
            mt2 = mt * mt
            mt3 = mt2 * mt
            x = mt3 * p0.x + 3 * mt2 * t_norm * p1.x + 3 * mt * t2 * p2.x + t3 * p3.x
            y = mt3 * p0.y + 3 * mt2 * t_norm * p1.y + 3 * mt * t2 * p2.y + t3 * p3.y
            pts.append(Point(x, y))
        return pts

    def sample_quadratic_bezier(p0: Point, p1: Point, p2: Point, samples: int = 10):
        """Sample points along a quadratic bezier curve."""
        pts = []
        for t in range(1, samples + 1):
            t_norm = t / samples
            mt = 1 - t_norm
            x = mt * mt * p0.x + 2 * mt * t_norm * p1.x + t_norm * t_norm * p2.x
            y = mt * mt * p0.y + 2 * mt * t_norm * p1.y + t_norm * t_norm * p2.y
            pts.append(Point(x, y))
        return pts

    while i < len(tokens):
        token = tokens[i]

        if token.isalpha():
            command = token
            i += 1
        elif command is None:
            i += 1
            continue

        if command == "M":
            x, y = get_number(), get_number()
            current = Point(x, y)
            start = current
            points.append(current)
            command = "L"  # Subsequent coords are line-to
        elif command == "m":
            dx, dy = get_number(), get_number()
            current = current + Point(dx, dy)
            start = current
            points.append(current)
            command = "l"
        elif command == "L":
            x, y = get_number(), get_number()
            current = Point(x, y)
            points.append(current)
        elif command == "l":
            dx, dy = get_number(), get_number()
            current = current + Point(dx, dy)
            points.append(current)
        elif command == "H":
            x = get_number()
            current = Point(x, current.y)
            points.append(current)
        elif command == "h":
            dx = get_number()
            current = current + Point(dx, 0)
            points.append(current)
        elif command == "V":
            y = get_number()
            current = Point(current.x, y)
            points.append(current)
        elif command == "v":
            dy = get_number()
            current = current + Point(0, dy)
            points.append(current)
        elif command == "C":
            x1, y1 = get_number(), get_number()
            x2, y2 = get_number(), get_number()
            x, y = get_number(), get_number()
            p0 = current
            p1 = Point(x1, y1)
            p2 = Point(x2, y2)
            p3 = Point(x, y)
            points.extend(sample_cubic_bezier(p0, p1, p2, p3))
            current = p3
            last_control = p2
        elif command == "c":
            dx1, dy1 = get_number(), get_number()
            dx2, dy2 = get_number(), get_number()
            dx, dy = get_number(), get_number()
            p0 = current
            p1 = current + Point(dx1, dy1)
            p2 = current + Point(dx2, dy2)
            p3 = current + Point(dx, dy)
            points.extend(sample_cubic_bezier(p0, p1, p2, p3))
            current = p3
            last_control = p2
        elif command == "S":
            x2, y2 = get_number(), get_number()
            x, y = get_number(), get_number()
            p0 = current
            # Reflect the last control point
            p1 = current + (current - last_control) if last_control else current
            p2 = Point(x2, y2)
            p3 = Point(x, y)
            points.extend(sample_cubic_bezier(p0, p1, p2, p3))
            current = p3
            last_control = p2
        elif command == "s":
            dx2, dy2 = get_number(), get_number()
            dx, dy = get_number(), get_number()
            p0 = current
            p1 = current + (current - last_control) if last_control else current
            p2 = current + Point(dx2, dy2)
            p3 = current + Point(dx, dy)
            points.extend(sample_cubic_bezier(p0, p1, p2, p3))
            current = p3
            last_control = p2
        elif command == "Q":
            x1, y1 = get_number(), get_number()
            x, y = get_number(), get_number()
            p0 = current
            p1 = Point(x1, y1)
            p2 = Point(x, y)
            points.extend(sample_quadratic_bezier(p0, p1, p2))
            current = p2
            last_control = p1
        elif command == "q":
            dx1, dy1 = get_number(), get_number()
            dx, dy = get_number(), get_number()
            p0 = current
            p1 = current + Point(dx1, dy1)
            p2 = current + Point(dx, dy)
            points.extend(sample_quadratic_bezier(p0, p1, p2))
            current = p2
            last_control = p1
        elif command == "T":
            x, y = get_number(), get_number()
            p0 = current
            p1 = current + (current - last_control) if last_control else current
            p2 = Point(x, y)
            points.extend(sample_quadratic_bezier(p0, p1, p2))
            current = p2
            last_control = p1
        elif command == "t":
            dx, dy = get_number(), get_number()
            p0 = current
            p1 = current + (current - last_control) if last_control else current
            p2 = current + Point(dx, dy)
            points.extend(sample_quadratic_bezier(p0, p1, p2))
            current = p2
            last_control = p1
        elif command in ("Z", "z"):
            if points and (points[-1].x != start.x or points[-1].y != start.y):
                points.append(start)
            current = start
            command = None
        else:
            i += 1

    return points


def compute_centroid(polygon: list[Point]) -> Point:
    """Compute the centroid of a polygon."""
    if not polygon:
        return Point(0, 0)

    # Use the signed area formula for centroid
    cx, cy = 0.0, 0.0
    signed_area = 0.0
    n = len(polygon)

    for i in range(n):
        x0, y0 = polygon[i].x, polygon[i].y
        x1, y1 = polygon[(i + 1) % n].x, polygon[(i + 1) % n].y
        cross = x0 * y1 - x1 * y0
        signed_area += cross
        cx += (x0 + x1) * cross
        cy += (y0 + y1) * cross

    if abs(signed_area) < 1e-10:
        # Fallback to simple average
        return Point(
            sum(p.x for p in polygon) / n,
            sum(p.y for p in polygon) / n,
        )

    signed_area *= 0.5
    cx /= 6 * signed_area
    cy /= 6 * signed_area

    return Point(cx, cy)


def get_bounding_box(polygon: list[Point]) -> tuple[float, float, float, float]:
    """Get the bounding box of a polygon as (min_x, min_y, max_x, max_y)."""
    if not polygon:
        return (0, 0, 0, 0)

    min_x = min(p.x for p in polygon)
    max_x = max(p.x for p in polygon)
    min_y = min(p.y for p in polygon)
    max_y = max(p.y for p in polygon)

    return (min_x, min_y, max_x, max_y)


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
    # Read the input SVG as text to preserve original formatting
    with open(input_path, encoding="utf-8") as f:
        svg_content = f.read()

    # Register namespaces first
    namespaces = {
        "": "http://www.w3.org/2000/svg",
        "inkscape": "http://www.inkscape.org/namespaces/inkscape",
        "sodipodi": "http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd",
        "xlink": "http://www.w3.org/1999/xlink",
    }
    for prefix, uri in namespaces.items():
        ET.register_namespace(prefix, uri)

    root = ET.fromstring(svg_content)

    # Find the path element (try various namespace approaches)
    path_elem = root.find(".//{http://www.w3.org/2000/svg}path")
    if path_elem is None:
        path_elem = root.find(".//path")

    if path_elem is None:
        raise ValueError("No path element found in the SVG")

    # Get the 'd' attribute
    path_d = path_elem.get("d")
    if not path_d:
        raise ValueError("Path element has no 'd' attribute")

    # Parse the path into points
    polygon = parse_svg_path(path_d)

    if len(polygon) < 3:
        raise ValueError("Path does not form a valid polygon")

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
    points_str = " ".join(f"{p.x},{p.y}" for p in sine_path)
    polyline_svg = (
        f'<polyline points="{points_str}" '
        f'fill="none" stroke="{stroke_color}" stroke-width="{stroke_width}" '
        f'stroke-linecap="round" stroke-linejoin="round" />'
    )

    # Find the closing </g> tag of layer1 and insert before it
    import re as regex

    # Look for the group containing layer1
    group_pattern = regex.compile(
        r'(<g[^>]*id="layer1"[^>]*>.*?)(</g>\s*</svg>)',
        regex.DOTALL | regex.IGNORECASE,
    )
    match = group_pattern.search(svg_content)

    if match:
        # Insert polyline before the closing </g>
        new_content = svg_content[: match.end(1)] + polyline_svg + svg_content[match.start(2) :]
    else:
        # Fallback: insert before </svg>
        svg_close_pattern = regex.compile(r"</svg\s*>", regex.IGNORECASE)
        svg_match = svg_close_pattern.search(svg_content)
        if svg_match:
            new_content = (
                svg_content[: svg_match.start()] + polyline_svg + svg_content[svg_match.start() :]
            )
        else:
            raise ValueError("Could not find suitable insertion point in SVG")

    # Ensure output directory exists
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Write the output SVG
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(new_content)

    print(f"Saved output to {output_path}")


def main():
    """Main function to run the sine wave fill."""
    # Get the project root directory
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent.parent

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
