"""
Shared utilities for SVG parsing and manipulation.
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


def get_bounding_box(polygon: list[Point]) -> tuple[float, float, float, float]:
    """Get the bounding box of a polygon as (min_x, min_y, max_x, max_y)."""
    if not polygon:
        return (0, 0, 0, 0)

    min_x = min(p.x for p in polygon)
    max_x = max(p.x for p in polygon)
    min_y = min(p.y for p in polygon)
    max_y = max(p.y for p in polygon)

    return (min_x, min_y, max_x, max_y)


# SVG namespace configuration
SVG_NAMESPACES = {
    "": "http://www.w3.org/2000/svg",
    "inkscape": "http://www.inkscape.org/namespaces/inkscape",
    "sodipodi": "http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd",
    "xlink": "http://www.w3.org/1999/xlink",
}


def register_svg_namespaces():
    """Register SVG namespaces with ElementTree."""
    for prefix, uri in SVG_NAMESPACES.items():
        ET.register_namespace(prefix, uri)


def load_svg_polygon(input_path: str) -> tuple[str, list[Point]]:
    """
    Load an SVG file and extract the polygon from the first path element.

    Args:
        input_path: Path to the input SVG file

    Returns:
        Tuple of (svg_content, polygon_points)

    Raises:
        ValueError: If no path element is found or path has no 'd' attribute
    """
    # Read the input SVG as text to preserve original formatting
    with open(input_path, encoding="utf-8") as f:
        svg_content = f.read()

    # Register namespaces
    register_svg_namespaces()

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

    return svg_content, polygon


def points_to_polyline_svg(
    points: list[Point],
    stroke_color: str = "blue",
    stroke_width: float = 0.5,
) -> str:
    """
    Convert a list of points to an SVG polyline element string.

    Args:
        points: List of points forming the path
        stroke_color: Color of the stroke
        stroke_width: Width of the stroke

    Returns:
        SVG polyline element string
    """
    if len(points) < 2:
        return ""

    points_str = " ".join(f"{p.x},{p.y}" for p in points)
    return (
        f'<polyline points="{points_str}" '
        f'fill="none" stroke="{stroke_color}" stroke-width="{stroke_width}" '
        f'stroke-linecap="round" stroke-linejoin="round" />'
    )


def insert_element_into_svg(svg_content: str, element_svg: str) -> str:
    """
    Insert an SVG element into the SVG content, preferably inside layer1.

    Args:
        svg_content: Original SVG content string
        element_svg: SVG element string to insert

    Returns:
        Modified SVG content with element inserted

    Raises:
        ValueError: If no suitable insertion point is found
    """
    # Find the closing </g> tag of layer1 and insert before it
    group_pattern = re.compile(
        r'(<g[^>]*id="layer1"[^>]*>.*?)(</g>\s*</svg>)',
        re.DOTALL | re.IGNORECASE,
    )
    match = group_pattern.search(svg_content)

    if match:
        # Insert element before the closing </g>
        return svg_content[: match.end(1)] + element_svg + svg_content[match.start(2) :]

    # Fallback: insert before </svg>
    svg_close_pattern = re.compile(r"</svg\s*>", re.IGNORECASE)
    svg_match = svg_close_pattern.search(svg_content)
    if svg_match:
        return svg_content[: svg_match.start()] + element_svg + svg_content[svg_match.start() :]

    raise ValueError("Could not find suitable insertion point in SVG")


def save_svg(output_path: str, svg_content: str):
    """
    Save SVG content to a file, creating directories as needed.

    Args:
        output_path: Path to the output file
        svg_content: SVG content to write
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(svg_content)
