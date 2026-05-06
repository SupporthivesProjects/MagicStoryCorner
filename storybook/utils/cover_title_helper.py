from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from django.core.files.base import File
import math
import random

FONT_CACHE = {}

def add_title_to_cover(cover_image, title, font_style='josephine-bold', text_effect='natural_colorful'):
    try:
        if isinstance(cover_image, File):
            cover_image.seek(0)
            img = Image.open(cover_image)
        else:
            img = Image.open(BytesIO(cover_image))
        
        img = img.convert('RGBA')
        img_width, img_height = img.size
        
        safe_margin_x = int(img_width * 0.10)
        safe_margin_y = int(img_height * 0.12)
        title_area_width = img_width - (2 * safe_margin_x)
        title_y_position = safe_margin_y
        font_size = int(img_height * 0.08)
        
        font = load_font(font_size, font_style)
        text_layer = Image.new('RGBA', img.size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(text_layer)
        lines = wrap_title_text(draw, title, font, title_area_width)
        
        render_text_effect(text_layer, lines, font, title_y_position, font_size, img_width, text_effect)
        
        final_img = Image.alpha_composite(img, text_layer)
        final_img = final_img.convert('RGB')
        
        output = BytesIO()
        final_img.save(output, format='PNG', quality=95)
        output.seek(0)
        
        return File(output, name="cover_with_title.png")
        
    except Exception as e:
        print(f"Error adding title to cover: {str(e)}")
        return cover_image

def load_font(font_size, style='josephine-bold'):
    cache_key = f"{style}_{font_size}"
    if cache_key in FONT_CACHE:
        return FONT_CACHE[cache_key]
    
    font_paths = {
        'josephine': ['static/font/JosephineCosy-Regular.ttf'],
        'josephine-bold': [
            'static/font/JosephineCosyBold.ttf',
            'static/font/JosephineCosyBold.otf',
        ]
    }
    
    if style in font_paths:
        for font_path in font_paths[style]:
            try:
                font = ImageFont.truetype(font_path, font_size)
                FONT_CACHE[cache_key] = font
                return font
            except Exception:
                continue
    
    default_fonts = [
        'static/font/JosephineCosyBold.ttf',
        'static/font/JosephineCosyBold.otf',
        'static/font/JosephineCosy-Regular.ttf',
    ]
    
    for font_path in default_fonts:
        try:
            font = ImageFont.truetype(font_path, font_size)
            FONT_CACHE[cache_key] = font
            return font
        except Exception:
            continue
    
    font = ImageFont.load_default()
    FONT_CACHE[cache_key] = font
    return font

def wrap_title_text(draw, text, font, max_width):
    words = text.split()
    lines = []
    current_line = []
    
    for word in words:
        test_line = ' '.join(current_line + [word])
        bbox = draw.textbbox((0, 0), test_line, font=font)
        text_width = bbox[2] - bbox[0]
        
        if text_width <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(' '.join(current_line))
                current_line = [word]
            else:
                lines.append(word)
                current_line = []
    
    if current_line:
        lines.append(' '.join(current_line))
    
    return lines

def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def render_text_effect(text_layer, lines, font, start_y, font_size, img_width, effect='natural_colorful'):
    effects = {
        'natural_colorful': render_natural_colorful,
        'natural_rainbow': render_natural_rainbow,
        'natural_gradient': render_natural_gradient,
        'natural_shadow': render_natural_shadow,
        'natural_neon': render_natural_neon,
        'natural_cartoon': render_natural_cartoon,
        'painted': render_painted_style,
        'storybook': render_storybook_style,
        'colorful': render_colorful,
        'rainbow': render_rainbow,
        'gradient': render_gradient,
        'shadow': render_shadow,
        'neon': render_neon,
        'cartoon': render_cartoon,
    }
    
    render_func = effects.get(effect, render_natural_colorful)
    render_func(text_layer, lines, font, start_y, font_size, img_width)

def add_texture_to_text(text_layer, x, y, width, height, intensity=0.15):
    texture = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    pixels = texture.load()
    
    for i in range(width):
        for j in range(height):
            if random.random() < intensity:
                alpha = random.randint(5, 25)
                variation = random.randint(-10, 10)
                pixels[i, j] = (variation, variation, variation, alpha)
    
    text_layer.paste(texture, (x, y), texture)

def draw_natural_outlined_text(draw, text, x, y, font, color, outline_color, outline_width, add_texture=True):
    variation = 0.5
    
    for adj_x in range(-outline_width-2, outline_width + 3):
        for adj_y in range(-outline_width-2, outline_width + 3):
            distance = math.sqrt(adj_x**2 + adj_y**2)
            if distance <= outline_width + 2:
                rand_x = adj_x + random.uniform(-variation, variation)
                rand_y = adj_y + random.uniform(-variation, variation)
                
                alpha = int(200 * (1 - distance / (outline_width + 2)))
                if isinstance(outline_color, tuple):
                    outline_with_alpha = outline_color[:3] + (alpha,)
                else:
                    r, g, b = hex_to_rgb(outline_color)
                    outline_with_alpha = (r, g, b, alpha)
                draw.text((x + rand_x, y + rand_y), text, font=font, fill=outline_with_alpha)
    
    if isinstance(color, str):
        color = hex_to_rgb(color) + (255,)
    draw.text((x, y), text, font=font, fill=color)

def draw_outlined_text(draw, text, x, y, font, color, outline_color, outline_width):
    for adj_x in range(-outline_width, outline_width + 1):
        for adj_y in range(-outline_width, outline_width + 1):
            distance = math.sqrt(adj_x**2 + adj_y**2)
            if distance <= outline_width:
                alpha = int(255 * (1 - distance / outline_width))
                if isinstance(outline_color, tuple):
                    outline_with_alpha = outline_color[:3] + (alpha,)
                else:
                    r, g, b = hex_to_rgb(outline_color)
                    outline_with_alpha = (r, g, b, alpha)
                draw.text((x + adj_x, y + adj_y), text, font=font, fill=outline_with_alpha)
    
    if isinstance(color, str):
        color = hex_to_rgb(color) + (255,)
    draw.text((x, y), text, font=font, fill=color)

def render_natural_colorful(text_layer, lines, font, start_y, font_size, img_width):
    draw = ImageDraw.Draw(text_layer)
    line_height = int(font_size * 1.3)
    current_y = start_y
    
    colors = ['#FF1744', '#F50057', '#FFD600', '#00E676', '#00B0FF', '#FF6B6B', '#4ECDC4', '#FFE66D']
    
    for line_idx, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        text_x = (img_width - text_width) // 2 + random.randint(-2, 2)
        
        color = colors[line_idx % len(colors)]
        
        for glow in range(12, 0, -2):
            alpha = int(40 * (1 - glow / 12))
            glow_color = (0, 0, 0, alpha)
            for adj_x in range(-glow, glow + 1, 2):
                for adj_y in range(-glow, glow + 1, 2):
                    distance = math.sqrt(adj_x**2 + adj_y**2)
                    if distance <= glow:
                        draw.text((text_x + adj_x, current_y + adj_y), line, font=font, fill=glow_color)
        
        draw_natural_outlined_text(draw, line, text_x, current_y, font, color, 'white', 6)
        add_texture_to_text(text_layer, text_x-5, current_y-5, text_width+10, text_height+10, intensity=0.12)
        
        current_y += line_height

def render_painted_style(text_layer, lines, font, start_y, font_size, img_width):
    draw = ImageDraw.Draw(text_layer)
    line_height = int(font_size * 1.3)
    current_y = start_y
    
    colors = ['#E74C3C', '#F39C12', '#F1C40F', '#2ECC71', '#3498DB', '#9B59B6']
    
    for line_idx, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        text_x = (img_width - text_width) // 2 + random.randint(-3, 3)
        
        color = colors[line_idx % len(colors)]
        color_rgb = hex_to_rgb(color)
        
        for layer in range(3):
            offset = layer * 0.5
            layer_alpha = 180 - (layer * 40)
            layer_color = color_rgb + (layer_alpha,)
            draw.text((text_x + offset, current_y + offset), line, font=font, fill=layer_color)
        
        for width in [8, 6, 4]:
            alpha = int(150 * (1 - width / 10))
            draw_natural_outlined_text(draw, line, text_x, current_y, font, color, (0, 0, 0, alpha), width, False)
        
        draw.text((text_x, current_y), line, font=font, fill=color_rgb + (255,))
        add_texture_to_text(text_layer, text_x-10, current_y-10, text_width+20, text_height+20, intensity=0.25)
        
        current_y += line_height

def render_storybook_style(text_layer, lines, font, start_y, font_size, img_width):
    draw = ImageDraw.Draw(text_layer)
    line_height = int(font_size * 1.3)
    current_y = start_y
    
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        text_x = (img_width - text_width) // 2
        
        shadow_offset = 4
        for i in range(shadow_offset, 0, -1):
            alpha = int(120 * (1 - i / shadow_offset))
            draw.text((text_x + i, current_y + i), line, font=font, fill=(0, 0, 0, alpha))
        
        draw_natural_outlined_text(draw, line, text_x, current_y, font, '#FFF8E7', '#8B4513', 7)
        draw.text((text_x, current_y), line, font=font, fill=(139, 69, 19, 255))
        add_texture_to_text(text_layer, text_x-5, current_y-5, text_width+10, text_height+10, intensity=0.1)
        
        current_y += line_height

def render_natural_rainbow(text_layer, lines, font, start_y, font_size, img_width):
    draw = ImageDraw.Draw(text_layer)
    line_height = int(font_size * 1.3)
    current_y = start_y
    
    rainbow = ['#FF0000', '#FF7F00', '#FFFF00', '#00FF00', '#0000FF', '#4B0082', '#9400D3']
    
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        text_width = bbox[2] - bbox[0]
        start_x = (img_width - text_width) // 2 + random.randint(-2, 2)
        
        words = line.split()
        current_x = start_x
        
        for word_idx, word in enumerate(words):
            color = rainbow[word_idx % len(rainbow)]
            
            for glow in range(8, 0, -2):
                alpha = int(50 * (1 - glow / 8))
                glow_color = hex_to_rgb(color) + (alpha,)
                for adj_x in range(-glow, glow + 1, 2):
                    for adj_y in range(-glow, glow + 1, 2):
                        draw.text((current_x + adj_x, current_y + adj_y), word, font=font, fill=glow_color)
            
            draw_natural_outlined_text(draw, word, current_x, current_y, font, color, 'white', 6)
            
            word_bbox = draw.textbbox((current_x, current_y), word, font=font)
            word_width = word_bbox[2] - word_bbox[0]
            word_height = word_bbox[3] - word_bbox[1]
            add_texture_to_text(text_layer, current_x-5, current_y-5, word_width+10, word_height+10, intensity=0.12)
            
            current_x += word_width
            
            if word_idx < len(words) - 1:
                space_bbox = draw.textbbox((0, 0), ' ', font=font)
                space_width = space_bbox[2] - space_bbox[0]
                current_x += space_width
        
        current_y += line_height

def render_natural_gradient(text_layer, lines, font, start_y, font_size, img_width):
    draw = ImageDraw.Draw(text_layer)
    line_height = int(font_size * 1.3)
    current_y = start_y
    
    gradients = [('#FF6B6B', '#FFE66D'), ('#4ECDC4', '#44A08D'), ('#F857A6', '#FF5858'), ('#00C9FF', '#92FE9D')]
    
    for line_idx, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        text_x = (img_width - text_width) // 2 + random.randint(-2, 2)
        
        start_color, end_color = gradients[line_idx % len(gradients)]
        start_rgb = hex_to_rgb(start_color)
        end_rgb = hex_to_rgb(end_color)
        mid_color = tuple(int((start_rgb[i] + end_rgb[i]) / 2) for i in range(3))
        
        for offset in range(5, 0, -1):
            alpha = int(100 * (1 - offset / 5))
            draw.text((text_x + offset, current_y + offset), line, font=font, fill=(0, 0, 0, alpha))
        
        draw_natural_outlined_text(draw, line, text_x, current_y, font, mid_color + (255,), 'white', 6)
        add_texture_to_text(text_layer, text_x-5, current_y-5, text_width+10, text_height+10, intensity=0.15)
        
        current_y += line_height

def render_natural_shadow(text_layer, lines, font, start_y, font_size, img_width):
    draw = ImageDraw.Draw(text_layer)
    line_height = int(font_size * 1.3)
    current_y = start_y
    
    colors = ['#FFD700', '#FF69B4', '#00CED1', '#FF6347', '#9370DB', '#32CD32', '#FF8C00']
    
    for line_idx, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        text_x = (img_width - text_width) // 2 + random.randint(-2, 2)
        
        shadow_offset = max(6, int(font_size * 0.1))
        for i in range(shadow_offset, 0, -1):
            alpha = int(150 * (1 - i / shadow_offset))
            rand_offset = random.uniform(0, 0.5)
            draw.text((text_x + i + rand_offset, current_y + i + rand_offset), line, font=font, fill=(0, 0, 0, alpha))
        
        draw_natural_outlined_text(draw, line, text_x, current_y, font, (255, 255, 255, 255), 'black', 6)
        
        color = colors[line_idx % len(colors)]
        color_rgb = hex_to_rgb(color) + (255,)
        draw.text((text_x, current_y), line, font=font, fill=color_rgb)
        
        add_texture_to_text(text_layer, text_x-5, current_y-5, text_width+10, text_height+10, intensity=0.12)
        
        current_y += line_height

def render_natural_neon(text_layer, lines, font, start_y, font_size, img_width):
    draw = ImageDraw.Draw(text_layer)
    line_height = int(font_size * 1.3)
    current_y = start_y
    
    neon = ['#FF00FF', '#00FFFF', '#FFFF00', '#FF1493', '#00FF00', '#FF4500']
    
    for line_idx, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        text_x = (img_width - text_width) // 2 + random.randint(-1, 1)
        
        color = neon[line_idx % len(neon)]
        color_rgb = hex_to_rgb(color)
        
        for glow in range(18, 0, -2):
            alpha = int(80 * (1 - glow / 18))
            glow_color = color_rgb + (alpha,)
            for adj_x in range(-glow, glow + 1, 2):
                for adj_y in range(-glow, glow + 1, 2):
                    distance = math.sqrt(adj_x**2 + adj_y**2)
                    if distance <= glow:
                        rand_x = adj_x + random.uniform(-0.5, 0.5)
                        rand_y = adj_y + random.uniform(-0.5, 0.5)
                        draw.text((text_x + rand_x, current_y + rand_y), line, font=font, fill=glow_color)
        
        draw_natural_outlined_text(draw, line, text_x, current_y, font, color, (0, 0, 0, 255), 3)
        add_texture_to_text(text_layer, text_x-10, current_y-10, text_width+20, text_height+20, intensity=0.08)
        
        current_y += line_height

def render_natural_cartoon(text_layer, lines, font, start_y, font_size, img_width):
    draw = ImageDraw.Draw(text_layer)
    line_height = int(font_size * 1.3)
    current_y = start_y
    
    colors = ['#FF6B6B', '#4ECDC4', '#FFE66D', '#95E1D3', '#F38181']
    
    for line_idx, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        text_x = (img_width - text_width) // 2 + random.randint(-3, 3)
        
        for width in [10, 8, 6]:
            draw_natural_outlined_text(draw, line, text_x, current_y, font, (0, 0, 0, 255), (0, 0, 0, 255), width, False)
        
        for width in [5, 3]:
            draw_natural_outlined_text(draw, line, text_x, current_y, font, (255, 255, 255, 255), (255, 255, 255, 255), width, False)
        
        color = colors[line_idx % len(colors)]
        color_rgb = hex_to_rgb(color) + (255,)
        draw.text((text_x, current_y), line, font=font, fill=color_rgb)
        
        add_texture_to_text(text_layer, text_x-10, current_y-10, text_width+20, text_height+20, intensity=0.2)
        
        current_y += line_height

def render_colorful(text_layer, lines, font, start_y, font_size, img_width):
    draw = ImageDraw.Draw(text_layer)
    line_height = int(font_size * 1.3)
    current_y = start_y
    
    colors = ['#FF1744', '#F50057', '#FFD600', '#00E676', '#00B0FF', '#FF6B6B', '#4ECDC4', '#FFE66D']
    
    for line_idx, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        text_width = bbox[2] - bbox[0]
        text_x = (img_width - text_width) // 2
        
        color = colors[line_idx % len(colors)]
        draw_outlined_text(draw, line, text_x, current_y, font, color, 'white', 8)
        
        current_y += line_height

def render_rainbow(text_layer, lines, font, start_y, font_size, img_width):
    draw = ImageDraw.Draw(text_layer)
    line_height = int(font_size * 1.3)
    current_y = start_y
    
    rainbow = ['#FF0000', '#FF7F00', '#FFFF00', '#00FF00', '#0000FF', '#4B0082', '#9400D3']
    
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        text_width = bbox[2] - bbox[0]
        start_x = (img_width - text_width) // 2
        
        words = line.split()
        current_x = start_x
        
        for word_idx, word in enumerate(words):
            color = rainbow[word_idx % len(rainbow)]
            draw_outlined_text(draw, word, current_x, current_y, font, color, 'white', 8)
            
            word_bbox = draw.textbbox((current_x, current_y), word, font=font)
            word_width = word_bbox[2] - word_bbox[0]
            current_x += word_width
            
            if word_idx < len(words) - 1:
                space_bbox = draw.textbbox((0, 0), ' ', font=font)
                space_width = space_bbox[2] - space_bbox[0]
                current_x += space_width
        
        current_y += line_height

def render_gradient(text_layer, lines, font, start_y, font_size, img_width):
    draw = ImageDraw.Draw(text_layer)
    line_height = int(font_size * 1.3)
    current_y = start_y
    
    gradients = [('#FF6B6B', '#FFE66D'), ('#4ECDC4', '#44A08D'), ('#F857A6', '#FF5858'), ('#00C9FF', '#92FE9D')]
    
    for line_idx, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        text_width = bbox[2] - bbox[0]
        text_x = (img_width - text_width) // 2
        
        start_color, end_color = gradients[line_idx % len(gradients)]
        start_rgb = hex_to_rgb(start_color)
        end_rgb = hex_to_rgb(end_color)
        mid_color = tuple(int((start_rgb[i] + end_rgb[i]) / 2) for i in range(3))
        
        draw_outlined_text(draw, line, text_x, current_y, font, mid_color + (255,), 'white', 8)
        
        current_y += line_height

def render_shadow(text_layer, lines, font, start_y, font_size, img_width):
    draw = ImageDraw.Draw(text_layer)
    line_height = int(font_size * 1.3)
    current_y = start_y
    
    colors = ['#FFD700', '#FF69B4', '#00CED1', '#FF6347', '#9370DB', '#32CD32', '#FF8C00']
    
    for line_idx, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        text_width = bbox[2] - bbox[0]
        text_x = (img_width - text_width) // 2
        
        shadow_offset = max(5, int(font_size * 0.08))
        for i in range(shadow_offset, 0, -1):
            alpha = int(180 * (1 - i / shadow_offset))
            draw.text((text_x + i, current_y + i), line, font=font, fill=(0, 0, 0, alpha))
        
        draw_outlined_text(draw, line, text_x, current_y, font, (255, 255, 255, 255), 'black', 8)
        
        color = colors[line_idx % len(colors)]
        color_rgb = hex_to_rgb(color) + (255,)
        draw.text((text_x, current_y), line, font=font, fill=color_rgb)
        
        current_y += line_height

def render_neon(text_layer, lines, font, start_y, font_size, img_width):
    draw = ImageDraw.Draw(text_layer)
    line_height = int(font_size * 1.3)
    current_y = start_y
    
    neon = ['#FF00FF', '#00FFFF', '#FFFF00', '#FF1493', '#00FF00', '#FF4500']
    
    for line_idx, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        text_width = bbox[2] - bbox[0]
        text_x = (img_width - text_width) // 2
        
        color = neon[line_idx % len(neon)]
        color_rgb = hex_to_rgb(color)
        
        for glow in range(15, 0, -1):
            alpha = int(100 * (1 - glow / 15))
            glow_color = color_rgb + (alpha,)
            for adj_x in range(-glow, glow + 1):
                for adj_y in range(-glow, glow + 1):
                    distance = math.sqrt(adj_x**2 + adj_y**2)
                    if distance <= glow:
                        draw.text((text_x + adj_x, current_y + adj_y), line, font=font, fill=glow_color)
        
        draw_outlined_text(draw, line, text_x, current_y, font, color, (0, 0, 0, 255), 3)
        
        current_y += line_height

def render_cartoon(text_layer, lines, font, start_y, font_size, img_width):
    draw = ImageDraw.Draw(text_layer)
    line_height = int(font_size * 1.3)
    current_y = start_y
    
    colors = ['#FF6B6B', '#4ECDC4', '#FFE66D', '#95E1D3', '#F38181']
    
    for line_idx, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        text_width = bbox[2] - bbox[0]
        text_x = (img_width - text_width) // 2
        
        for width in [12, 10, 8]:
            draw_outlined_text(draw, line, text_x, current_y, font, (0, 0, 0, 255), (0, 0, 0, 255), width)