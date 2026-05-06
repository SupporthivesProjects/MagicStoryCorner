import os
import io
from typing import Dict, Any, Tuple, Optional
from time import sleep
from PIL import Image, ImageFilter, ImageEnhance
from django.core.files.base import File
import google.generativeai as genai
from products.models import ProductBook
from stories.models import AIModel, ImageStyle
from logs.models import Log


class GeminiCoverGenerator:
    
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

            word_spelling = "\n".join([f"  * '{word}' = {'-'.join(word.upper())}" for word in title_display.split()])

            prompt = (
                f"REFERENCE IMAGES PROVIDED: {len(reference_images)} character(s)\n\n"
                f"Analyze each reference image:\n"
                f"{ref_instructions}\n"
                f"Identify: exact hair color/style/length, facial features, clothing colors, body proportions, accessories{story_context}\n\n"
                f"CRITICAL RULES:\n"
                f"- Match ALL characteristics from reference images EXACTLY\n"
                f"- Hair: Match color, style, length EXACTLY\n"
                f"- Face: Match features EXACTLY\n"
                f"- Clothing: Match colors and style EXACTLY\n"
                f"- Body: Match proportions EXACTLY\n"
            )
            
            if has_main:
                prompt += f"- Reference Image 1 (MAIN CHARACTER) must be the largest and most prominent\n"
            
            prompt += (
                f"- Include ALL {len(reference_images)} characters together\n"
                f"- DO NOT modify any feature\n\n"
                f"COVER DESIGN:\n"
                f"- Vibrant children's book cover illustration\n"
                f"- Art style: {imagestyle}\n"
                f"- Full bleed background to all edges\n"
            )
            
            if has_main:
                prompt += f"- MAIN CHARACTER prominently featured in center-bottom\n"
                prompt += f"- Supporting characters arranged naturally around main character\n"
            else:
                prompt += f"- All characters prominently featured in center-bottom\n"
            
            prompt += (
                f"- Characters positioned with 10-15% margin from edges\n"
                f"- Professional children's book cover, NOT a book mockup\n\n"
                f"TITLE TEXT SPELLING (CRITICAL - READ CAREFULLY):\n"
                f"The exact title to display is: {title_display}\n\n"
                f"SPELL EACH WORD LETTER-BY-LETTER:\n"
                f"{word_spelling}\n\n"
                f"SPELLING VERIFICATION RULES:\n"
                f"- Copy each letter EXACTLY as shown above\n"
                f"- DO NOT skip any letters\n"
                f"- DO NOT add extra letters\n"
                f"- DO NOT swap or rearrange letters\n"
                f"- DO NOT replace similar looking letters\n"
                f"- Count the letters in each word and match exactly\n\n"
                f"TITLE DISPLAY REQUIREMENTS:\n"
                f"- Display the title EXACTLY: \"{title_display}\"\n"
                f"- LARGE, BOLD, COLORFUL, CHILD-FRIENDLY LETTERS\n"
                f"- CENTERED horizontally at TOP with 15-20% margin from left/right edges\n"
                f"- Title must stay within central 50-60% of image width\n"
                f"- Title must be clearly visible and readable\n"
                f"- NO other text besides the title\n\n"
                f"Generate stunning cover with perfect character consistency and proper title placement."
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
            
            cropped_cover = self._resize_cover_image(
                File(io.BytesIO(cover_content), name="cover_original.png")
            )
            
            if cropped_cover:
                return File(io.BytesIO(cover_content), name="cover_original.png"), cropped_cover
            
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