# utils.py
from pptx.util import Pt

def calculate_dynamic_font_size(text: str, is_chorus: bool = False) -> Pt:
    """
    Estimate font size based on text length to avoid overflow.
    """
    base_size = 28
    min_size = 18
    max_lines = 12 if is_chorus else 14
    max_chars_per_line = 50  # Empirical guess

    # Count actual visual lines based on wrap
    raw_lines = text.split('\n')
    estimated_lines = sum((len(line) // max_chars_per_line + 1) for line in raw_lines)

    scale = min(1.0, max_lines / max(estimated_lines, 1))
    size = int(base_size * scale)
    return Pt(max(size, min_size))

def estimate_wrapped_lines(text: str, box_width_inches: float, font_size_pt: float) -> int:
    """
    A very rough estimation of how many lines text will occupy.
    """
    # This factor is highly dependent on the font.
    # 0.55 is a rough guess for an average proportional font.
    char_width_factor = 0.55 
    
    # 1 point = 1/72 inch
    avg_char_width_inches = (font_size_pt / 72.0) * char_width_factor

    if avg_char_width_inches == 0:
        return 1

    chars_per_line = max(1, box_width_inches / avg_char_width_inches)
    lines = text.split('\n')

    estimated_lines = 0
    for line in lines:
        # +1 to account for the line itself, 
        # int(len(line) / chars_per_line) for wraps
        est_line_count = int(len(line) / chars_per_line) + 1
        estimated_lines += est_line_count

    return estimated_lines

# def _estimate_wrapped_lines(self, text: str, box_width_inches: float, font_size_pt: float) -> int:
#         """
#         bruh
#         """
#         char_width_factor = 0.55  # Empirical average character width factor
#         avg_char_width_inches = (font_size_pt / 72.0) * char_width_factor # in points, where 1pt = 1/72 inch

#         if avg_char_width_inches == 0:
#             return 1

#         chars_per_line = box_width_inches / avg_char_width_inches
#         lines = text.split('\n')

#         estimated_lines = 0
#         for line in lines:
#             est_line_count = max(1, int(len(line) / chars_per_line) + 1)
#             estimated_lines += est_line_count

#         return estimated_lines