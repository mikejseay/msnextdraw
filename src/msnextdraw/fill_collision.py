"""
Begin with an input file found in input/outline.svg, which contains a single enclosed arbitrary
shape. Place a "ball" inside the shape at its centroid, then pick a random direction.
Throw the ball in a straight line in that direction and trace its path. When the ball encounters
the edge of the shape, it should collide and bounce off the edge in a different direction.
Continue this process until the shape is sufficiently filled.
Output the result as an SVG.
"""

from dataclasses import dataclass
import math
from pathlib import Path
import random
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

    def dot(self, other: "Point") -> float:
        return self.x * other.x + self.y * other.y

    def length(self) -> float:
        return math.sqrt(self.x * self.x + self.y * self.y)

    def normalize(self) -> "Point":
        length = self.length()
        if length == 0:
            return Point(0, 0)
        return Point(self.x / length, self.y / length)


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


def line_segment_intersection(
    p1: Point, p2: Point, p3: Point, p4: Point
) -> tuple[Point, float] | None:
    """
    Find the intersection of two line segments (p1-p2 and p3-p4).
    Returns the intersection point and the parameter t along the first segment, or None.
    """
    d1 = p2 - p1
    d2 = p4 - p3
    d3 = p1 - p3

    denom = d1.x * d2.y - d1.y * d2.x
    if abs(denom) < 1e-10:
        return None  # Lines are parallel

    t = (d2.x * d3.y - d2.y * d3.x) / denom
    s = (d1.x * d3.y - d1.y * d3.x) / denom

    if 0 < t <= 1 and 0 <= s <= 1:
        intersection = p1 + d1 * t
        return intersection, t

    return None


def find_first_intersection(
    pos: Point, direction: Point, polygon: list[Point], epsilon: float = 1e-6
) -> tuple[Point, Point, float] | None:
    """
    Find the first intersection of a ray from pos in direction with the polygon edges.
    Returns (intersection_point, edge_normal, distance) or None.
    """
    n = len(polygon)
    best_t = float("inf")
    best_intersection = None
    best_normal = None

    # Cast a long ray
    ray_end = pos + direction * 10000

    for i in range(n):
        p1 = polygon[i]
        p2 = polygon[(i + 1) % n]

        result = line_segment_intersection(pos, ray_end, p1, p2)
        if result is not None:
            intersection, t = result
            # Only consider intersections that are ahead (t > epsilon to avoid self-intersection)
            if t > epsilon and t < best_t:
                best_t = t
                best_intersection = intersection

                # Compute edge normal (perpendicular to edge, pointing inward)
                edge = p2 - p1
                # Normal perpendicular to edge
                normal = Point(-edge.y, edge.x).normalize()

                # Make sure normal points inward (opposite to direction)
                if normal.dot(direction) > 0:
                    normal = Point(-normal.x, -normal.y)

                best_normal = normal

    if best_intersection is not None and best_normal is not None:
        return best_intersection, best_normal, best_t * 10000  # Actual distance

    return None


def reflect_direction(direction: Point, normal: Point) -> Point:
    """Reflect a direction vector off a surface with given normal."""
    # r = d - 2(d·n)n
    dot = direction.dot(normal)
    return direction - 2 * dot * normal


def simulate_bouncing_ball(
    polygon: list[Point],
    num_bounces: int = 100,
    seed: int | None = None,
) -> list[Point]:
    """
    Simulate a ball bouncing inside a polygon.
    Returns the path as a list of points.
    """
    if seed is not None:
        random.seed(seed)

    # Start at centroid
    centroid = compute_centroid(polygon)
    pos = centroid

    # Random initial direction
    angle = random.uniform(0, 2 * math.pi)
    direction = Point(math.cos(angle), math.sin(angle))

    path = [pos]

    for _ in range(num_bounces):
        result = find_first_intersection(pos, direction, polygon)
        if result is None:
            # No intersection found, stop
            break

        intersection, normal, _ = result

        # Move to the intersection point (slightly before to avoid getting stuck)
        pos = intersection

        path.append(pos)

        # Reflect direction
        direction = reflect_direction(direction, normal).normalize()

        # Add small random perturbation to avoid getting stuck in loops
        perturbation = random.uniform(-0.05, 0.05)
        angle = math.atan2(direction.y, direction.x) + perturbation
        direction = Point(math.cos(angle), math.sin(angle))

    return path


def path_to_svg_polyline(
    path: list[Point], stroke_color: str = "blue", stroke_width: float = 0.5
) -> str:
    """Convert a path of points to an SVG polyline element."""
    if len(path) < 2:
        return ""

    points_str = " ".join(f"{p.x},{p.y}" for p in path)
    return (
        f'<polyline points="{points_str}" '
        f'fill="none" stroke="{stroke_color}" stroke-width="{stroke_width}" '
        f'stroke-linecap="round" stroke-linejoin="round" />'
    )


def fill_shape_with_bouncing_ball(
    input_path: str = "input/outline.svg",
    output_path: str = "output/filled.svg",
    num_bounces: int = 500,
    stroke_color: str = "blue",
    stroke_width: float = 0.5,
    seed: int | None = None,
):
    """
    Load an SVG with a single enclosed shape, simulate a bouncing ball inside it,
    and save the result with both the original shape and the ball's path.
    """
    # Read the input SVG as text to preserve original formatting
    with open(input_path, encoding="utf-8") as f:
        svg_content = f.read()

    # Parse to extract path data for collision detection
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

    # Simulate the bouncing ball
    ball_path = simulate_bouncing_ball(polygon, num_bounces=num_bounces, seed=seed)
    print(f"Generated path with {len(ball_path)} points")

    # Create the polyline SVG string
    points_str = " ".join(f"{p.x},{p.y}" for p in ball_path)
    polyline_svg = (
        f'<polyline points="{points_str}" '
        f'fill="none" stroke="{stroke_color}" stroke-width="{stroke_width}" '
        f'stroke-linecap="round" stroke-linejoin="round" />'
    )

    # Find the closing </g> tag of layer1 and insert before it
    # This preserves the original SVG formatting
    import re as regex

    # Find the last </g> before </svg> to insert the polyline
    # Look for the group containing path2
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
    """Main function to run the fill collision simulation."""
    # Get the project root directory
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent.parent

    input_file = project_root / "input" / "outline.svg"
    output_file = project_root / "output" / "fill_collision.svg"

    fill_shape_with_bouncing_ball(
        input_path=str(input_file),
        output_path=str(output_file),
        num_bounces=100,
        stroke_color="blue",
        stroke_width=0.3,
        seed=42,  # For reproducibility
    )


if __name__ == "__main__":
    main()
