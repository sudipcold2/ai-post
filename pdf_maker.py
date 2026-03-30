from PIL import Image, ImageDraw, ImageFont
import textwrap
import os

def create_slide(title_text, body_text, bg_color):
    """Generates a 1080x1080 image with centered/wrapped text."""
    width, height = 1080, 1080
    img = Image.new('RGB', (width, height), color=bg_color)
    draw = ImageDraw.Draw(img)
    
    # Try finding a native Mac font, fallback to default
    try:
        font_title = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 80)
        font_body = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 50)
    except:
        font_title = ImageFont.load_default()
        font_body = ImageFont.load_default()
        
    # Wrap text
    wrapped_title = textwrap.fill(title_text, width=22)
    wrapped_body = textwrap.fill(body_text, width=35)
    
    # Draw Title
    title_bbox = draw.multiline_textbbox((0,0), wrapped_title, font=font_title)
    title_w = title_bbox[2] - title_bbox[0]
    title_h = title_bbox[3] - title_bbox[1]
    title_x = (width - title_w) / 2
    title_y = (height / 2) - title_h - 50
    draw.multiline_text((title_x, title_y), wrapped_title, font=font_title, fill=(255, 255, 255), align="center")
    
    # Draw Body
    body_bbox = draw.multiline_textbbox((0,0), wrapped_body, font=font_body)
    body_w = body_bbox[2] - body_bbox[0]
    body_h = body_bbox[3] - body_bbox[1]
    body_x = (width - body_w) / 2
    body_y = (height / 2) + 50
    draw.multiline_text((body_x, body_y), wrapped_body, font=font_body, fill=(200, 200, 220), align="center")
    
    return img

def generate_carousel_pdf(western_headline, eastern_headline, base_output_path="carousel"):
    """Creates individual slide images and returns their paths."""
    slides = [
        {"title": "Today in AI", "body": "The Most Critical Updates You Missed", "color": (26, 30, 48)},
        {"title": "Western Breakthrough", "body": western_headline, "color": (15, 23, 42)},
        {"title": "Eastern Frontier", "body": eastern_headline, "color": (45, 20, 30)},
        {"title": "Stay Ahead", "body": "Follow for daily AI insights.", "color": (255, 42, 95)}
    ]
    
    paths = []
    for i, data in enumerate(slides):
        img = create_slide(data["title"], data["body"], data["color"])
        path = f"{base_output_path}_{i}.jpg"
        img.save(path, quality=95)
        paths.append(path)
        
    return paths
