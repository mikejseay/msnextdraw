"""
First, represent a 2d rectangular room. Place a "spotlight" (small circle) near the bottom left
corner. Draw rays emanating from the "spotlight" towards the top-right corner of the room (perhaps a
75 degree angle from 0 on the unit circle). The spotlight consists of a family of rays whose angles
are slightly spread apart from each other, depending on the initial position relative from the
cirle. In other words, a ray can be made by moving a line representing a circles's radius to its
perimeter and lengthening it. Pretend these rays are like photons, bouncing around the corners of
the room. Output the result as an SVG. Allow the user to input the angle spread, number of rays, and
ray length.
"""

import math
from pathlib import Path


def reflect_ray(
    start_x: float,
    start_y: float,
    angle: float,
    room_width: float,
    room_height: float,
    max_bounces: int = 10,
) -> list[tuple[float, float]]:
    """
    Trace a ray from start position at given angle, bouncing off room walls.

    Args:
        start_x: Starting x position
        start_y: Starting y position
        angle: Initial angle in radians (0 = right, pi/2 = up)
        room_width: Width of the room
        room_height: Height of the room
        max_bounces: Maximum number of reflections

    Returns:
        List of (x, y) points tracing the ray path
    """
    points = [(start_x, start_y)]
    x, y = start_x, start_y
    dx = math.cos(angle)
    dy = -math.sin(angle)  # Negative because SVG y-axis is inverted

    for _ in range(max_bounces):
        # Find the nearest wall intersection
        # Check all four walls and find the closest valid intersection

        min_t = float("inf")
        wall_hit = None

        # Right wall (x = room_width)
        if dx > 0:
            t = (room_width - x) / dx
            if t > 1e-6 and t < min_t:
                new_y = y + t * dy
                if 0 <= new_y <= room_height:
                    min_t = t
                    wall_hit = "right"

        # Left wall (x = 0)
        if dx < 0:
            t = -x / dx
            if t > 1e-6 and t < min_t:
                new_y = y + t * dy
                if 0 <= new_y <= room_height:
                    min_t = t
                    wall_hit = "left"

        # Top wall (y = 0)
        if dy < 0:
            t = -y / dy
            if t > 1e-6 and t < min_t:
                new_x = x + t * dx
                if 0 <= new_x <= room_width:
                    min_t = t
                    wall_hit = "top"

        # Bottom wall (y = room_height)
        if dy > 0:
            t = (room_height - y) / dy
            if t > 1e-6 and t < min_t:
                new_x = x + t * dx
                if 0 <= new_x <= room_width:
                    min_t = t
                    wall_hit = "bottom"

        if wall_hit is None or min_t == float("inf"):
            break

        # Move to intersection point
        x = x + min_t * dx
        y = y + min_t * dy

        # Clamp to room boundaries (handle floating point errors)
        x = max(0, min(room_width, x))
        y = max(0, min(room_height, y))

        points.append((x, y))

        # Reflect the direction based on which wall was hit
        if wall_hit in ("left", "right"):
            dx = -dx  # Reflect horizontally
        else:  # top or bottom
            dy = -dy  # Reflect vertically

    return points


def draw_spotlight_rays(
    output_path: str = "./output/spotlight_rays.svg",
    room_width: float = 600,
    room_height: float = 400,
    spotlight_x: float = 80,
    spotlight_y: float = 320,
    spotlight_radius: float = 15,
    center_angle: float = 75,
    angle_spread: float = 30,
    num_rays: int = 15,
    max_bounces: int = 8,
    stroke_color: str = "#FFD700",
    stroke_width: float = 1.5,
    room_stroke_color: str = "black",
    room_stroke_width: float = 3,
):
    """
    Draw a spotlight shining into a room with rays bouncing off walls.

    Args:
        output_path: Path to save the SVG file
        room_width: Width of the room
        room_height: Height of the room
        spotlight_x: X position of spotlight center
        spotlight_y: Y position of spotlight center
        spotlight_radius: Radius of the spotlight circle
        center_angle: Central angle of the light beam (degrees, 0 = right)
        angle_spread: Total angular spread of the rays (degrees)
        num_rays: Number of rays to draw
        max_bounces: Maximum number of wall bounces per ray
        stroke_color: Color of the light rays
        stroke_width: Width of the ray lines
        room_stroke_color: Color of the room outline
        room_stroke_width: Width of the room outline
    """
    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    # Canvas size with some margin
    margin = 20
    canvas_width = room_width + 2 * margin
    canvas_height = room_height + 2 * margin

    svg_elements = []

    # Draw the room (rectangle)
    room_rect = (
        f'<rect x="{margin}" y="{margin}" width="{room_width}" height="{room_height}" '
        f'fill="none" stroke="{room_stroke_color}" stroke-width="{room_stroke_width}" />'
    )
    svg_elements.append(room_rect)

    # Adjust spotlight position relative to margin
    spot_x = margin + spotlight_x
    spot_y = margin + spotlight_y

    # Draw the spotlight circle
    spotlight_circle = (
        f'<circle cx="{spot_x}" cy="{spot_y}" r="{spotlight_radius}" '
        f'fill="none" stroke="{stroke_color}" stroke-width="2" />'
    )
    svg_elements.append(spotlight_circle)

    # Calculate ray angles
    center_angle_rad = math.radians(center_angle)
    half_spread_rad = math.radians(angle_spread / 2)

    # Generate rays
    for i in range(num_rays):
        if num_rays == 1:
            ray_angle = center_angle_rad
            edge_angle = 0
        else:
            # Distribute rays evenly across the spread
            t = i / (num_rays - 1)  # 0 to 1
            ray_angle = center_angle_rad - half_spread_rad + t * 2 * half_spread_rad
            edge_angle = -half_spread_rad + t * 2 * half_spread_rad

        # Calculate starting point on the spotlight circle's perimeter
        start_x = spotlight_x + spotlight_radius * math.cos(ray_angle)
        start_y = spotlight_y - spotlight_radius * math.sin(ray_angle)  # SVG y is inverted

        # Trace the ray with reflections
        ray_points = reflect_ray(start_x, start_y, ray_angle, room_width, room_height, max_bounces)

        # Convert to SVG path (adjust for margin)
        if len(ray_points) >= 2:
            path_d = f"M {ray_points[0][0] + margin:.2f} {ray_points[0][1] + margin:.2f}"
            for px, py in ray_points[1:]:
                path_d += f" L {px + margin:.2f} {py + margin:.2f}"

            # Vary opacity slightly based on position for visual interest
            opacity = 0.6 + 0.4 * (1 - abs(2 * i / (num_rays - 1) - 1) if num_rays > 1 else 1)

            ray_path = (
                f'<path d="{path_d}" fill="none" stroke="{stroke_color}" '
                f'stroke-width="{stroke_width}" stroke-opacity="{opacity:.2f}" '
                f'stroke-linecap="round" stroke-linejoin="round" />'
            )
            svg_elements.append(ray_path)

    # Create SVG content
    svg_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{canvas_width}" height="{canvas_height}" viewBox="0 0 {canvas_width} {canvas_height}">
  <rect width="100%" height="100%" fill="#1a1a2e"/>
  
  <!-- Room and spotlight -->
  {chr(10).join("  " + elem for elem in svg_elements)}
</svg>'''

    # Write to file
    with open(output_path, "w") as f:
        f.write(svg_content)

    print(f"Spotlight rays SVG saved to {output_path}")
    return output_path


if __name__ == "__main__":
    # Default parameters
    draw_spotlight_rays(
        output_path="./output/spotlight_rays.svg",
        room_width=816,
        room_height=1132,
        spotlight_x=80,
        spotlight_y=320,
        spotlight_radius=15,
        center_angle=75,
        angle_spread=30,
        num_rays=15,
        max_bounces=3,
    )
