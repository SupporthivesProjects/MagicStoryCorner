import re
import os
import io
import requests
from io import BytesIO
from time import sleep
from django.core.files import File
from django.utils.text import slugify
from django.db import transaction
from products.models import ProductBookPage, ProductBook
from stories.models import AIModel, LanguageOption, NarratorVoice, StoryBook, StoryBookPage, ChildAgeRange, StorySetting, StoryEnd, StoryLength, StoryPlot, StoryTheme, StoryTone, ImageStyle
from logs.models import Log
from concurrent.futures import ThreadPoolExecutor, as_completed
from PIL import Image, ImageDraw, ImageFont
import google.generativeai as genai
from openai import OpenAI
from products.usage_tracker import UsageTracker
from products.models import Configuration
from PIL import ImageFilter, ImageEnhance
from storybook.utils.cover_title_helper import add_title_to_cover

class ProductBookBuilder:
    def __init__(self, user, input_data):
        self.user = user
        self.input = input_data

        config = Configuration.objects.filter(type='admin', is_active=True).first()
        self.CHARACTERS_PER_PAGE = config.chars_per_page if config else 400
        self.MAX_PAGES_LIMIT = config.max_pages if config else 25
        self.IMAGE_RETRIES = config.img_retries if config else 3
        self.TTS_RETRIES = config.tts_retries if config else 3
        self.MAX_WORKERS = config.workers if config else 10
        self.CHARACTER_CONSISTENCY_COUNT = config.consistency_checks if config else 3
        self.STORY_GENERATION_MAX_RETRIES = config.story_retries if config else 3
        self.STORY_LENGTH_MIN_THRESHOLD = config.min_story_len if config else 70

        self.CHARS_PER_TOKEN = 3.5
        self.OPENAI_MAX_TOKENS = 4096
        self.OPENAI_MIN_OUTPUT_TOKENS = 1024
        self.OPENAI_OUTPUT_BUFFER = 500

        self.text_model = AIModel.objects.filter(type="text", is_active=True).first()
        self.image_model = AIModel.objects.filter(type="image", is_active=True).first()
        self.tts_model = AIModel.objects.filter(type="tts", is_active=True).first()

        self.openai_key = self.text_model.apikey if self.text_model else None
        self.openai_name = self.text_model.name if self.text_model else None
        self.elevenlabs_key = self.tts_model.apikey if self.tts_model else None
        self.gemini_key = self.image_model.apikey if self.image_model else None
        self.gemini_name = self.image_model.name if self.image_model else None
        
        if self.openai_key:
            self.openai_client = OpenAI(api_key=self.openai_key)
        else:
            self.openai_client = None
        
        if self.gemini_key:
            genai.configure(api_key=self.gemini_key)
        
        self.refined_character_desc = None

        self.supporting_characters_count = max(0, self.CHARACTER_CONSISTENCY_COUNT - 1)
        
        self.character_references = {
            'main': {
                'name': '',
                'description': '',
                'image': None,
                'role': 'main'
            }
        }
        
        for i in range(self.supporting_characters_count):
            char_key = f'sub_{i+1}' if i > 0 else 'sub'
            self.character_references[char_key] = {
                'name': '',
                'description': '',
                'image': None,
                'role': 'supporting'
            }

        self.current_book_id = None
        self.min_chars = 0
        self.max_chars = 0
        self.max_pages = 0
        self.usage_tracker = UsageTracker()

    def get_content(self, model_class, obj_id):
        if not obj_id:
            return ""
        obj = model_class.objects.filter(pk=obj_id).first()
        return obj.content if obj else ""
    
    def get_narrator_vid(self, narrator_id):
        if not narrator_id:
            return None
        narrator = NarratorVoice.objects.filter(pk=narrator_id).first()
        return narrator.vid if narrator else None

    def refine_character_description(self, character_name="", character_desc="", char_type="main"):
        if not self.openai_client:
            Log.objects.create(
                title="Missing OpenAI API key", 
                type="error", 
                message=f"Cannot refine character description"
            )
            return character_desc
        
        if char_type == "main":
            character_name = self.input.get("character_name", "")
            character_desc = self.input.get("character_desc", "")
        
        childgroup = self.get_content(ChildAgeRange, self.input.get("childgroup_id"))
        setting = self.get_content(StorySetting, self.input.get("setting_id"))
        setting_desc = self.input.get("setting_desc", "")
        imagestyle = self.get_content(ImageStyle, self.input.get("imagestyle_id"))
        
        prompt = f"""Refine character description for children's book illustration:

        Character Type: {char_type}
        Character: {character_name}
        Description: {character_desc}
        Context: {childgroup}, {setting} ({setting_desc}), {imagestyle} style

        - Keep all user-provided visual details (colors, clothing, features)
        - Add missing visual details based on character name and context
        - If very short or no description, create one from character name and provided description
        - Replace any inappropriate, violent, scary, or weapon-related terms with wholesome, child-friendly alternatives
        - Remove personality traits, keep only physical appearance
        - Output 2-3 sentences, visual only"""

        try:
            response = self.openai_client.chat.completions.create(
                model= self.openai_name or 'gpt-4-turbo' ,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
                temperature=0.7
            )
            refined_desc = response.choices[0].message.content.strip()
            self.usage_tracker.add_openai_usage(response)
            
            return refined_desc
            
        except Exception as e:
            Log.objects.create(
                title="Character refinement failed",
                type="error",
                message=f"Error: {str(e)}. Using original description."
            )
            return character_desc
        
    def extract_characters_from_story(self, story_text):
        if not self.openai_client:
            return []
        
        character_name = self.input.get("character_name", "")
        
        prompt = f"""Analyze this children's story and identify the {self.supporting_characters_count} most important supporting characters (besides the main character {character_name}).

        Story:
        {story_text[:2000]}

        For each supporting character, provide:
        1. Name (extract exact name from story)
        2. Physical description (appearance, clothing, colors, features - be specific)
        3. Role in story (their relationship to main character and purpose)

        Return ONLY a valid JSON array with exactly {self.supporting_characters_count} characters (or fewer if not enough exist):
        [
        {{"name": "Character Name", "description": "Detailed physical description", "role": "Their role in the story"}}
        ]

        Rules:
        - Extract exact character names as they appear in the story
        - Physical descriptions must be detailed and visual
        - Focus on recurring characters who interact with {character_name}
        - Return maximum {self.supporting_characters_count} supporting characters
        - If fewer supporting characters exist, return fewer entries
        - Return empty array [] if no supporting characters found
        - No personality traits, only physical appearance"""

        try:
            response = self.openai_client.chat.completions.create(
                model=self.openai_name or 'gpt-4-turbo',
                messages=[{"role": "user", "content": prompt}],
                max_tokens=400,
                temperature=0.7
            )
            result = response.choices[0].message.content.strip()
            self.usage_tracker.add_openai_usage(response)
            
            import json
            json_match = re.search(r'\[.*\]', result, re.DOTALL)
            if json_match:
                characters = json.loads(json_match.group())
                validated_chars = []
                for char in characters[:self.supporting_characters_count]:
                    if char.get('name') and char.get('description') and char.get('role'):
                        validated_chars.append(char)
                return validated_chars
            
        except Exception as e:
            Log.objects.create(
                title="Character extraction failed",
                type="warning",
                message=f"Error: {str(e)}. Continuing without supporting characters."
            )
        
        return []
        

    def generate_book_description(self, title, story_text):
        character_name = self.input.get("character_name", "our hero")
        childgroup_obj = ChildAgeRange.objects.filter(pk=self.input.get("childgroup_id")).first()
        age_range = childgroup_obj.age_range if childgroup_obj and hasattr(childgroup_obj, 'age_range') else "young"
        theme = self.get_content(StoryTheme, self.input.get("theme_id")) or "adventure"
        story_excerpt = (story_text or "")[:800]
        
        prompt = f"""Write a professional children's book description based on this story:

        Story: {story_excerpt}
        Character: {character_name}
        Age: {age_range}
        Theme: {theme}

        Section 1 (2-3 sentences): Start with "Embark on a magical journey with {character_name}..." Mention ages {age_range}, captivating illustrations, engaging narration, and what world/discovery awaits.

        Section 2 (3-4 sentences): Start with "Join {character_name} as..." Describe the quest, challenges faced, teamwork and courage. End with how children will be captivated by the bravery and whimsical world. Add natural paragraph breaks within this section for better readability.

        Use marketing language that appeals to parents and children. Natural prose, no lists."""
        
        try:
            response = self.openai_client.chat.completions.create(
                model=self.openai_name or 'gpt-4-turbo',
                messages=[{"role": "user", "content": prompt}],
                max_tokens=400,
                temperature=0.7
            )
            content = response.choices[0].message.content.strip()
            self.usage_tracker.add_openai_usage(response)
            
            content = re.sub(r'Section \d+.*?:\s*', '', content, flags=re.IGNORECASE)
            content = re.sub(r'Discover the Magic Inside.*?:\s*', '', content, flags=re.IGNORECASE)
            content = re.sub(r'The Adventure Within.*?:\s*', '', content, flags=re.IGNORECASE)
            content = re.sub(r'\*\*.*?\*\*:\s*', '', content)
            
            sections = [s.strip() for s in content.split('\n\n') if s.strip()]
            
            if len(sections) >= 2:
                para1 = sections[0]
                para2 = '\n\n'.join(sections[1:])
                
                return f'<b class="section_title">Discover the Magic Inside</b>\n{para1}\n\n<b class="section_title">The Adventure Within</b>\n{para2}'
            
            return self._get_fallback_description(title)
            
        except Exception as e:
            Log.objects.create(title="Book description generation failed", type="error", message=f"Error: {str(e)}")
            return self._get_fallback_description(title)


    def _get_fallback_description(self, title):
        character_name = self.input.get("character_name", "our hero")
        childgroup_obj = ChildAgeRange.objects.filter(pk=self.input.get("childgroup_id")).first()
        age_range = childgroup_obj.age_range if childgroup_obj and hasattr(childgroup_obj, 'age_range') else "young"
        theme = self.get_content(StoryTheme, self.input.get("theme_id")) or "adventure"
        
        section1 = f"Embark on a magical journey with {character_name} in this enchanting children's book designed for ages {age_range}. With captivating illustrations and engaging narration, young readers will be transported to a world filled with wonder and adventure as {character_name} discovers a hidden world that leads to a magical land."
        
        section2 = f"Join {character_name} as they befriend new companions and set off on a daring quest through a world filled with {theme}.\n\nAlong the way, {character_name} and their new friends face challenges and obstacles, but with teamwork and courage, they overcome them all. Children will be captivated by {character_name}'s bravery and determination as they navigate through this whimsical world filled with friendly characters and beautiful landscapes."
        
        return f'<b class="section_title">Discover the Magic Inside</b>\n{section1}\n\n<b class="section_title">The Adventure Within</b>\n{section2}'
    
    def generate_unique_slug(self, title):
        base_slug = slugify(title)
        if not base_slug:
            base_slug = "story"
        slug = base_slug
        counter = 1
        while ProductBook.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        return slug

    def build_prompt(self):
        length_obj = StoryLength.objects.filter(pk=self.input.get("storylength_id")).first()
        min_pages = length_obj.min if length_obj else 1
        max_pages = length_obj.max if length_obj else 3

        self.min_chars = min_pages * self.CHARACTERS_PER_PAGE
        safe_pages = min(max_pages, self.MAX_PAGES_LIMIT)
        self.max_chars = safe_pages * self.CHARACTERS_PER_PAGE
        self.max_pages = safe_pages
        self.avg_chars = (self.min_chars + self.max_chars) / 2.0

        if not self.refined_character_desc:
            self.refined_character_desc = self.refine_character_description()

        self.data = {
            "childgroup": self.get_content(ChildAgeRange, self.input.get("childgroup_id")),
            "character_name": self.input.get("character_name", ""),
            "character_desc": self.refined_character_desc,
            "setting": self.get_content(StorySetting, self.input.get("setting_id")),
            "setting_desc": self.input.get("setting_desc", ""),
            "plot": self.get_content(StoryPlot, self.input.get("plot_id")),
            "plot_desc": self.input.get("plot_desc", ""),
            "theme": self.get_content(StoryTheme, self.input.get("theme_id")),
            "theme_desc": self.input.get("theme_desc", ""),
            "tone": self.get_content(StoryTone, self.input.get("tone_id")),
            "storylength": self.get_content(StoryLength, self.input.get("storylength_id")),
            "imagestyle": self.get_content(ImageStyle, self.input.get("imagestyle_id")),
            "outputlanguage": self.get_content(LanguageOption, self.input.get("language_id")),
            "voice_id": self.get_narrator_vid(self.input.get("narrator_id")),
        }

        prompt = f"""Write a complete children's story for age {self.data['childgroup']}.

        Character: {self.data['character_name']} - {self.data['character_desc']}
        Setting: {self.data['setting']} - {self.data['setting_desc']}
        Plot: {self.data['plot']} - {self.data['plot_desc']}
        Theme: {self.data['theme']} - {self.data['theme_desc']}
        Tone: {self.data['tone']}
        Language: {self.data['outputlanguage']}

        CRITICAL CHARACTER LIMIT REQUIREMENTS:
        1. Start with 'Title: <story title>' on the first line
        2. Title MUST be SHORT (maximum 4-6 words), attractive, and meaningful
        3. Story MUST be between {self.min_chars} and {self.max_chars} characters EXACTLY
        4. DO NOT exceed {self.max_chars} characters under ANY circumstance
        5. Story body ONLY (excluding title) must be {self.min_chars} to {self.max_chars} characters
        6. Count characters carefully - STOP writing when you reach {self.max_chars} characters
        7. MUST have complete beginning, middle, and satisfying ending
        8. Structure: Beginning (25%), Middle (50%), Ending (25%)
        9. Character descriptions: Maximum 3 sentences total when introducing characters
        10. Focus on action, dialogue, and plot progression
        11. Use descriptive, adventurous, age-appropriate language

        CHARACTER COUNTING:
        - Include ONLY story text in character count (not title)
        - Count spaces and punctuation
        - Story must use {self.min_chars}-{self.max_chars} characters max

        ENDING REQUIREMENTS (VERY IMPORTANT):
        - Story MUST end with a complete sentence followed by a period
        - Do NOT end mid-word, mid-sentence, or mid-paragraph
        - Last sentence must be a proper conclusion
        - Every sentence must be grammatically complete
        - Ensure final paragraph provides closure and resolution

        LENGTH VERIFICATION BEFORE SUBMITTING:
        - Verify story body is between {self.min_chars} and {self.max_chars} characters
        - Do NOT truncate at character limit - reduce content earlier if needed
        - Read the entire ending to verify it's complete
        - Confirm story ends with period, not comma or mid-word

        Write the complete story now with EXACT character count between {self.min_chars} and {self.max_chars}:"""
        return prompt


    def generate_story(self):
        if not self.openai_client:
            Log.objects.create(
                title="Missing OpenAI API key", 
                type="error", 
                message=f"Admin tried to generate a story but no API key is configured."
            )
            return None, None

        MAX_RETRIES = self.STORY_GENERATION_MAX_RETRIES
        
        all_attempts = []
        
        for attempt in range(MAX_RETRIES):
            prompt = self.build_prompt()
            
            if attempt > 0 and all_attempts:
                best_attempt = max(all_attempts, key=lambda x: len(x['story_text']))
                best_length = len(best_attempt['story_text'])
                shortage = self.min_chars - best_length
                
                if shortage > 0:
                    prompt += f"\n\nCRITICAL: Previous attempt generated {best_length} characters but MUST be at least {self.min_chars} characters (need {shortage} MORE). Add more dialogue, descriptions, and character interactions. Do NOT go below {self.min_chars} or above {self.max_chars} characters."
                elif best_length > self.max_chars:
                    prompt += f"\n\nWARNING: Previous attempt generated {best_length} characters which exceeds maximum {self.max_chars}. Reduce content and ensure story is between {self.min_chars} and {self.max_chars} characters EXACTLY."
            
            required_output_chars = self.max_chars + 500
            estimated_tokens = int(required_output_chars / self.CHARS_PER_TOKEN) + self.OPENAI_OUTPUT_BUFFER
            
            max_tokens = min(estimated_tokens, self.OPENAI_MAX_TOKENS)
            max_tokens = max(max_tokens, self.OPENAI_MIN_OUTPUT_TOKENS)

            try:
                response = self.openai_client.chat.completions.create(
                    model=self.openai_name or 'gpt-4-turbo',
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=max_tokens,
                    temperature=0.7
                )

                story_text = response.choices[0].message.content.strip()
                self.usage_tracker.add_openai_usage(response)

                if not story_text:
                    continue

                title_match = re.search(r'(?i)^title[:\-–]\s*(.+)', story_text, re.MULTILINE)
                if not title_match:
                    title_match = re.search(r'(?i)title[:\-–]\s*(.+)', story_text)

                title = title_match.group(1).strip().strip('"\'*#') if title_match else "Untitled Story"

                story_text = re.sub(r'(?i)^\*+\s*$', '', story_text, flags=re.MULTILINE)
                story_text = re.sub(r'(?i)^.*title[:\-–].*$', '', story_text, flags=re.MULTILINE)
                story_text = re.sub(r'^\s*[\*\-=_]{2,}\s*$', '', story_text, flags=re.MULTILINE)
                story_text = story_text.strip()
                
                story_length = len(story_text)
                
                if story_length > self.max_chars:
                    last_period = story_text[:self.max_chars].rfind('.')
                    if last_period > self.min_chars:
                        story_text = story_text[:last_period + 1].strip()
                        story_length = len(story_text)
                    else:
                        story_text = story_text[:self.max_chars].strip()
                        if not story_text.endswith('.'):
                            last_space = story_text.rfind(' ')
                            if last_space > 0:
                                story_text = story_text[:last_space] + '.'
                        story_length = len(story_text)
                
                all_attempts.append({
                    'title': title,
                    'story_text': story_text,
                    'length': story_length,
                    'attempt': attempt + 1
                })
                
                min_threshold = int(self.min_chars * (self.STORY_LENGTH_MIN_THRESHOLD / 100.0))
                if story_length >= min_threshold and story_length <= self.max_chars:
                    return title, story_text
                            
            except Exception as e:
                if attempt < MAX_RETRIES - 1:
                    continue
                else:
                    Log.objects.create(
                        title="Story generation failed after all retries", 
                        type="error", 
                        message=f"All {MAX_RETRIES} attempts failed. Final error: {str(e)}"
                    )
                    
                    if all_attempts:
                        break
                    return None, None
        
        if all_attempts:
            best_attempt = max(all_attempts, key=lambda x: x['length'])
            min_threshold = int(self.min_chars * (self.STORY_LENGTH_MIN_THRESHOLD / 100.0))
            if best_attempt['length'] >= min_threshold:
                return best_attempt['title'], best_attempt['story_text']
        
        return None, None


    def divide_pages(self, story_text):
        import math
        
        total_chars = len(story_text)
        
        if total_chars == 0:
            return [""]
        
        if total_chars < self.CHARACTERS_PER_PAGE * 0.7:
            return [story_text.strip()]
        
        target_pages = max(1, round(total_chars / self.CHARACTERS_PER_PAGE))
        
        if target_pages > self.MAX_PAGES_LIMIT:
            target_pages = self.MAX_PAGES_LIMIT
        
        min_pages = self.min_chars // self.CHARACTERS_PER_PAGE
        if target_pages < min_pages:
            target_pages = min_pages
        
        avg_chars_per_page = total_chars / target_pages
        min_page_chars = avg_chars_per_page * 0.75
        
        pages = []
        position = 0
        
        for page_num in range(target_pages):
            if page_num == target_pages - 1:
                remaining = story_text[position:].strip()
                if remaining and len(remaining) >= min_page_chars * 0.5:
                    pages.append(remaining)
                elif pages and remaining:
                    pages[-1] = pages[-1] + ' ' + remaining
                break
            
            ideal_end = int(position + avg_chars_per_page)
            min_end = int(position + min_page_chars)
            max_end = min(int(position + avg_chars_per_page * 1.4), len(story_text))
            
            if position >= len(story_text):
                break
            
            remaining_length = len(story_text) - position
            if remaining_length < avg_chars_per_page * 0.5:
                if pages:
                    pages[-1] = pages[-1] + ' ' + story_text[position:].strip()
                else:
                    pages.append(story_text[position:].strip())
                break
            
            search_text = story_text[min_end:max_end]
            best_pos = -1
            best_score = -1
            
            for match in re.finditer(r'\n\n+', search_text):
                pos = min_end + match.end()
                distance_score = 1.0 - abs(pos - ideal_end) / avg_chars_per_page
                final_score = 100 + (distance_score * 50)
                if final_score > best_score:
                    best_score = final_score
                    best_pos = pos
            
            if best_pos == -1:
                for match in re.finditer(r'[.!?।]["\'")]?\s+(?=[A-Z"\'\u0900-\u097F])', search_text):
                    pos = min_end + match.end()
                    distance_score = 1.0 - abs(pos - ideal_end) / avg_chars_per_page
                    final_score = 80 + (distance_score * 40)
                    if final_score > best_score:
                        best_score = final_score
                        best_pos = pos
            
            if best_pos == -1:
                for match in re.finditer(r'[.!?।]["\'")]?\s*\n', search_text):
                    pos = min_end + match.end()
                    distance_score = 1.0 - abs(pos - ideal_end) / avg_chars_per_page
                    final_score = 70 + (distance_score * 35)
                    if final_score > best_score:
                        best_score = final_score
                        best_pos = pos
            
            if best_pos == -1:
                for match in re.finditer(r'\n', search_text):
                    pos = min_end + match.end()
                    distance_score = 1.0 - abs(pos - ideal_end) / avg_chars_per_page
                    final_score = 50 + (distance_score * 25)
                    if final_score > best_score:
                        best_score = final_score
                        best_pos = pos
            
            if best_pos == -1:
                for match in re.finditer(r'[,;:]\s+', search_text):
                    pos = min_end + match.end()
                    distance_score = 1.0 - abs(pos - ideal_end) / avg_chars_per_page
                    final_score = 40 + (distance_score * 20)
                    if final_score > best_score:
                        best_score = final_score
                        best_pos = pos
            
            if best_pos == -1:
                for match in re.finditer(r'\s+', search_text):
                    pos = min_end + match.end()
                    distance_score = 1.0 - abs(pos - ideal_end) / avg_chars_per_page
                    final_score = 20 + (distance_score * 10)
                    if final_score > best_score:
                        best_score = final_score
                        best_pos = pos
            
            if best_pos == -1:
                best_pos = ideal_end
            
            if best_pos > position and best_pos <= len(story_text):
                page_content = story_text[position:best_pos].strip()
                if len(page_content) >= min_page_chars * 0.5:
                    pages.append(page_content)
                    position = best_pos
                else:
                    position = best_pos
            else:
                remaining_text = story_text[position:].strip()
                if remaining_text and len(remaining_text) >= min_page_chars * 0.5:
                    pages.append(remaining_text)
                break
        
        final_pages = []
        for i, page in enumerate(pages):
            cleaned = page.strip()
            if cleaned:
                if i == len(pages) - 1:
                    if len(cleaned) >= min_page_chars * 0.4:
                        final_pages.append(cleaned)
                    elif final_pages:
                        final_pages[-1] = final_pages[-1] + ' ' + cleaned
                else:
                    final_pages.append(cleaned)
        
        if not final_pages:
            final_pages = [story_text.strip()]
        
        if len(final_pages) > self.MAX_PAGES_LIMIT:
            while len(final_pages) > self.MAX_PAGES_LIMIT:
                last_page = final_pages.pop()
                if final_pages:
                    final_pages[-1] = final_pages[-1] + ' ' + last_page
                else:
                    final_pages.append(last_page)
        
        return final_pages

    def generate_image_gemini(self, prompt):
        if not self.gemini_key:
            Log.objects.create(
                title="Missing Gemini API key", 
                type="error", 
                message="Cannot generate image without Gemini API key"
            )
            return None
        
        for attempt in range(self.IMAGE_RETRIES):
            try:
                model = genai.GenerativeModel(self.gemini_name or 'gemini-2.5-flash-image')
                response = model.generate_content(prompt)
                self.usage_tracker.add_gemini_usage(response)
                
                if not response or not response.parts:
                    if attempt < self.IMAGE_RETRIES - 1:
                        continue
                    else:
                        break
                
                image_part = None
                for part in response.parts:
                    if hasattr(part, 'inline_data') and part.inline_data:
                        image_part = part
                        break
                
                if not image_part:
                    if attempt < self.IMAGE_RETRIES - 1:
                        continue
                    else:
                        break
                
                data = image_part.inline_data.data
                return File(BytesIO(data), name="image.png")
                    
            except Exception as e:
                error_message = str(e).lower()
                if "safety" in error_message or "policy" in error_message or "blocked" in error_message:
                    if attempt == self.IMAGE_RETRIES - 1:
                        Log.objects.create(
                            title="Image generation blocked by safety policy", 
                            type="error", 
                            message=f"{str(e)}"
                        )
                else:
                    if attempt == self.IMAGE_RETRIES - 1:
                        Log.objects.create(
                            title="Image generation failed", 
                            type="error", 
                            message=f"All {self.IMAGE_RETRIES} attempts failed - {str(e)}"
                        )
        
        return None

    def generate_image_with_character_reference(self, prompt, characters_in_scene=None):
        if not self.gemini_key:
            return self.generate_image_gemini(prompt)
        
        if characters_in_scene is None:
            characters_in_scene = ['main']
        
        reference_images = []
        character_descriptions = []
        
        for idx, char_type in enumerate(characters_in_scene, 1):
            char_data = self.character_references.get(char_type, {})
            if char_data.get('image') and char_data.get('name'):
                reference_images.append(char_data['image'])
                role = char_data.get('role', 'character')
                age_group = char_data.get('age_group') 
                character_descriptions.append(
                    f"CHARACTER #{idx} - {char_data['name']} ({role}):\n"
                    f"Age Group: {age_group}\n"
                    f"Physical Description: {char_data['description']}\n"
                    f"HEIGHT/SIZE: Must match reference image EXACTLY"
                )
        
        if not reference_images:
            return self.generate_image_gemini(prompt)
        
        for attempt in range(self.IMAGE_RETRIES):
            try:
                model = genai.GenerativeModel(self.gemini_name or 'gemini-2.5-flash-image')
                
                pil_images = [Image.open(io.BytesIO(img_data)) for img_data in reference_images]
                
                char_list = "\n\n".join(character_descriptions)
                
                enhanced_prompt = (
                    f"REFERENCE IMAGES PROVIDED: {len(reference_images)} character(s)\n\n"
                    f"YOU MUST USE THESE EXACT CHARACTER DESIGNS:\n{char_list}\n\n"
                    f"CRITICAL CONSISTENCY RULES:\n"
                    f"1. Each character's HEIGHT must match reference image EXACTLY\n"
                    f"2. Each character's AGE must match reference EXACTLY\n"
                    f"3. BODY PROPORTIONS (head-to-body ratio) must match reference\n"
                    f"4. If reference shows a child, keep as child in scene\n"
                    f"5. Do NOT make characters taller or shorter than reference\n"
                    f"6. Match facial features, hair, clothing, colors EXACTLY\n"
                    f"SCENE TO GENERATE:\n{prompt}\n\n"
                    f"VERIFICATION CHECKLIST:\n"
                    f"✓ Face matches reference (eyes, nose, mouth, expression)\n"
                    f"✓ Hair color, style, length identical\n"
                    f"✓ Body proportions match\n"
                    f"✓ Clothing colors and patterns match\n"
                    f"✓ All distinctive features present\n"
                    f"✓ Character instantly recognizable from reference\n\n"
                    f"Generate the scene with ALL characters matching their references exactly."
                )
                
                content = pil_images + [enhanced_prompt]
                
                response = model.generate_content(content)
                self.usage_tracker.add_gemini_usage(response)
                
                if not response or not response.parts:
                    continue
                
                image_part = None
                for part in response.parts:
                    if hasattr(part, 'inline_data') and part.inline_data:
                        image_part = part
                        break
                
                if not image_part:
                    continue
                
                data = image_part.inline_data.data
                return File(BytesIO(data), name="scene.png")
                    
            except Exception as e:
                error_msg = str(e).lower()
                if "safety" in error_msg or "policy" in error_msg or "blocked" in error_msg:
                    pass
                else:
                    if attempt == self.IMAGE_RETRIES - 1:
                        Log.objects.create(
                            title="Multi-character scene failed", 
                            type="error", 
                            message=f"All attempts failed with {len(reference_images)} references"
                        )
        
        return None
    
    def resize_cover_image(self, image_file):
        if not image_file:
            return None
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
            
            output = BytesIO()
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

    def generate_tts(self, text, voice_id):
        if not voice_id:
            return None
        if not self.elevenlabs_key:
            Log.objects.create(
                title="TTS skipped", 
                type="warning", 
                message="ElevenLabs key missing"
            )
            return None
        
        for attempt in range(self.TTS_RETRIES):
            try:
                resp = requests.post(
                    f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
                    headers={
                        "xi-api-key": self.elevenlabs_key, 
                        "Content-Type": "application/json"
                    },
                    json={
                        "text": text, 
                        "voice_settings": {
                            "stability": 0.5, 
                            "similarity_boost": 0.5
                        }
                    },
                    timeout=90
                )
                
                if resp.status_code == 200:
                    self.usage_tracker.add_elevenlabs_usage(resp.headers, text)
                    return File(BytesIO(resp.content), name="audio.mp3")
                else:
                    Log.objects.create(
                        title="TTS request failed",
                        type="error",
                        message=f"Attempt {attempt + 1}/{self.TTS_RETRIES} - Status {resp.status_code} | Response: {resp.text[:200]}"
                    )
                    
            except Exception as e:
                if attempt == self.TTS_RETRIES - 1:
                    Log.objects.create(
                        title="TTS generation failed",
                        type="error",
                        message=f"All {self.TTS_RETRIES} attempts failed - {str(e)}"
                    )
                else:
                    sleep(3 * (attempt + 1))
                    
        return None

    def detect_characters_in_scene(self, page_text):
        characters_present = []
        page_lower = page_text.lower()
        
        for char_key, char_data in self.character_references.items():
            char_name = char_data.get('name', '')
            if not char_name:
                continue
            
            name_lower = char_name.lower()
            
            if name_lower in page_lower:
                characters_present.append(char_key)
                continue
            
            name_parts = name_lower.split()
            if len(name_parts) > 1:
                if any(part in page_lower for part in name_parts if len(part) > 2):
                    characters_present.append(char_key)
        
        if not characters_present and self.character_references['main'].get('name'):
            characters_present = ['main']
        
        characters_present = [
            char for char in characters_present 
            if self.character_references.get(char, {}).get('image')
        ]
        
        return characters_present if characters_present else ['main']
    
    def _generate_page_content(self, page_num, page_text, voice_id, total_pages):
        characters_in_scene = self.detect_characters_in_scene(page_text)
        
        scene_desc = page_text[:350].replace('\n', ' ').strip()
        image_style = self.data['imagestyle']
        
        character_specs = []
        for idx, char_type in enumerate(characters_in_scene, 1):
            char_data = self.character_references.get(char_type, {})
            if char_data.get('name') and char_data.get('description'):
                role = char_data.get('role', 'character')
                character_specs.append(
                    f"CHARACTER #{idx} ({role.upper()}): {char_data['name']}\n"
                    f"Description: {char_data['description']}\n"
                    f"Reference: Image #{idx}"
                )
        
        char_details = "\n\n".join(character_specs) if character_specs else "Main character"
        
        image_prompt = (
            f"SCENE DESCRIPTION:\n{scene_desc}\n\n"
            f"ART STYLE: {image_style}\n\n"
            f"CHARACTERS IN THIS SCENE ({len(characters_in_scene)} total):\n{char_details}\n\n"
            f"MANDATORY CONSISTENCY REQUIREMENTS:\n"
            f"- Each character MUST match their reference image EXACTLY\n"
            f"- Facial features, hair, clothing, colors must be IDENTICAL to reference\n"
            f"- Characters should be instantly recognizable from references\n"
            f"- No alterations to character designs from references\n"
            f"- Maintain visual continuity with previous scenes\n\n"
            f"SCENE COMPOSITION:\n"
            f"- Position characters naturally based on story context\n"
            f"- Each character in dynamic pose relevant to scene action\n"
            f"- Appropriate background setting for the scene\n"
            f"- Vibrant colors, clear focus, engaging composition\n"
            f"- Professional children's book illustration quality\n\n"
            f"STRICT TEXT-FREE REQUIREMENT:\n"
            f"ABSOLUTELY NO text, words, letters, numbers, character names, labels, signs, "
            f"captions, speech bubbles, or any written content of any kind.\n"
            f"Pure visual storytelling only.\n\n"
            f"TECHNICAL SPECS:\n"
            f"- Full bleed illustration (no margins or borders)\n"
            f"- Clean composition suitable for children's book\n"
            f"- High contrast and clarity\n"
            f"- Consistent art style throughout\n\n"
            f"Generate the scene maintaining perfect character consistency with references."
        )

        image_file = self.generate_image_with_character_reference(image_prompt, characters_in_scene)
        audio_file = self.generate_tts(page_text, voice_id) if voice_id else None
        
        if not image_file:
            raise Exception(f"Page {page_num} image generation failed")
        
        image_file.seek(0)
        
        return (page_num, page_text, image_file, audio_file)
    

    def generate_character_reference(self, char_type='main', char_name='', char_desc=''):
        if char_type == 'main':
            char_name = self.input.get("character_name", "")
            char_desc = self.refined_character_desc or self.input.get("character_desc", "")
        
        imagestyle = self.data['imagestyle']
        childgroup = self.get_content(ChildAgeRange, self.input.get("childgroup_id"))
        
        prompt = (
            f"Create a REFERENCE CHARACTER DESIGN SHEET for {char_name}.\n\n"
            f"CHARACTER SPECIFICATIONS:\n{char_desc}\n\n"
            f"TARGET AGE GROUP: {childgroup}\n"
            f"CHARACTER AGE/SIZE: Match the age group - show appropriate child proportions if child\n\n"
            f"ART STYLE: {imagestyle}\n\n"
            f"STRICT REFERENCE REQUIREMENTS:\n"
            f"- Full body character in neutral T-pose or standing pose\n"
            f"- Character facing forward (front view) for maximum clarity\n"
            f"- Centered perfectly in frame, taking up 70-80% of image space\n"
            f"- ALL distinctive features clearly visible and well-lit\n"
            f"- Uniform lighting from front to show all details\n"
            f"- Plain solid color background (white, light gray, or soft gradient)\n"
            f"- NO scenery, props, objects, or decorative elements\n"
            f"- NO text, labels, names, or annotations anywhere\n"
            f"- Professional character turnaround/model sheet quality\n"
            f"- Crisp details, vibrant consistent colors\n"
            f"- Full bleed - character clearly visible edge to edge\n\n"
            f"FOCUS AREAS (ensure these are CRYSTAL CLEAR):\n"
            f"- Overall height and body proportions (HEAD TO FEET)\n"
            f"- Age-appropriate body structure\n"
            f"- Facial features (eyes, nose, mouth, expression)\n"
            f"- Hair style, color, and texture\n"
            f"- Body proportions and build\n"
            f"- Clothing colors, patterns, and style\n"
            f"- Any distinctive accessories or markings\n\n"
            f"This reference will be used for ALL future scenes. Maximum clarity and detail required."
        )
        
        image_file = self.generate_image_gemini(prompt)
        
        if image_file:
            try:
                image_file.seek(0)
                image_data = image_file.read()
                
                if not image_data or len(image_data) == 0:
                    Log.objects.create(
                        title=f"Reference {char_type} empty data",
                        type="error",
                        message=f"Image file contains no data"
                    )
                    return None
                
                self.character_references[char_type]['name'] = char_name
                self.character_references[char_type]['description'] = char_desc
                self.character_references[char_type]['age_group'] = childgroup
                self.character_references[char_type]['image'] = image_data
                
                images_dir = f'media/products/books/{self.current_book_id}/images'
                os.makedirs(images_dir, exist_ok=True)
                with open(f'{images_dir}/{char_type}_reference.png', 'wb') as f:
                    f.write(image_data)
                
                image_file = File(BytesIO(image_data), name=f"{char_type}_reference.png")
               
            except Exception as e:
                Log.objects.create(
                    title=f"Reference {char_type} storage failed",
                    type="error",
                    message=f"Error: {str(e)}"
                )
                return None
        
        return image_file


    def generate_cover_image(self, title, character_desc, imagestyle_content):
        title_clean = title.strip()
        title_display = ' '.join(title_clean.split())
        
        character_keys = [k for k in self.character_references.keys() 
                        if self.character_references[k].get('image')]
        
        if not character_keys:
            Log.objects.create(
                title="Cover generation failed",
                type="error",
                message=f"Cannot generate cover without references"
            )
            return None, None
        
        reference_images = []
        character_descriptions = []
        
        for idx, char_key in enumerate(character_keys, 1):
            char_data = self.character_references[char_key]
            
            if not char_data.get('image'):
                continue
                    
            reference_images.append(char_data['image'])
            role = char_data.get('role', 'character')
            character_descriptions.append(
                f"CHARACTER #{idx} - {char_data['name']} ({role}):\n{char_data['description']}"
            )
        
        if not reference_images:
            Log.objects.create(
                title="Cover generation failed",
                type="error",
                message=f"No valid image data found"
            )
            return None, None
        
        original_cover = None
        
        for attempt in range(self.IMAGE_RETRIES):
            try:
                model = genai.GenerativeModel(self.gemini_name or 'gemini-2.5-flash-image')
                
                pil_images = [Image.open(io.BytesIO(img_data)) for img_data in reference_images]
                
                char_list = "\n\n".join(character_descriptions)
                word_spelling = "\n".join([f"  * '{word}' = {'-'.join(word.upper())}" for word in title_display.split()])
                
                prompt = (
                        f"REFERENCE IMAGES PROVIDED: {len(reference_images)} character(s)\n\n"
                        f"CHARACTER CONSISTENCY:\n"
                        f"YOU MUST USE THESE EXACT CHARACTER DESIGNS:\n{char_list}\n"
                        f"- Each character MUST be IDENTICAL to their reference image\n"
                        f"- Match facial features, hair, clothing, colors, and proportions EXACTLY\n"
                        f"- Position all {len(reference_images)} characters together in engaging composition\n\n"
                        f"COVER DESIGN:\n"
                        f"- Vibrant children's book cover illustration\n"
                        f"- Art style: {imagestyle_content}\n"
                        f"- Pure illustration, NOT a physical book mockup or 3D render\n"
                        f"- Appropriate background scenery for the story theme\n\n"
                        f"LAYOUT & POSITIONING:\n"
                        f"- Full bleed background extending to all edges\n"
                        f"- Character(s) prominently featured in center-bottom area\n"
                        f"- Character(s) positioned with 10-15% margin from edges\n"
                        f"- Professional children's book cover illustration\n\n"
                        f"TITLE TEXT SPELLING (CRITICAL):\n"
                        f"The exact title to display is: {title_display}\n\n"
                        f"SPELL EACH WORD LETTER-BY-LETTER:\n"
                        f"{word_spelling}\n\n"
                        f"SPELLING RULES:\n"
                        f"- Copy each letter EXACTLY as shown above\n"
                        f"- DO NOT modify, skip, add, or rearrange any letters\n"
                        f"- Match the letter count exactly for each word\n\n"
                        f"TITLE DISPLAY REQUIREMENTS:\n"
                        f"- Display \"{title_display}\" at CENTER TOP\n"
                        f"- LARGE, BOLD, COLORFUL, CHILD-FRIENDLY letters\n"
                        f"- Centered with 15-20% margin from edges (within central 60-70% width)\n"
                        f"- Clearly visible and readable\n"
                        f"- NO other text besides the title\n\n"
                        f"Generate a stunning children's book cover with perfect character consistency and correct title spelling."
                    )
                
                content = pil_images + [prompt]
                response = model.generate_content(content)
                self.usage_tracker.add_gemini_usage(response)
                
                if not response or not response.parts:
                    continue
                
                image_part = None
                for part in response.parts:
                    if hasattr(part, 'inline_data') and part.inline_data:
                        image_part = part
                        break
                
                if not image_part:
                    continue
                
                data = image_part.inline_data.data
                original_cover = File(BytesIO(data), name="cover_original.png")
                
                break
                        
            except Exception as e:
                error_msg = str(e).lower()
                
                if "safety" not in error_msg and "policy" not in error_msg and "blocked" not in error_msg:
                    if attempt == self.IMAGE_RETRIES - 1:
                        Log.objects.create(
                            title="Cover generation error",
                            type="error",
                            message=f"All attempts failed: {str(e)}"
                        )
        
        if not original_cover:
            Log.objects.create(
                title="Cover generation failed after retries",
                type="error",
                message=f"Failed after {self.IMAGE_RETRIES} attempts"
            )
            return None, None

        original_cover.seek(0)
        cover_content = original_cover.read()

        cover_for_cropping = File(BytesIO(cover_content), name="cover_original.png")
        cropped_cover = self.resize_cover_image(cover_for_cropping)

        if cropped_cover:
            cropped_cover.seek(0)

        original_cover = File(BytesIO(cover_content), name="cover_original.png")

        return original_cover, cropped_cover


    def save_book(self, story_text=None, title=None):
        if not story_text:
            title, story_text = self.generate_story()
            if not story_text:
                Log.objects.create(
                    title="Book generation aborted",
                    type="error",
                    message="Story generation failed"
                )
                return None
        
        supporting_characters = self.extract_characters_from_story(story_text)
        description = self.generate_book_description(title, story_text)
        pages_text = self.divide_pages(story_text)
        
        if not pages_text:
            Log.objects.create(
                title="Book generation aborted",
                type="error",
                message=f"Story division failed"
            )
            return None
        
        slug = self.generate_unique_slug(title)
        
        book = ProductBook.objects.create(
            title=title,
            description=description,
            slug=slug,
            prompt=self.build_prompt(),
            status="pending",
            char_name=self.input.get("character_name", ""),
            char_desc=self.refined_character_desc or self.input.get("character_desc", ""),
            agegroup_id=self.input.get("childgroup_id"),
            setting_id=self.input.get("setting_id"),
            plot_id=self.input.get("plot_id"),
            theme_id=self.input.get("theme_id"),
            tone_id=self.input.get("tone_id"),
            length_id=self.input.get("storylength_id"),
            imagestyle_id=self.input.get("imagestyle_id"),
            language_id=self.input.get("language_id"),
            narrator_id=self.input.get("narrator_id") or None,
            tokens=self.usage_tracker.get_totals() + 1
        )

        self.current_book_id = book.pk
        os.makedirs(f'media/products/books/{book.pk}/images', exist_ok=True)

        voice_id = self.data.get('voice_id')
        total_pages = len(pages_text)

        try:
            main_char_result = self.generate_character_reference('main')
            
            if not main_char_result:
                main_char_result = self.generate_character_reference('main')
            
            if not main_char_result:
                Log.objects.create(
                    title="Main character reference failed",
                    type="error",
                    message=f"Cannot proceed without main character"
                )
                book.status = "failed"
                book.save()
                return None
            
            if not self.character_references.get('main', {}).get('image'):
                Log.objects.create(
                    title="Main reference not stored",
                    type="error",
                    message="Reference generated but not in memory"
                )
                book.status = "failed"
                book.save()
                return None
            
            char_keys = [k for k in self.character_references.keys() if k != 'main']
            for idx, char_key in enumerate(char_keys):
                if idx < len(supporting_characters):
                    sub_char = supporting_characters[idx]
                    refined_desc = self.refine_character_description(
                        sub_char['name'], 
                        sub_char['description'], 
                        char_key
                    )
                    
                    sub_result = self.generate_character_reference(
                        char_key, 
                        sub_char['name'], 
                        refined_desc
                    )
            
            original_cover, cropped_cover = self.generate_cover_image(
                title,
                self.refined_character_desc or self.input.get("character_desc", ""),
                self.data['imagestyle']
            )
            
            with ThreadPoolExecutor(self.MAX_WORKERS) as executor:
                page_futures = {}
                for i, text in enumerate(pages_text, start=1):
                    future = executor.submit(self._generate_page_content, i, text, voice_id, total_pages)
                    page_futures[future] = i
                
                page_results = {}
                failed_pages = []
                
                for future in as_completed(page_futures):
                    page_num = page_futures[future]
                    try:
                        page_num, page_text, image_file, audio_file = future.result()
                        page_results[page_num] = (page_text, image_file, audio_file)
                    except Exception as e:
                        failed_pages.append(page_num)
                
                if failed_pages:
                    for page_num in failed_pages:
                        if self.IMAGE_RETRIES > 1:
                            for retry in range(self.IMAGE_RETRIES - 1):
                                try:
                                    page_text = pages_text[page_num - 1]
                                    result = self._generate_page_content(page_num, page_text, voice_id, total_pages)
                                    page_results[result[0]] = (result[1], result[2], result[3])
                                    break
                                except Exception as e:
                                    if retry == self.IMAGE_RETRIES - 2:
                                        Log.objects.create(
                                            title=f"Page {page_num} failed after retries",
                                            type="error",
                                            message=f"Page {page_num} could not be generated after {self.IMAGE_RETRIES - 1} retries"
                                        )
                        else:
                            Log.objects.create(
                                title=f"Page {page_num} failed",
                                type="error",
                                message=f"Page {page_num} could not be generated"
                            )
            
            if original_cover:
                filename = f"original_cover.png"
                book.char_img.save(filename, original_cover, save=False)
            
            if cropped_cover:
                filename = f"cropped_cover.png"
                book.image.save(filename, cropped_cover, save=False)
            
            book.save()

            pages_to_create = []
            for i in sorted(page_results.keys()):
                page_text, image_file, audio_file = page_results[i]
                pages_to_create.append(ProductBookPage(
                    book=book,
                    page=i,
                    text=page_text,
                    image=image_file,
                    audio=audio_file
                ))
            
            if pages_to_create:
                with transaction.atomic():
                    ProductBookPage.objects.bulk_create(pages_to_create)

            book.status = "completed"
            book.save()
            
            book.refresh_from_db()
            
            return book
            
        except Exception as e:
            book.status = "failed"
            book.save()
            Log.objects.create(
                title="ProductBook generation failed", 
                type="error", 
                message=f"Error generating book {book.id}: {str(e)}"
            )
            raise