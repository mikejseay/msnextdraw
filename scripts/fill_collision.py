"""
Begin with an input file found in input/outline.svg, which contains a single enclosed arbitrary
shape. Place a "ball" inside the shape at its centroid, then pick a random direction.
Throw the ball in a straight line in that direction and trace its path. When the ball encounters
the edge of the shape, it should collide and bounce off the edge in a different direction.
Continue this process until the shape is sufficiently filled.
Output the result as an SVG.
"""

import math
from pathlib import Path
import random

from msnextdraw.svg_utils import (
    Point,
    compute_centroid,
    insert_element_into_svg,
    load_svg_polygon,
    points_to_polyline_svg,
    save_svg,
)


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
    # Load SVG and extract polygon
    svg_content, polygon = load_svg_polygon(input_path)

    print(f"Parsed polygon with {len(polygon)} points")
    print(f"Centroid: {compute_centroid(polygon)}")

    # Simulate the bouncing ball
    ball_path = simulate_bouncing_ball(polygon, num_bounces=num_bounces, seed=seed)
    print(f"Generated path with {len(ball_path)} points")

    # Create the polyline SVG string
    polyline_svg = points_to_polyline_svg(ball_path, stroke_color, stroke_width)

    # Insert into SVG and save
    new_content = insert_element_into_svg(svg_content, polyline_svg)
    save_svg(output_path, new_content)

    print(f"Saved output to {output_path}")


def main():
    """Main function to run the fill collision simulation."""
    # Get the project root directory
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent

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
