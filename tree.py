"""
Draw a sine wave of increasing amplitude and eccentricity so that it resembles
a Christmas tree. Output the result as an SVG file.
"""

import math


def generate_christmas_tree_svg(filename="christmas_tree.svg"):
    # SVG dimensions
    width = 400
    height = 500

    # Tree parameters
    center_x = width / 2
    start_y = 50  # Top of tree
    end_y = 420  # Bottom of tree

    # Sine wave parameters
    num_waves = 18  # Number of complete sine cycles
    points_per_wave = 50  # Resolution of the sine wave
    total_points = num_waves * points_per_wave

    # Generate the tree path using sine wave with increasing amplitude
    path_points = []

    for i in range(total_points + 1):
        # Progress from 0 to 1 (top to bottom)
        t = i / total_points

        # Y position (linear from top to bottom)
        y = start_y + t * (end_y - start_y)

        # Amplitude increases as we go down (creates tree shape)
        # Use exponential growth for more natural tree shape
        base_amplitude = 5
        max_amplitude = 150
        amplitude = base_amplitude + (max_amplitude - base_amplitude) * (t**1.5)

        # Add some eccentricity - vary the amplitude slightly with each wave
        eccentricity = 1 + 0.15 * math.sin(t * math.pi * 3)
        amplitude *= eccentricity

        # Sine wave oscillation
        angle = i / points_per_wave * 2 * math.pi
        x = center_x + amplitude * math.sin(angle)

        path_points.append((x, y))

    # Create SVG path string
    path_d = f"M {path_points[0][0]:.2f} {path_points[0][1]:.2f}"
    for point in path_points[1:]:
        path_d += f" L {point[0]:.2f} {point[1]:.2f}"

    # Generate trunk points (simple rectangle as a path)
    trunk_width = 30
    trunk_height = 50
    trunk_x = center_x - trunk_width / 2
    trunk_y = end_y
    trunk_path = f"M {trunk_x:.2f} {trunk_y:.2f} L {trunk_x + trunk_width:.2f} {trunk_y:.2f} L {trunk_x + trunk_width:.2f} {trunk_y + trunk_height:.2f} L {trunk_x:.2f} {trunk_y + trunk_height:.2f} Z"

    # Generate star at top
    star_points = generate_star(center_x, start_y - 15, 15, 7, 5)
    star_path = f"M {star_points[0][0]:.2f} {star_points[0][1]:.2f}"
    for point in star_points[1:]:
        star_path += f" L {point[0]:.2f} {point[1]:.2f}"
    star_path += " Z"

    # Create SVG content
    svg_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <rect width="100%" height="100%" fill="white"/>
  
  <!-- Star at top -->
  <path d="{star_path}" fill="none" stroke="#DAA520" stroke-width="2"/>
  
  <!-- Tree (sine wave) -->
  <path d="{path_d}" fill="none" stroke="#228B22" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
  
  <!-- Trunk -->
  <path d="{trunk_path}" fill="none" stroke="#8B4513" stroke-width="2"/>
</svg>'''

    # Write to file
    with open(filename, "w") as f:
        f.write(svg_content)

    print(f"Christmas tree SVG saved to {filename}")
    return filename


def generate_star(cx, cy, outer_radius, inner_radius, num_points):
    """Generate points for a star shape."""
    points = []
    for i in range(num_points * 2):
        angle = (i * math.pi / num_points) - math.pi / 2
        if i % 2 == 0:
            r = outer_radius
        else:
            r = inner_radius
        x = cx + r * math.cos(angle)
        y = cy + r * math.sin(angle)
        points.append((x, y))
    return points


if __name__ == "__main__":
    generate_christmas_tree_svg()
