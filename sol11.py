"""
Sol LeWitt's Wall Drawing #11 (1969)
"A wall divided horizontally and vertically into four equal parts.
Within each part, three of the four kinds of lines are superimposed."

The four kinds of lines are: horizontal, vertical, and both diagonals.

This Python adaptation supports multiple modes:
- animation: Animated display using py5 (similar to original p5.js)
- single: Single frame display using py5
- svg: Export single frame to SVG file
- plotter: Draw directly using NextDraw plotter

Original JavaScript by Michael Seay, January 2022
Python adaptation, December 2025
"""

import argparse
from dataclasses import dataclass, field
from typing import Literal

# Line type constants
LINE_HORIZONTAL = 0
LINE_DIAGONAL_1 = 1  # Bottom-left to top-right
LINE_VERTICAL = 2
LINE_DIAGONAL_2 = 3  # Top-left to bottom-right


@dataclass
class Sol11Drawing:
    """
    Generates line coordinates for Sol LeWitt's Wall Drawing #11.
    
    The canvas is divided into four quadrants, each showing three of four line types.
    Each quadrant skips the line type whose index matches the quadrant index.
    """
    
    # Canvas dimensions (in abstract units - can be pixels, mm, inches, etc.)
    width: float = 500.0
    height: float = 500.0
    
    # Line spacing
    line_spacing: float = 50.0
    
    # Phase offsets for each line type (controls position within spacing)
    horizontal_phase: float = 0.0
    vertical_phase: float = 0.0
    diagonal_phase_1: float = 0.0
    diagonal_phase_2: float = 0.0
    
    # Animation speeds (units per frame)
    horizontal_speed: float = 1.25
    vertical_speed: float = 1.0
    diagonal_speed_1: float = 0.75
    diagonal_speed_2: float = 0.5
    
    # Quadrant mapping: quadrant_index -> (x_offset, y_offset)
    # 0: top-right, 1: top-left, 2: bottom-right, 3: bottom-left
    _quadrant_map: dict = field(init=False)
    
    def __post_init__(self):
        self._update_quadrant_map()
    
    def _update_quadrant_map(self):
        """Update quadrant positions based on current dimensions."""
        hw = self.width / 2
        hh = self.height / 2
        self._quadrant_map = {
            0: (hw, 0),      # Top-right - skips horizontal
            1: (0, 0),       # Top-left - skips diagonal_1
            2: (hw, hh),     # Bottom-right - skips vertical
            3: (0, hh),      # Bottom-left - skips diagonal_2
        }
    
    def set_dimensions(self, width: float, height: float):
        """Update canvas dimensions."""
        self.width = width
        self.height = height
        self._update_quadrant_map()
    
    def advance_animation(self):
        """Advance all phases by their respective speeds (for animation mode)."""
        self.horizontal_phase = (self.horizontal_phase + self.horizontal_speed) % self.line_spacing
        self.vertical_phase = (self.vertical_phase + self.vertical_speed) % self.line_spacing
        self.diagonal_phase_1 = (self.diagonal_phase_1 + self.diagonal_speed_1) % self.line_spacing
        self.diagonal_phase_2 = (self.diagonal_phase_2 + self.diagonal_speed_2) % self.line_spacing
    
    def set_frame(self, frame_index: int):
        """Set phases to a specific frame index."""
        self.horizontal_phase = (self.horizontal_speed * frame_index) % self.line_spacing
        self.vertical_phase = (self.vertical_speed * frame_index) % self.line_spacing
        self.diagonal_phase_1 = (self.diagonal_speed_1 * frame_index) % self.line_spacing
        self.diagonal_phase_2 = (self.diagonal_speed_2 * frame_index) % self.line_spacing
    
    def get_quadrant_dividers(self) -> list[tuple[float, float, float, float]]:
        """Return the two lines dividing the canvas into quadrants."""
        return [
            (self.width / 2, 0, self.width / 2, self.height),  # Vertical divider
            (0, self.height / 2, self.width, self.height / 2),  # Horizontal divider
        ]
    
    def _get_horizontal_lines(self, qx: float, qy: float) -> list[tuple[float, float, float, float]]:
        """Generate horizontal lines for a quadrant."""
        lines = []
        hw = self.width / 2
        hh = self.height / 2
        
        y = qy + self.horizontal_phase
        y_end = qy + hh - 1
        while y <= y_end:
            lines.append((qx, y, qx + hw, y))
            y += self.line_spacing
        return lines
    
    def _get_vertical_lines(self, qx: float, qy: float) -> list[tuple[float, float, float, float]]:
        """Generate vertical lines for a quadrant."""
        lines = []
        hw = self.width / 2
        hh = self.height / 2
        
        x = qx + self.vertical_phase
        x_end = qx + hw - 1
        while x <= x_end:
            lines.append((x, qy, x, qy + hh))
            x += self.line_spacing
        return lines
    
    def _get_diagonal_1_lines(self, qx: float, qy: float) -> list[tuple[float, float, float, float]]:
        """Generate diagonal lines (bottom-left to top-right) for a quadrant."""
        lines = []
        hw = self.width / 2
        hh = self.height / 2
        
        d = self.diagonal_phase_1
        d_end = self.diagonal_phase_1 + hw - 1
        while d <= d_end:
            # Lower triangle part
            lines.append((qx, qy + hh - d, qx + d, qy + hh))
            # Upper triangle part
            lines.append((qx + d, qy, qx + hw, qy + hh - d))
            d += self.line_spacing
        return lines
    
    def _get_diagonal_2_lines(self, qx: float, qy: float) -> list[tuple[float, float, float, float]]:
        """Generate diagonal lines (top-left to bottom-right) for a quadrant."""
        lines = []
        hw = self.width / 2
        hh = self.height / 2
        
        d = self.diagonal_phase_2
        d_end = self.diagonal_phase_2 + hh - 1
        while d <= d_end:
            # Right part
            lines.append((qx + d, qy + hh, qx + hw, qy + d))
            # Left part
            lines.append((qx, qy + d, qx + d, qy))
            d += self.line_spacing
        return lines
    
    def get_lines_for_quadrant(self, quadrant_index: int) -> list[tuple[float, float, float, float]]:
        """
        Get all lines for a specific quadrant.
        Each quadrant skips the line type whose index matches the quadrant index.
        
        Returns list of (x1, y1, x2, y2) tuples.
        """
        qx, qy = self._quadrant_map[quadrant_index]
        lines = []
        
        line_generators = {
            LINE_HORIZONTAL: self._get_horizontal_lines,
            LINE_DIAGONAL_1: self._get_diagonal_1_lines,
            LINE_VERTICAL: self._get_vertical_lines,
            LINE_DIAGONAL_2: self._get_diagonal_2_lines,
        }
        
        for line_type, generator in line_generators.items():
            if line_type != quadrant_index:  # Skip the matching line type
                lines.extend(generator(qx, qy))
        
        return lines
    
    def get_all_lines(self) -> list[tuple[float, float, float, float]]:
        """Get all lines for the entire drawing."""
        lines = []
        for quadrant_index in range(4):
            lines.extend(self.get_lines_for_quadrant(quadrant_index))
        return lines


# =============================================================================
# py5 Display Mode
# =============================================================================

def run_py5_display(mode: Literal["animation", "single"], frame_index: int = 0):
    """Run the drawing using py5 for display."""
    import py5
    
    drawing = Sol11Drawing()
    
    def setup():
        py5.size(500, 500)
        py5.background(255)
        py5.stroke_weight(1)
        py5.stroke(0)
        drawing.set_dimensions(py5.width, py5.height)
        drawing.line_spacing = py5.height * 0.1
        
        if mode == "single":
            drawing.set_frame(frame_index)
            py5.no_loop()
    
    def draw():
        py5.clear()
        py5.background(255)
        
        if mode == "animation":
            drawing.advance_animation()
        
        # Draw quadrant dividers
        for x1, y1, x2, y2 in drawing.get_quadrant_dividers():
            py5.line(x1, y1, x2, y2)
        
        # Draw all lines
        for x1, y1, x2, y2 in drawing.get_all_lines():
            py5.line(x1, y1, x2, y2)
    
    py5.run_sketch(sketch_functions={"setup": setup, "draw": draw})


# =============================================================================
# SVG Export Mode
# =============================================================================

def export_svg(output_path: str, size_inches: float = 6.0, frame_index: int = 0):
    """Export a single frame to SVG file."""
    import svgwrite
    
    # Convert inches to mm for SVG
    size_mm = size_inches * 25.4
    
    # Create drawing with canvas units matching mm
    drawing = Sol11Drawing(width=size_mm, height=size_mm)
    drawing.line_spacing = size_mm * 0.1
    drawing.set_frame(frame_index)
    
    # Create SVG
    dwg = svgwrite.Drawing(
        output_path,
        size=(f"{size_mm}mm", f"{size_mm}mm"),
        viewBox=f"0 0 {size_mm} {size_mm}"
    )
    
    # Style for lines
    line_style = {"stroke": "black", "stroke-width": "0.3mm", "fill": "none"}
    
    # Draw quadrant dividers
    for x1, y1, x2, y2 in drawing.get_quadrant_dividers():
        dwg.add(dwg.line((x1, y1), (x2, y2), **line_style))
    
    # Draw all lines
    for x1, y1, x2, y2 in drawing.get_all_lines():
        dwg.add(dwg.line((x1, y1), (x2, y2), **line_style))
    
    dwg.save()
    print(f"SVG saved to: {output_path}")


# =============================================================================
# NextDraw Plotter Mode
# =============================================================================

def run_plotter(size_inches: float = 6.0, frame_index: int = 0, dry_run: bool = False):
    """Draw directly using NextDraw plotter."""
    from nextdraw import NextDraw
    
    # Convert inches to mm
    size_mm = size_inches * 25.4
    
    # Create drawing with canvas units in mm
    drawing = Sol11Drawing(width=size_mm, height=size_mm)
    drawing.line_spacing = size_mm * 0.1
    drawing.set_frame(frame_index)
    
    # Collect all lines (dividers + pattern lines)
    all_lines = drawing.get_quadrant_dividers() + drawing.get_all_lines()
    
    if dry_run:
        print(f"Dry run: would draw {len(all_lines)} lines")
        print(f"Canvas size: {size_mm:.1f}mm x {size_mm:.1f}mm ({size_inches}\" x {size_inches}\")")
        return
    
    # Initialize NextDraw
    nd = NextDraw()
    nd.interactive()
    nd.options.units = 2  # mm
    nd.options.speed_pendown = 25
    nd.options.speed_penup = 75
    
    if not nd.connect():
        print("Error: Could not connect to NextDraw plotter")
        return
    
    try:
        print(f"Drawing {len(all_lines)} lines...")
        
        # Offset to center on the page (assuming 11" x 8.5" travel area)
        # Center horizontally: (11" - size) / 2
        # Center vertically: (8.5" - size) / 2
        offset_x = (11 * 25.4 - size_mm) / 2
        offset_y = (8.5 * 25.4 - size_mm) / 2
        
        for i, (x1, y1, x2, y2) in enumerate(all_lines):
            # Apply offset
            x1_mm = x1 + offset_x
            y1_mm = y1 + offset_y
            x2_mm = x2 + offset_x
            y2_mm = y2 + offset_y
            
            nd.moveto(x1_mm, y1_mm)  # Pen up, move to start
            nd.lineto(x2_mm, y2_mm)  # Pen down, draw line
            
            if (i + 1) % 50 == 0:
                print(f"  Progress: {i + 1}/{len(all_lines)} lines")
        
        nd.moveto(0, 0)  # Return to home
        print("Drawing complete!")
        
    finally:
        nd.disconnect()


# =============================================================================
# CLI Interface
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Sol LeWitt's Wall Drawing #11 - Python adaptation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python sol11.py animation          # Animated display
  python sol11.py single             # Single frame display
  python sol11.py svg output.svg     # Export to SVG
  python sol11.py plotter            # Draw with NextDraw
  python sol11.py plotter --dry-run  # Preview plotter commands
        """
    )
    
    parser.add_argument(
        "mode",
        choices=["animation", "single", "svg", "plotter"],
        help="Output mode"
    )
    
    parser.add_argument(
        "output",
        nargs="?",
        default="sol11_output.svg",
        help="Output filename (for svg mode)"
    )
    
    parser.add_argument(
        "--frame", "-f",
        type=int,
        default=0,
        help="Frame index for single/svg/plotter modes (default: 0)"
    )
    
    parser.add_argument(
        "--size", "-s",
        type=float,
        default=6.0,
        help="Drawing size in inches for svg/plotter modes (default: 6.0)"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="For plotter mode: show what would be drawn without plotting"
    )
    
    args = parser.parse_args()
    
    if args.mode == "animation":
        run_py5_display("animation")
    elif args.mode == "single":
        run_py5_display("single", frame_index=args.frame)
    elif args.mode == "svg":
        export_svg(args.output, size_inches=args.size, frame_index=args.frame)
    elif args.mode == "plotter":
        run_plotter(size_inches=args.size, frame_index=args.frame, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
