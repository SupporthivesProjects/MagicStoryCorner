import os
import io
import math
import random
from typing import Dict, Any, Tuple, Optional
from time import sleep
from PIL import Image, ImageFilter, ImageEnhance, ImageDraw, ImageFont
from django.core.files.base import File
import google.generativeai as genai
from products.models import ProductBook
from stories.models import AIModel, ImageStyle
from logs.models import Log

FONT_CACHE = {}


class PILCoverGenerator:
    
    def __init__(self):
        pass
        
    def retry_cover(self, book_id: int) -> Dict[str, Any]:
        try:
            book = ProductBook.objects.get(pk=book_id)
            
            image_model = AIModel.objects.filter(type="image", is_active=True).first()
            if not image_model:
                Log.objects.create(
                    title="Cover Retry Error",
                    type="error",
                    message=f"Book {book_id} - No active image model configured"
                )
                return {
                    "success": False,
                    "message": "No image model configured",
                    "book_id": book_id
                }
            
            gemini_key = image_model.apikey
            gemini_name = image_model.name or 'gemini-2.5-flash-image'
            
            imagestyle = self._get_content(ImageStyle, book.imagestyle_id)

            story_content = ""
            try:
                pages = book.pages.filter(page__lte=2).order_by('page')
                story_texts = []
                for page in pages:
                    if page.text:
                        story_texts.append(page.text.strip())
                if story_texts:
                    story_content = " ".join(story_texts)
            except Exception as e:
                Log.objects.create(
                    title="Story Context Warning",
                    type="warning",
                    message=f"Book {book_id} - Could not load story pages: {str(e)}"
                )
                
            
            character_refs = self._load_character_references(book.pk)

            if not character_refs:
                character_refs = self._load_page_images_as_references(book)

            if not character_refs:
                Log.objects.create(
                    title="Cover Retry Error",
                    type="error",
                    message=f"Book {book_id} - No character references or page images found"
                )
                return {
                    "success": False,
                    "message": "No character references or page images found. Cannot regenerate cover.",
                    "book_id": book_id
                }
            
            sleep(1)
            
            original_cover, cropped_cover = self._regenerate_cover_with_retry(
                title=book.title,
                character_desc=book.char_desc,
                story_content=story_content,
                imagestyle=imagestyle,
                character_refs=character_refs,
                gemini_key=gemini_key,
                gemini_name=gemini_name
            )
            
            if original_cover and cropped_cover:
                original_cover.seek(0)
                book.char_img.save("original_cover.png", original_cover, save=True)
                
                cropped_cover.seek(0)
                book.image.save("cropped_cover.png", cropped_cover, save=True)


                book.refresh_from_db()
                book.thumbnail = None
                book._generate_thumbnail()
                ProductBook.objects.filter(pk=book.pk).update(thumbnail=book.thumbnail)
                
                return {
                    "success": True,
                    "message": "Cover regenerated and replaced successfully",
                    "book_id": book_id,
                    "title": book.title
                }
            else:
                Log.objects.create(
                    title="Cover Retry Failed",
                    type="error",
                    message=f"Book {book_id} - All retry attempts failed to generate cover"
                )
                return {
                    "success": False,
                    "message": "Cover regeneration failed after all retry attempts",
                    "book_id": book_id
                }
                
        except ProductBook.DoesNotExist:
            Log.objects.create(
                title="Cover Retry Error",
                type="error",
                message=f"Book {book_id} does not exist"
            )
            return {
                "success": False,
                "message": f"Book with id {book_id} not found",
                "book_id": book_id
            }
        except Exception as e:
            Log.objects.create(
                title="Cover Retry Error",
                type="error",
                message=f"Book {book_id} - Unexpected error: {str(e)}"
            )
            return {
                "success": False,
                "message": f"Error: {str(e)}",
                "book_id": book_id
            }
    
    def _get_content(self, model_class, obj_id):
        if not obj_id:
            return ""
        obj = model_class.objects.filter(pk=obj_id).first()
        return obj.content if obj else ""
    
    def _load_character_references(self, book_pk: int) -> Dict[str, Dict]:
        character_ref_dir = f'media/products/books/{book_pk}/images'
        character_refs = {}
        
        if not os.path.exists(character_ref_dir):
            return character_refs
        
        try:
            files = os.listdir(character_ref_dir)
            
            main_ref = 'main_reference.png'
            sub_refs = [f for f in files if f.startswith('sub_') and f.endswith('_reference.png')]
            sub_refs.sort()
            
            ref_files = []
            if main_ref in files:
                ref_files.append(main_ref)
            ref_files.extend(sub_refs)
            
            for filename in ref_files:
                if filename == 'main_reference.png':
                    char_key = 'main'
                else:
                    char_key = filename.replace('_reference.png', '')
                
                ref_path = os.path.join(character_ref_dir, filename)
                
                try:
                    with open(ref_path, 'rb') as f:
                        image_data = f.read()
                        if image_data and len(image_data) > 0:
                            character_refs[char_key] = {
                                'image': image_data,
                                'is_main': filename == 'main_reference.png'
                            }
                except Exception as e:
                    Log.objects.create(
                        title="Load Reference Warning",
                        type="warning",
                        message=f"Failed to load {char_key} reference: {str(e)}"
                    )
        except Exception as e:
            Log.objects.create(
                title="Load References Warning",
                type="warning",
                message=f"Failed to scan reference directory: {str(e)}"
            )
        
        return character_refs
    

    def _load_page_images_as_references(self, book) -> Dict[str, Dict]:
        page_refs = {}
        
        try:
            pages = book.pages.filter(page__lte=2).order_by('page')
            
            for idx, page in enumerate(pages):
                if page.image:
                    try:
                        page.image.seek(0)
                        image_data = page.image.read()
                        
                        if image_data and len(image_data) > 0:
                            char_key = f'page_{page.page}'
                            page_refs[char_key] = {
                                'image': image_data,
                                'is_main': idx == 0
                            }
                    except Exception as e:
                        Log.objects.create(
                            title="Load Page Image Warning",
                            type="warning",
                            message=f"Failed to load page {page.page} image: {str(e)}"
                        )
        except Exception as e:
            Log.objects.create(
                title="Load Page Images Warning",
                type="warning",
                message=f"Failed to load page images: {str(e)}"
            )
        
        return page_refs

    def _regenerate_cover_with_retry(self, 
                                 title: str, 
                                 character_desc: str, 
                                 story_content: str,
                                 imagestyle: str, 
                                 character_refs: Dict,
                                 gemini_key: str,
                                 gemini_name: str) -> Tuple[Optional[File], Optional[File]]:
    
        try:
            genai.configure(api_key=gemini_key)
            
            title_display = ' '.join(title.strip().split())
            
            reference_images = []
            char_keys_order = []
            
            if 'main' in character_refs and character_refs['main'].get('image'):
                reference_images.append(character_refs['main']['image'])
                char_keys_order.append('main')
            
            for char_key in sorted([k for k in character_refs.keys() if k != 'main']):
                if character_refs[char_key].get('image'):
                    reference_images.append(character_refs[char_key]['image'])
                    char_keys_order.append(char_key)
            
            if not reference_images:
                Log.objects.create(
                    title="Cover Retry Error",
                    type="error",
                    message="No reference images available"
                )
                return None, None
            
            sleep(1)
            
            model = genai.GenerativeModel(gemini_name)
            pil_images = [Image.open(io.BytesIO(img_data)) for img_data in reference_images]
            
            has_main = 'main' in char_keys_order
            ref_instructions = "\n".join([
                f"- Reference Image {i+1} ({'MAIN CHARACTER' if i == 0 and has_main else 'Supporting Character'}) = Use EXACTLY as shown" 
                for i in range(len(reference_images))
            ])

            story_context = ""
            if story_content:
                story_context = f"\n\nSTORY CONTEXT:\n{story_content}\n\nUse this story context to create appropriate background scene and atmosphere.\n"

            prompt = (
                f"REFERENCE IMAGES: {len(reference_images)} character(s)\n"
                f"{ref_instructions}\n"
                f"Match EXACTLY: hair color/style/length, facial features, clothing colors/patterns, body proportions, accessories. DO NOT modify any feature.{story_context}\n"
            )
            
            if has_main:
                prompt += f"CHARACTER HIERARCHY: Image 1 is MAIN CHARACTER (largest, most prominent, centered). Others are supporting characters (smaller, flanking main). All characters must appear together.\n\n"
            else:
                prompt += f"All {len(reference_images)} characters together with equal prominence.\n\n"

            prompt += (
                f"CRITICAL BOOK COVER LAYOUT - STRICT SPATIAL ZONES:\n"
                f"TOP 40% OF IMAGE: COMPLETELY EMPTY - only simple sky, clouds, or distant horizon. Absolutely NO characters, NO objects, NO foreground elements. This is reserved for title text overlay.\n\n"
                f"BOTTOM 60% OF IMAGE: Position ALL characters here. Characters stand on ground in lower portion. Use LOW camera angle looking UP from ground level. Characters' heads must NOT reach into top 40%.\n\n"
            )
            
            if has_main:
                prompt += f"Main character: center position, largest size, most prominent. Supporting characters: positioned around main character, all staying in bottom 60%.\n\n"
            
            prompt += (
                f"VISUAL REQUIREMENTS:\n"
                f"- Art style: {imagestyle}\n"
                f"- Vibrant professional children's book cover\n"
                f"- Full bleed to all edges\n"
                f"- Ground/environment visible at bottom\n"
                f"- 10-15% side margins\n"
                f"- Camera: ground-level perspective shooting upward\n"
                f"- Composition: professional book cover with clear empty title space at top\n\n"
                f"ABSOLUTE REQUIREMENTS:\n"
                f"- NO text, letters, or words anywhere\n"
                f"- NO characters above the 40% line from top\n"
                f"- NO tall objects extending into title space\n"
                f"- Top 40% must remain visually simple and uncluttered\n"
                f"- All characters grounded in bottom 60%, not floating\n"
                f"- Frame composition so characters fit comfortably in lower zone\n"
            )

            content = pil_images + [prompt]
            response = model.generate_content(content)
            
            if not response or not response.parts:
                Log.objects.create(
                    title="Cover Generation Error",
                    type="error",
                    message="Empty response from API"
                )
                return None, None
            
            image_part = None
            for part in response.parts:
                if hasattr(part, 'inline_data') and part.inline_data:
                    image_part = part
                    break
            
            if not image_part:
                Log.objects.create(
                    title="Cover Generation Error",
                    type="error",
                    message="No image in API response"
                )
                return None, None
            
            data = image_part.inline_data.data
            original_cover = File(io.BytesIO(data), name="cover_original.png")
            original_cover.seek(0)
            cover_content = original_cover.read()
            
            cover_with_text = self._add_stylish_title_overlay(
                File(io.BytesIO(cover_content), name="cover_original.png"),
                title_display
            )
            
            if not cover_with_text:
                Log.objects.create(
                    title="Text Overlay Error",
                    type="error",
                    message="Failed to add text overlay"
                )
                return None, None
            
            cropped_cover = self._resize_cover_image(cover_with_text)
            
            if cropped_cover:
                return cover_with_text, cropped_cover
            
            Log.objects.create(
                title="Cover Resize Error",
                type="error",
                message="Failed to resize cover image"
            )
            return None, None
            
        except Exception as e:
            Log.objects.create(
                title="Cover Generation Error",
                type="error",
                message=f"Error: {str(e)}"
            )
            return None, None
    
    def _load_font(self, font_size, style='josephine-bold'):
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
    
    def _hex_to_rgb(self, hex_color):
        color_map = {
            'white': (255, 255, 255),
            'black': (0, 0, 0),
            'red': (255, 0, 0),
            'green': (0, 255, 0),
            'blue': (0, 0, 255),
            'yellow': (255, 255, 0),
            'cyan': (0, 255, 255),
            'magenta': (255, 0, 255),
        }
        
        if isinstance(hex_color, str):
            hex_color_lower = hex_color.lower()
            if hex_color_lower in color_map:
                return color_map[hex_color_lower]
            hex_color = hex_color.lstrip('#')
        
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def _add_texture_to_text(self, text_layer, x, y, width, height, intensity=0.15):
        texture = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        pixels = texture.load()
        
        for i in range(width):
            for j in range(height):
                if random.random() < intensity:
                    alpha = random.randint(5, 25)
                    variation = random.randint(-10, 10)
                    pixels[i, j] = (variation, variation, variation, alpha)
        
        text_layer.paste(texture, (x, y), texture)
    
    def _draw_natural_outlined_text(self, draw, text, x, y, font, color, outline_color, outline_width, add_texture=True):
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
                        r, g, b = self._hex_to_rgb(outline_color)
                        outline_with_alpha = (r, g, b, alpha)
                    draw.text((x + rand_x, y + rand_y), text, font=font, fill=outline_with_alpha)
        
        if isinstance(color, str):
            color = self._hex_to_rgb(color) + (255,)
        draw.text((x, y), text, font=font, fill=color)
    
    def _add_stylish_title_overlay(self, image_file: File, title: str) -> Optional[File]:
        try:
            image_file.seek(0)
            img = Image.open(image_file)
            
            if img.mode not in ('RGB', 'RGBA'):
                img = img.convert('RGB')
            
            img = img.convert('RGBA')
            img_width, img_height = img.size
            
            safe_margin_x = int(img_width * 0.12)
            safe_margin_y = int(img_height * 0.04)
            title_area_width = min(img_width - (2 * safe_margin_x), int(img_width * 0.75))
            title_y_position = safe_margin_y
            font_size = int(img_height * 0.07)
            
            font = self._load_font(font_size, 'josephine-bold')
            text_layer = Image.new('RGBA', img.size, (255, 255, 255, 0))
            draw = ImageDraw.Draw(text_layer)
            
            words = title.split()
            lines = []
            current_line = []
            
            for word in words:
                test_line = ' '.join(current_line + [word])
                bbox = draw.textbbox((0, 0), test_line, font=font)
                text_width = bbox[2] - bbox[0]
                
                if text_width <= title_area_width:
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
            
            styles = [
                'vibrant_glow',
                'rainbow_pop',
                'neon_burst',
                'cartoon_bold',
                'painted_texture',
                'gradient_shine',
                'shadow_3d',
                'sparkle_magic',
                'word_color_pop',
                'modern_gradient',
                'playful_bounce',
                'glossy_3d'
            ]
            
            selected_style = random.choice(styles)
            
            if selected_style == 'vibrant_glow':
                self._render_vibrant_glow(draw, text_layer, lines, font, font_size, img_width, title_y_position)
            elif selected_style == 'rainbow_pop':
                self._render_rainbow_pop(draw, text_layer, lines, font, font_size, img_width, title_y_position)
            elif selected_style == 'neon_burst':
                self._render_neon_burst(draw, text_layer, lines, font, font_size, img_width, title_y_position)
            elif selected_style == 'cartoon_bold':
                self._render_cartoon_bold(draw, text_layer, lines, font, font_size, img_width, title_y_position)
            elif selected_style == 'painted_texture':
                self._render_painted_texture(draw, text_layer, lines, font, font_size, img_width, title_y_position)
            elif selected_style == 'gradient_shine':
                self._render_gradient_shine(draw, text_layer, lines, font, font_size, img_width, title_y_position)
            elif selected_style == 'shadow_3d':
                self._render_shadow_3d(draw, text_layer, lines, font, font_size, img_width, title_y_position)
            elif selected_style == 'sparkle_magic':
                self._render_sparkle_magic(draw, text_layer, lines, font, font_size, img_width, title_y_position)
            elif selected_style == 'word_color_pop':
                self._render_word_color_pop(draw, text_layer, lines, font, font_size, img_width, title_y_position)
            elif selected_style == 'modern_gradient':
                self._render_modern_gradient(draw, text_layer, lines, font, font_size, img_width, title_y_position)
            elif selected_style == 'playful_bounce':
                self._render_playful_bounce(draw, text_layer, lines, font, font_size, img_width, title_y_position)
            else:
                self._render_glossy_3d(draw, text_layer, lines, font, font_size, img_width, title_y_position)
            
            final_img = Image.alpha_composite(img, text_layer)
            final_img = final_img.convert('RGB')
            
            output = io.BytesIO()
            final_img.save(output, format='PNG', quality=95, optimize=True)
            output.seek(0)
            
            return File(output, name="cover_with_text.png")
            
        except Exception as e:
            Log.objects.create(
                title="Text Overlay Failed",
                type="error",
                message=f"Error adding text overlay: {str(e)}"
            )
            return None
    
    def _render_vibrant_glow(self, draw, text_layer, lines, font, font_size, img_width, start_y):
        line_height = int(font_size * 1.15)
        current_y = start_y
        colors = ['#FF1744', '#2196F3', '#FFD600', '#4CAF50', '#9C27B0', '#FF5722']
        
        for line_idx, line in enumerate(lines):
            bbox = draw.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            text_x = (img_width - text_width) // 2
            
            color = colors[line_idx % len(colors)]
            color_rgb = self._hex_to_rgb(color)
            
            for width in [16, 14, 12, 10]:
                alpha = 255
                for adj_x in range(-width, width + 1):
                    for adj_y in range(-width, width + 1):
                        distance = math.sqrt(adj_x**2 + adj_y**2)
                        if distance <= width:
                            draw.text((text_x + adj_x, current_y + adj_y), line, font=font, fill=(0, 0, 0, alpha))
            
            for width in [8, 6, 4]:
                alpha = 255
                for adj_x in range(-width, width + 1):
                    for adj_y in range(-width, width + 1):
                        distance = math.sqrt(adj_x**2 + adj_y**2)
                        if distance <= width:
                            draw.text((text_x + adj_x, current_y + adj_y), line, font=font, fill=(255, 255, 255, alpha))
            
            for i in range(4, 0, -1):
                draw.text((text_x + i, current_y + i), line, font=font, fill=(0, 0, 0, 180))
            
            draw.text((text_x, current_y), line, font=font, fill=color_rgb + (255,))
            
            current_y += line_height
    
    def _render_word_color_pop(self, draw, text_layer, lines, font, font_size, img_width, start_y):
        line_height = int(font_size * 1.2)
        current_y = start_y
        word_colors = ['#FF1744', '#9C27B0', '#2196F3', '#4CAF50', '#FF9800', '#E91E63']
        
        for line in lines:
            words = line.split()
            total_width = 0
            word_widths = []
            
            for word in words:
                bbox = draw.textbbox((0, 0), word + ' ', font=font)
                word_width = bbox[2] - bbox[0]
                word_widths.append(word_width)
                total_width += word_width
            
            start_x = (img_width - total_width) // 2
            current_x = start_x
            
            for word_idx, word in enumerate(words):
                color = word_colors[word_idx % len(word_colors)]
                color_rgb = self._hex_to_rgb(color)
                
                for width in [14, 12, 10]:
                    for adj_x in range(-width, width + 1):
                        for adj_y in range(-width, width + 1):
                            if math.sqrt(adj_x**2 + adj_y**2) <= width:
                                draw.text((current_x + adj_x, current_y + adj_y), word, font=font, fill=(255, 255, 255, 255))
                
                for width in [7, 5]:
                    for adj_x in range(-width, width + 1):
                        for adj_y in range(-width, width + 1):
                            if math.sqrt(adj_x**2 + adj_y**2) <= width:
                                draw.text((current_x + adj_x, current_y + adj_y), word, font=font, fill=(0, 0, 0, 255))
                
                draw.text((current_x, current_y), word, font=font, fill=color_rgb + (255,))
                
                current_x += word_widths[word_idx]
            
            current_y += line_height
    
    def _render_modern_gradient(self, draw, text_layer, lines, font, font_size, img_width, start_y):
        line_height = int(font_size * 1.2)
        current_y = start_y
        modern_gradients = [
            ('#667EEA', '#764BA2'), ('#F093FB', '#F5576C'), ('#4FACFE', '#00F2FE'),
            ('#43E97B', '#38F9D7'), ('#FA8BFF', '#2BD2FF')
        ]
        
        for line in lines:
            words = line.split()
            total_width = 0
            word_widths = []
            
            for word in words:
                bbox = draw.textbbox((0, 0), word + ' ', font=font)
                word_width = bbox[2] - bbox[0]
                word_widths.append(word_width)
                total_width += word_width
            
            start_x = (img_width - total_width) // 2
            current_x = start_x
            
            for word_idx, word in enumerate(words):
                grad_start, grad_end = modern_gradients[word_idx % len(modern_gradients)]
                start_rgb = self._hex_to_rgb(grad_start)
                end_rgb = self._hex_to_rgb(grad_end)
                mid_color = tuple(int((start_rgb[i] + end_rgb[i]) / 2) for i in range(3))
                
                for width in [12, 10, 8]:
                    for adj_x in range(-width, width + 1):
                        for adj_y in range(-width, width + 1):
                            if math.sqrt(adj_x**2 + adj_y**2) <= width:
                                draw.text((current_x + adj_x, current_y + adj_y), word, font=font, fill=(255, 255, 255, 255))
                
                for i in range(4, 0, -1):
                    draw.text((current_x + i, current_y + i), word, font=font, fill=(0, 0, 0, 180))
                
                draw.text((current_x, current_y), word, font=font, fill=mid_color + (255,))
                
                current_x += word_widths[word_idx]
            
            current_y += line_height
    
    def _render_playful_bounce(self, draw, text_layer, lines, font, font_size, img_width, start_y):
        line_height = int(font_size * 1.3)
        current_y = start_y
        bounce_colors = ['#FF6B9D', '#C44569', '#FFA502', '#FF6348', '#5F27CD', '#00D2D3']
        
        for line in lines:
            words = line.split()
            total_width = 0
            word_widths = []
            
            for word in words:
                bbox = draw.textbbox((0, 0), word + ' ', font=font)
                word_width = bbox[2] - bbox[0]
                word_widths.append(word_width)
                total_width += word_width
            
            start_x = (img_width - total_width) // 2
            current_x = start_x
            
            for word_idx, word in enumerate(words):
                bounce_offset = int(font_size * 0.1) if word_idx % 2 == 0 else -int(font_size * 0.05)
                word_y = current_y + bounce_offset
                
                color = bounce_colors[word_idx % len(bounce_colors)]
                color_rgb = self._hex_to_rgb(color)
                
                for width in [14, 12, 10]:
                    for adj_x in range(-width, width + 1):
                        for adj_y in range(-width, width + 1):
                            if math.sqrt(adj_x**2 + adj_y**2) <= width:
                                draw.text((current_x + adj_x, word_y + adj_y), word, font=font, fill=(255, 255, 255, 255))
                
                for i in range(4, 0, -1):
                    draw.text((current_x + i, word_y + i), word, font=font, fill=(0, 0, 0, 150))
                
                draw.text((current_x, word_y), word, font=font, fill=color_rgb + (255,))
                
                current_x += word_widths[word_idx]
            
            current_y += line_height
    
    def _render_glossy_3d(self, draw, text_layer, lines, font, font_size, img_width, start_y):
        line_height = int(font_size * 1.2)
        current_y = start_y
        glossy_colors = ['#E74C3C', '#8E44AD', '#3498DB', '#1ABC9C', '#F39C12', '#E91E63']
        
        for line in lines:
            words = line.split()
            total_width = 0
            word_widths = []
            
            for word in words:
                bbox = draw.textbbox((0, 0), word + ' ', font=font)
                word_width = bbox[2] - bbox[0]
                word_widths.append(word_width)
                total_width += word_width
            
            start_x = (img_width - total_width) // 2
            current_x = start_x
            
            for word_idx, word in enumerate(words):
                color = glossy_colors[word_idx % len(glossy_colors)]
                color_rgb = self._hex_to_rgb(color)
                
                for i in range(6, 0, -1):
                    draw.text((current_x + i, current_y + i), word, font=font, fill=(0, 0, 0, 180))
                
                for width in [11, 9, 7]:
                    for adj_x in range(-width, width + 1):
                        for adj_y in range(-width, width + 1):
                            if math.sqrt(adj_x**2 + adj_y**2) <= width:
                                draw.text((current_x + adj_x, current_y + adj_y), word, font=font, fill=(0, 0, 0, 255))
                
                for width in [5, 3]:
                    for adj_x in range(-width, width + 1):
                        for adj_y in range(-width, width + 1):
                            if math.sqrt(adj_x**2 + adj_y**2) <= width:
                                draw.text((current_x + adj_x, current_y + adj_y), word, font=font, fill=(255, 255, 255, 255))
                
                draw.text((current_x, current_y), word, font=font, fill=color_rgb + (255,))
                
                current_x += word_widths[word_idx]
            
            current_y += line_height
    
    def _render_rainbow_pop(self, draw, text_layer, lines, font, font_size, img_width, start_y):
        line_height = int(font_size * 1.15)
        current_y = start_y
        rainbow = ['#FF0000', '#FF7F00', '#FFFF00', '#00FF00', '#0000FF', '#9400D3']
        
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]
            text_x = (img_width - text_width) // 2
            
            words = line.split()
            current_x = text_x
            
            for word_idx, word in enumerate(words):
                color = rainbow[word_idx % len(rainbow)]
                color_rgb = self._hex_to_rgb(color)
                
                for width in [16, 14, 12]:
                    for adj_x in range(-width, width + 1):
                        for adj_y in range(-width, width + 1):
                            if math.sqrt(adj_x**2 + adj_y**2) <= width:
                                draw.text((current_x + adj_x, current_y + adj_y), word, font=font, fill=(0, 0, 0, 255))
                
                for width in [8, 6, 4]:
                    for adj_x in range(-width, width + 1):
                        for adj_y in range(-width, width + 1):
                            if math.sqrt(adj_x**2 + adj_y**2) <= width:
                                draw.text((current_x + adj_x, current_y + adj_y), word, font=font, fill=(255, 255, 255, 255))
                
                draw.text((current_x, current_y), word, font=font, fill=color_rgb + (255,))
                
                word_bbox = draw.textbbox((current_x, current_y), word, font=font)
                current_x = word_bbox[2] + int(font_size * 0.2)
            
            current_y += line_height
    
    def _render_neon_burst(self, draw, text_layer, lines, font, font_size, img_width, start_y):
        line_height = int(font_size * 1.15)
        current_y = start_y
        neon_colors = ['#FF00FF', '#00FFFF', '#FFFF00', '#00FF00', '#FF4500']
        
        for line_idx, line in enumerate(lines):
            bbox = draw.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]
            text_x = (img_width - text_width) // 2
            
            color = neon_colors[line_idx % len(neon_colors)]
            color_rgb = self._hex_to_rgb(color)
            
            for width in [12, 10, 8]:
                for adj_x in range(-width, width + 1):
                    for adj_y in range(-width, width + 1):
                        if math.sqrt(adj_x**2 + adj_y**2) <= width:
                            draw.text((text_x + adj_x, current_y + adj_y), line, font=font, fill=(0, 0, 0, 255))
            
            draw.text((text_x, current_y), line, font=font, fill=color_rgb + (255,))
            
            current_y += line_height
    
    def _render_cartoon_bold(self, draw, text_layer, lines, font, font_size, img_width, start_y):
        line_height = int(font_size * 1.15)
        current_y = start_y
        colors = ['#FF6B6B', '#4ECDC4', '#FFE66D', '#95E1D3', '#F38181', '#AA96DA']
        
        for line_idx, line in enumerate(lines):
            bbox = draw.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]
            text_x = (img_width - text_width) // 2
            
            color = colors[line_idx % len(colors)]
            color_rgb = self._hex_to_rgb(color)
            
            for width in [18, 16, 14]:
                for adj_x in range(-width, width + 1):
                    for adj_y in range(-width, width + 1):
                        if math.sqrt(adj_x**2 + adj_y**2) <= width:
                            draw.text((text_x + adj_x, current_y + adj_y), line, font=font, fill=(0, 0, 0, 255))
            
            for width in [10, 8, 6]:
                for adj_x in range(-width, width + 1):
                    for adj_y in range(-width, width + 1):
                        if math.sqrt(adj_x**2 + adj_y**2) <= width:
                            draw.text((text_x + adj_x, current_y + adj_y), line, font=font, fill=(255, 255, 255, 255))
            
            draw.text((text_x, current_y), line, font=font, fill=color_rgb + (255,))
            
            current_y += line_height
    
    def _render_painted_texture(self, draw, text_layer, lines, font, font_size, img_width, start_y):
        line_height = int(font_size * 1.15)
        current_y = start_y
        colors = ['#E74C3C', '#F39C12', '#2ECC71', '#3498DB', '#9B59B6']
        
        for line_idx, line in enumerate(lines):
            bbox = draw.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]
            text_x = (img_width - text_width) // 2
            
            color = colors[line_idx % len(colors)]
            color_rgb = self._hex_to_rgb(color)
            
            for width in [14, 12, 10]:
                for adj_x in range(-width, width + 1):
                    for adj_y in range(-width, width + 1):
                        if math.sqrt(adj_x**2 + adj_y**2) <= width:
                            draw.text((text_x + adj_x, current_y + adj_y), line, font=font, fill=(0, 0, 0, 255))
            
            for width in [7, 5]:
                for adj_x in range(-width, width + 1):
                    for adj_y in range(-width, width + 1):
                        if math.sqrt(adj_x**2 + adj_y**2) <= width:
                            draw.text((text_x + adj_x, current_y + adj_y), line, font=font, fill=(255, 255, 255, 255))
            
            draw.text((text_x, current_y), line, font=font, fill=color_rgb + (255,))
            
            current_y += line_height
    
    def _render_gradient_shine(self, draw, text_layer, lines, font, font_size, img_width, start_y):
        line_height = int(font_size * 1.15)
        current_y = start_y
        gradients = [
            ('#FF6B6B', '#FFE66D'), ('#4ECDC4', '#44A08D'), 
            ('#F857A6', '#FF5858'), ('#00C9FF', '#92FE9D')
        ]
        
        for line_idx, line in enumerate(lines):
            bbox = draw.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]
            text_x = (img_width - text_width) // 2
            
            start_color, end_color = gradients[line_idx % len(gradients)]
            start_rgb = self._hex_to_rgb(start_color)
            end_rgb = self._hex_to_rgb(end_color)
            mid_color = tuple(int((start_rgb[i] + end_rgb[i]) / 2) for i in range(3))
            
            for width in [14, 12, 10]:
                for adj_x in range(-width, width + 1):
                    for adj_y in range(-width, width + 1):
                        if math.sqrt(adj_x**2 + adj_y**2) <= width:
                            draw.text((text_x + adj_x, current_y + adj_y), line, font=font, fill=(255, 255, 255, 255))
            
            for i in range(4, 0, -1):
                draw.text((text_x + i, current_y + i), line, font=font, fill=(0, 0, 0, 180))
            
            draw.text((text_x, current_y), line, font=font, fill=mid_color + (255,))
            
            current_y += line_height
    
    def _render_shadow_3d(self, draw, text_layer, lines, font, font_size, img_width, start_y):
        line_height = int(font_size * 1.15)
        current_y = start_y
        colors = ['#FFD700', '#FF69B4', '#00CED1', '#FF6347', '#9370DB']
        
        for line_idx, line in enumerate(lines):
            bbox = draw.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]
            text_x = (img_width - text_width) // 2
            
            for i in range(6, 0, -1):
                draw.text((text_x + i, current_y + i), line, font=font, fill=(0, 0, 0, 200))
            
            for width in [12, 10, 8]:
                for adj_x in range(-width, width + 1):
                    for adj_y in range(-width, width + 1):
                        if math.sqrt(adj_x**2 + adj_y**2) <= width:
                            draw.text((text_x + adj_x, current_y + adj_y), line, font=font, fill=(255, 255, 255, 255))
            
            color = colors[line_idx % len(colors)]
            color_rgb = self._hex_to_rgb(color)
            draw.text((text_x, current_y), line, font=font, fill=color_rgb + (255,))
            
            current_y += line_height
    
    def _render_sparkle_magic(self, draw, text_layer, lines, font, font_size, img_width, start_y):
        line_height = int(font_size * 1.15)
        current_y = start_y
        colors = ['#FF1493', '#FFD700', '#00CED1', '#FF69B4', '#7B68EE']
        
        for line_idx, line in enumerate(lines):
            bbox = draw.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]
            text_x = (img_width - text_width) // 2
            
            color = colors[line_idx % len(colors)]
            color_rgb = self._hex_to_rgb(color)
            
            for width in [14, 12, 10]:
                for adj_x in range(-width, width + 1):
                    for adj_y in range(-width, width + 1):
                        if math.sqrt(adj_x**2 + adj_y**2) <= width:
                            draw.text((text_x + adj_x, current_y + adj_y), line, font=font, fill=(0, 0, 0, 255))
            
            for width in [7, 5]:
                for adj_x in range(-width, width + 1):
                    for adj_y in range(-width, width + 1):
                        if math.sqrt(adj_x**2 + adj_y**2) <= width:
                            draw.text((text_x + adj_x, current_y + adj_y), line, font=font, fill=(255, 255, 255, 255))
            
            draw.text((text_x, current_y), line, font=font, fill=color_rgb + (255,))
            
            current_y += line_height
    
    def _resize_cover_image(self, image_file):
        try:
            image_file.seek(0)
            img = Image.open(image_file)
            
            if img.mode not in ('RGB', 'RGBA'):
                img = img.convert('RGB')
            
            target_width, target_height = 2100, 2800
            target_ratio = target_width / target_height
            img_ratio = img.width / img.height
            
            if img_ratio > target_ratio:
                new_height = target_height
                new_width = int(target_height * img_ratio)
            else:
                new_width = target_width
                new_height = int(target_width / img_ratio)
            
            img_resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            background = img_resized.copy()
            background = background.filter(ImageFilter.GaussianBlur(radius=80))
            
            enhancer = ImageEnhance.Brightness(background)
            background = enhancer.enhance(0.6)
            
            background = background.resize((target_width, target_height), Image.Resampling.LANCZOS)
            
            canvas = Image.new('RGB', (target_width, target_height))
            canvas.paste(background, (0, 0))
            
            paste_x = (target_width - img_resized.width) // 2
            paste_y = (target_height - img_resized.height) // 2
            
            if img_resized.mode == 'RGBA':
                canvas.paste(img_resized, (paste_x, paste_y), img_resized)
            else:
                canvas.paste(img_resized, (paste_x, paste_y))
            
            output = io.BytesIO()
            canvas.save(output, format='PNG', quality=95, optimize=True)
            output.seek(0)
            return File(output, name="cover_cropped.png")
        except Exception as e:
            Log.objects.create(
                title="Cover resize failed", 
                type="error", 
                message=str(e)
            )
            return image_file