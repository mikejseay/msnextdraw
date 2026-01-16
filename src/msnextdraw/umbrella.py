"""
Draw an umbrella from a 2D side-view appearance using geometric shapes.
It can be drawn in the following way:
First, draw a family of arcs formed by projected circles (conic sections / ellipses) becoming more
"compressed" due to foreshortening. Each arc should start from the same origin point.
They should be left-right symmetric (mirrored across a vertical axis).
Make a note of the final positions of each arc.
In the second step, connect the final position of each arc with its neighbor using another smaller
arc that bends upward.
Finally, draw a single line vertically from the origin point down to twice the radius of the circle.
Output the result as an SVG file.
"""

import math
from pathlib import Path


def draw_umbrella(
    output_path: str = "umbrella.svg",
    radius: float = 150,
    num_ribs: int = 8,
    origin_x: float = 200,
    origin_y: float = 50,
    stroke_color: str = "black",
    stroke_width: float = 2,
):
    """
    Draw a 2D side-view of an umbrella and save it as an SVG file.

    Args:
        output_path: Path to save the SVG file
        radius: Radius of the umbrella canopy
        num_ribs: Number of umbrella ribs (sections)
        origin_x: X coordinate of the umbrella top (origin point)
        origin_y: Y coordinate of the umbrella top (origin point)
        stroke_color: Color of the strokes
        stroke_width: Width of the strokes
    """
    # Calculate canvas size
    canvas_width = origin_x * 2
    canvas_height = origin_y + radius + radius * 2 + 50  # canopy + handle + margin

    svg_elements = []

    # Store the endpoints of each rib for connecting arcs
    rib_endpoints = []

    # Step 1: Draw family of arcs (umbrella ribs)
    # Each arc is an ellipse with decreasing vertical radius (foreshortening effect)
    # The arcs spread out from the origin point

    for i in range(num_ribs + 1):
        # Angle for this rib (spread across the front-facing half)
        # Use angles from -pi/2 to pi/2 for the visible portion
        angle = -math.pi / 2 + (math.pi * i / num_ribs)

        # Calculate the foreshortening factor based on viewing angle
        # Ribs at the edges appear more compressed
        foreshortening = abs(math.cos(angle))

        # The horizontal extent of this rib
        x_extent = radius * math.sin(angle)

        # The vertical drop (how far down the rib goes)
        # More foreshortening means less vertical drop for edge ribs
        y_drop = radius * 0.3 * (1 + foreshortening * 0.5)

        # End point of this rib
        end_x = origin_x + x_extent
        end_y = origin_y + y_drop

        rib_endpoints.append((end_x, end_y))

        # Draw the rib as a quadratic bezier curve
        # Control point is below the origin to create the arc
        ctrl_x = origin_x + x_extent * 0.5
        ctrl_y = origin_y + y_drop * 0.3

        path = f'<path d="M {origin_x} {origin_y} Q {ctrl_x} {ctrl_y} {end_x} {end_y}" '
        path += f'fill="none" stroke="{stroke_color}" stroke-width="{stroke_width}" />'
        svg_elements.append(path)

    # Step 2: Connect adjacent rib endpoints with small upward-bending arcs
    # These form the scalloped edge of the umbrella
    for i in range(len(rib_endpoints) - 1):
        x1, y1 = rib_endpoints[i]
        x2, y2 = rib_endpoints[i + 1]

        # Control point for the connecting arc (curves upward)
        mid_x = (x1 + x2) / 2
        # The arc bends upward (negative y offset)
        arc_height = abs(x2 - x1) * 0.3
        mid_y = max(y1, y2) + arc_height  # Curves downward for umbrella edge

        path = f'<path d="M {x1} {y1} Q {mid_x} {mid_y} {x2} {y2}" '
        path += f'fill="none" stroke="{stroke_color}" stroke-width="{stroke_width}" />'
        svg_elements.append(path)

    # Step 3: Draw the handle (vertical line from origin down)
    handle_length = radius * 2
    handle_start_y = origin_y
    handle_end_y = origin_y + handle_length

    # Main handle shaft
    line = f'<line x1="{origin_x}" y1="{handle_start_y}" x2="{origin_x}" y2="{handle_end_y}" '
    line += f'stroke="{stroke_color}" stroke-width="{stroke_width}" />'
    svg_elements.append(line)

    # Add a curved hook at the bottom of the handle
    hook_radius = 15
    hook_path = f'<path d="M {origin_x} {handle_end_y} '
    hook_path += (
        f'A {hook_radius} {hook_radius} 0 0 0 {origin_x - hook_radius * 2} {handle_end_y}" '
    )
    hook_path += f'fill="none" stroke="{stroke_color}" stroke-width="{stroke_width}" />'
    svg_elements.append(hook_path)

    # Add a small tip at the top of the umbrella
    tip_height = 10
    tip = f'<line x1="{origin_x}" y1="{origin_y}" x2="{origin_x}" y2="{origin_y - tip_height}" '
    tip += f'stroke="{stroke_color}" stroke-width="{stroke_width}" />'
    svg_elements.append(tip)

    # Small circle at the very top
    tip_circle = f'<circle cx="{origin_x}" cy="{origin_y - tip_height - 3}" r="3" '
    tip_circle += f'fill="{stroke_color}" />'
    svg_elements.append(tip_circle)

    # Compose the full SVG
    svg_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg"
     width="{canvas_width}" height="{canvas_height}"
     viewBox="0 0 {canvas_width} {canvas_height}">
  <rect width="100%" height="100%" fill="white"/>
  {chr(10).join("  " + elem for elem in svg_elements)}
</svg>'''

    # Write to file
    output = Path(output_path)
    output.write_text(svg_content)
    print(f"Umbrella SVG saved to: {output.absolute()}")

    return svg_content


if __name__ == "__main__":
    # Generate the umbrella SVG
    draw_umbrella("output/umbrella.svg", num_ribs=16)
