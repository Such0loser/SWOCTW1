import cairosvg
import os

def convert_svg_to_png(svg_content: str, output_filepath: str, width: int = None, height: int = None):
    """
    Converts an SVG string to a PNG image with specified dimensions.

    Args:
        svg_content (str): The SVG content as a string.
        output_filepath (str): The full path for the output PNG file (e.g., "output/my_image.png").
        width (int, optional): The desired width of the output PNG in pixels.
                                If None, scales based on SVG's viewBox or natural size.
        height (int, optional): The desired height of the output PNG in pixels.
                                If None, scales based on SVG's viewBox or natural size.
    """
    try:
        # Create output directory if it doesn't exist
        output_dir = os.path.dirname(output_filepath)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)

        cairosvg.svg2png(bytestring=svg_content.encode('utf-8'), write_to=output_filepath, parent_width=width, parent_height=height)
        print(f"Successfully converted SVG to PNG: {output_filepath}")
    except Exception as e:
        print(f"Error converting SVG: {e}")

# --- Example Usage ---

# 1. Example SVG content (a simple blue circle)
# In a real scenario, you'd likely read this from an .svg file
example_svg_content = """
<svg width="200" height="200" viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
  <circle cx="100" cy="100" r="80" fill="blue" stroke="black" stroke-width="3"/>
  <text x="100" y="105" font-family="Arial" font-size="20" fill="white" text-anchor="middle">Hello!</text>
</svg>
"""

# Define output path
output_directory = "converted_images"
output_filename = "my_circle.png"
output_full_path = os.path.join(output_directory, output_filename)

# Convert to PNG with default SVG dimensions (200x200 in this case)
print("Converting with default dimensions (based on SVG's width/height/viewBox)...")
convert_svg_to_png(example_svg_content, output_full_path)

# Convert to PNG with a specific width (e.g., 400 pixels wide, height will scale proportionally)
output_filename_scaled = "my_circle_400px.png"
output_full_path_scaled = os.path.join(output_directory, output_filename_scaled)
print("\nConverting to 400px width...")
convert_svg_to_png(example_svg_content, output_full_path_scaled, width=400)

# You can also read SVG content from a file
def convert_svg_file_to_png(input_filepath: str, output_filepath: str, width: int = None, height: int = None):
    """
    Reads an SVG file and converts it to a PNG image.
    """
    try:
        with open(input_filepath, 'r', encoding='utf-8') as f:
            svg_content = f.read()
        convert_svg_to_png(svg_content, output_filepath, width, height)
    except FileNotFoundError:
        print(f"Error: Input SVG file not found at {input_filepath}")
    except Exception as e:
        print(f"Error reading or converting file: {e}")

# Example of converting from a file (first, let's create a dummy SVG file)
dummy_svg_filename = "dummy_logo.svg"
dummy_svg_filepath = os.path.join(output_directory, dummy_svg_filename) # Put it in the same output dir for simplicity

if not os.path.exists(output_directory):
    os.makedirs(output_directory)

with open(dummy_svg_filepath, 'w', encoding='utf-8') as f:
    f.write("""
<svg width="150" height="150" viewBox="0 0 150 150" xmlns="http://www.w3.org/2000/svg">
  <rect x="25" y="25" width="100" height="100" fill="green"/>
  <text x="75" y="85" font-family="Verdana" font-size="25" fill="yellow" text-anchor="middle">WEB</text>
</svg>
""")
print(f"\nCreated a dummy SVG file: {dummy_svg_filepath}")

output_filename_from_file = "logo_from_file.png"
output_full_path_from_file = os.path.join(output_directory, output_filename_from_file)
print("\nConverting SVG from file to PNG...")
convert_svg_file_to_png(dummy_svg_filepath, output_full_path_from_file, width=300)