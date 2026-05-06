from django.db import models
import os
from storybook.utils.models import DefaultFields
from django.contrib.auth import get_user_model
from io import BytesIO
from django.core.files.base import ContentFile
from PIL import Image as PILImage


User = get_user_model()

# Create your models here.

MODEL_TYPE_CHOICES = [
    ("text", "Text Generation"),
    ("image", "Image Generation"),
    ("tts", "Text to Speech"),
    ("embedding", "Embeddings"),
    ("stt", "Speech to Text"),
    ("moderation", "Content Moderation"),
    ("other", "Other"),
]

class AIModel(DefaultFields):
    name = models.CharField(max_length=150, unique=True, help_text="Exact model name, e.g. gpt-4o")
    emoji = models.CharField(max_length=10, blank=True, null=True,help_text="Optional: Add an emoji to represent AI model (e.g., 📚, 🐱, 🎉)")
    alias = models.CharField(max_length=100, blank=True, null=True, help_text="Friendly name, e.g. Story Writer")
    type = models.CharField(max_length=50, choices=MODEL_TYPE_CHOICES, help_text="Type of AI model")
    family = models.CharField(max_length=50, default="openai", help_text="Model provider, e.g. OpenAI")
    apikey = models.CharField(max_length=255, blank=True, null=True, help_text="Custom API key if different from default")
    temperature = models.FloatField(default=0.7, help_text="Controls randomness in responses (0–1)")
    endpoint = models.CharField(max_length=255, blank=True, null=True, help_text="API endpoint or URL to call this model")
    parameters = models.JSONField(blank=True, null=True, help_text="Additional configuration options")

    class Meta:
        db_table = "ai_models"
        ordering = ["family", "type"]

    def __str__(self):
        return str(self.alias or self.name)



def upload_child_age_icon(instance, filename):
    base, ext = os.path.splitext(filename)
    folder = f"stories/agerange/{instance.id or 'temp'}"
    return f"{folder}/icon{ext}"


class ChildAgeRange(DefaultFields):
    name = models.CharField(max_length=50, help_text="Example: 3–5", blank=True, null=True)
    emoji = models.CharField(max_length=10, blank=True, null=True,help_text="Optional: Add an emoji to represent age group (e.g., 📚, 🐱, 🎉)")
    icon = models.ImageField(upload_to=upload_child_age_icon, blank=True, null=True, help_text="Upload icon image")
    content = models.TextField(blank=True, help_text="Description or notes for this age range")
    cost = models.PositiveIntegerField(default=0, help_text="Token cost for selecting this option")

    class Meta:
        db_table = "child_age_ranges"

    def __str__(self):
        return str(self.name)

    def save(self, *args, **kwargs):
        if self.pk is None:
            saved_icon = self.icon
            self.icon = None
            super().save(*args, **kwargs)
            self.icon = saved_icon
            if saved_icon:
                super().save(update_fields=['icon'])
        else:
            super().save(*args, **kwargs)


def upload_story_setting_icon(instance, filename):
    base, ext = os.path.splitext(filename)
    folder = f"stories/setting/{instance.id or 'temp'}"
    return f"{folder}/icon{ext}"


class StorySetting(DefaultFields):
    name = models.CharField(max_length=100, help_text="Example: Fairy tale, Outer space, Enchanted forest")
    emoji = models.CharField(max_length=10, blank=True, null=True,help_text="Optional: Add an emoji to represent story setting (e.g., 📚, 🐱, 🎉)")
    icon = models.ImageField(upload_to=upload_story_setting_icon, blank=True, null=True, help_text="Upload icon image")
    content = models.TextField(blank=True, help_text="Optional description of this setting")
    cost = models.PositiveIntegerField(default=0, help_text="Token cost for selecting this setting")

    class Meta:
        db_table = "story_settings"

    def __str__(self):
        return str(self.name)

    def save(self, *args, **kwargs):
        if self.pk is None:
            saved_icon = self.icon
            self.icon = None
            super().save(*args, **kwargs)
            self.icon = saved_icon
            if saved_icon:
                super().save(update_fields=['icon'])
        else:
            super().save(*args, **kwargs)


def upload_story_plot_icon(instance, filename):
    base, ext = os.path.splitext(filename)
    folder = f"stories/plot/{instance.id or 'temp'}"
    return f"{folder}/icon{ext}"


class StoryPlot(DefaultFields):
    name = models.CharField(max_length=100, help_text="Example: Silly Adventure, Magical Find, Epic Race")
    emoji = models.CharField(max_length=10, blank=True, null=True,help_text="Optional: Add an emoji to represent story plot (e.g., 📚, 🐱, 🎉)")
    icon = models.ImageField(upload_to=upload_story_plot_icon, blank=True, null=True, help_text="Upload icon for this plot")
    content = models.TextField(blank=True, help_text="Optional description of this plot type")
    cost = models.PositiveIntegerField(default=0, help_text="Token cost for selecting this plot")

    class Meta:
        db_table = "story_plots"

    def __str__(self):
        return str(self.name)

    def save(self, *args, **kwargs):
        if self.pk is None:
            saved_icon = self.icon
            self.icon = None
            super().save(*args, **kwargs)
            self.icon = saved_icon
            if saved_icon:
                super().save(update_fields=['icon'])
        else:
            super().save(*args, **kwargs)


def upload_story_theme_icon(instance, filename):
    base, ext = os.path.splitext(filename)
    folder = f"stories/theme/{instance.id or 'temp'}"
    return f"{folder}/icon{ext}"


class StoryTheme(DefaultFields):
    name = models.CharField(max_length=100, help_text="Example: Funny, Heroes, Space, Animals, Magic")
    emoji = models.CharField(max_length=10, blank=True, null=True,help_text="Optional: Add an emoji to represent story theme (e.g., 📚, 🐱, 🎉)")
    icon = models.ImageField(upload_to=upload_story_theme_icon, blank=True, null=True, help_text="Upload icon image for this theme")
    content = models.TextField(blank=True, help_text="Optional description for this theme")
    cost = models.PositiveIntegerField(default=0, help_text="Token cost for selecting this theme")

    class Meta:
        db_table = "story_themes"

    def __str__(self):
        return str(self.name)

    def save(self, *args, **kwargs):
        if self.pk is None:
            saved_icon = self.icon
            self.icon = None
            super().save(*args, **kwargs)
            self.icon = saved_icon
            if saved_icon:
                super().save(update_fields=['icon'])
        else:
            super().save(*args, **kwargs)


def upload_story_tone_icon(instance, filename):
    base, ext = os.path.splitext(filename)
    folder = f"stories/tone/{instance.id or 'temp'}"
    return f"{folder}/icon{ext}"


class StoryTone(DefaultFields):
    name = models.CharField(max_length=100, help_text="Example: Playful, Heartwarming, Happy, Exciting")
    emoji = models.CharField(max_length=10, blank=True, null=True,help_text="Optional: Add an emoji to represent story tone (e.g., 📚, 🐱, 🎉)")
    icon = models.ImageField(upload_to=upload_story_tone_icon, blank=True, null=True, help_text="Upload icon image for this tone")
    content = models.TextField(blank=True, help_text="Optional description for this tone")
    cost = models.PositiveIntegerField(default=0, help_text="Token cost for selecting this tone")

    class Meta:
        db_table = "story_tones"

    def __str__(self):
        return str(self.name)

    def save(self, *args, **kwargs):
        if self.pk is None:
            saved_icon = self.icon
            self.icon = None
            super().save(*args, **kwargs)
            self.icon = saved_icon
            if saved_icon:
                super().save(update_fields=['icon'])
        else:
            super().save(*args, **kwargs)

def upload_story_length_icon(instance, filename):
    base, ext = os.path.splitext(filename)
    folder = f"stories/length/{instance.id or 'temp'}"
    return f"{folder}/icon{ext}"

class StoryLength(DefaultFields):
    name = models.CharField(max_length=100, help_text="Example: Short, Medium, Long")
    min = models.PositiveIntegerField(default=1, help_text="Minimum number of pages for this story length")
    max = models.PositiveIntegerField(default=10, help_text="Maximum number of pages for this story length")
    emoji = models.CharField(max_length=10, blank=True, null=True,help_text="Optional: Add an emoji to represent story length (e.g., 📚, 🐱, 🎉)")
    icon = models.ImageField(upload_to=upload_story_length_icon, blank=True, null=True, help_text="Upload icon image for this story length")
    content = models.TextField(blank=True, help_text="Optional description for this story length")
    cost = models.PositiveIntegerField(default=0, help_text="Token cost for selecting this story length")

    class Meta:
        db_table = "story_lengths"

    def __str__(self):
        return str(self.name)

    def save(self, *args, **kwargs):
        if not self.pk:
            saved_icon = self.icon
            self.icon = None
            super().save(*args, **kwargs)
            self.icon = saved_icon
            if saved_icon:
                super().save(update_fields=['icon'])
        else:
            super().save(*args, **kwargs)



def upload_image_style_icon(instance, filename):
    base, ext = os.path.splitext(filename)
    folder = f"stories/imagestyle/{instance.id or 'temp'}"
    return f"{folder}/image{ext}"


class ImageStyle(DefaultFields):
    name = models.CharField(max_length=100, help_text="Example: Cartoon, Watercolor, 3D, Pencil Sketch")
    image = models.ImageField(upload_to=upload_image_style_icon, blank=True, null=True, help_text="Upload image for this image style")
    emoji = models.CharField(max_length=10, blank=True, null=True,help_text="Optional: Add an emoji to represent story image style (e.g., 📚, 🐱, 🎉)")
    content = models.TextField(blank=True, help_text="Optional description of this image style")
    cost = models.PositiveIntegerField(default=0, help_text="Token cost for selecting this image style")

    class Meta:
        db_table = "image_styles"

    def __str__(self):
        return str(self.name)

    def save(self, *args, **kwargs):
        if self.pk is None:
            saved_image = self.image
            self.image = None
            super().save(*args, **kwargs)
            self.image = saved_image
            if saved_image:
                super().save(update_fields=['image'])
        else:
            super().save(*args, **kwargs)


def upload_language_icon(instance, filename):
    base, ext = os.path.splitext(filename)
    folder = f"stories/language/{instance.id or 'temp'}"
    return f"{folder}/icon{ext}"


class LanguageOption(DefaultFields):
    name = models.CharField(max_length=100, help_text="Example: English, Marathi, Hindi, Spanish")
    code = models.CharField(max_length=10, unique=True, help_text="Language code, e.g., en, mr, hi, es")
    emoji = models.CharField(max_length=10, blank=True, null=True,help_text="Optional: Add an emoji to represent outout language (e.g., 📚, 🐱, 🎉)")
    icon = models.ImageField(upload_to=upload_language_icon, blank=True, null=True, help_text="Upload flag or language icon")
    content = models.TextField(blank=True, help_text="Optional description about this language option")
    cost = models.PositiveIntegerField(default=0, help_text="Token cost for selecting this language")

    class Meta:
        db_table = "story_languages"

    def __str__(self):
        return str(self.name)

    def save(self, *args, **kwargs):
        if self.pk is None:
            saved_icon = self.icon
            self.icon = None
            super().save(*args, **kwargs)
            self.icon = saved_icon
            if saved_icon:
                super().save(update_fields=['icon'])
        else:
            super().save(*args, **kwargs)


def upload_narrator_voice_icon(instance, filename):
    base, ext = os.path.splitext(filename)
    folder = f"stories/narrators/{instance.id or 'temp'}"
    return f"{folder}/icon{ext}"


def upload_narrator_voice_audio(instance, filename):
    base, ext = os.path.splitext(filename)
    folder = f"stories/upload/narrators/{instance.id or 'temp'}"
    return f"{folder}/voice_sample{ext}"


class NarratorVoice(DefaultFields):
    name = models.CharField(max_length=100, help_text="Voice name, e.g. Warm Male, Friendly Female")
    emoji = models.CharField(max_length=10, blank=True, null=True,help_text="Optional: Add an emoji to represent story narrator (e.g., 📚, 🐱, 🎉)")
    icon = models.ImageField(upload_to=upload_narrator_voice_icon, blank=True, null=True, help_text="Upload icon image")
    upload = models.FileField(upload_to=upload_narrator_voice_audio, blank=True, null=True, help_text="Upload sample audio (MP3/WAV)")
    model = models.ForeignKey(AIModel, on_delete=models.SET_NULL, null=True, blank=True, related_name="narrator_voices", help_text="Default TTS model")
    vid = models.CharField(max_length=100, blank=True, null=True, help_text="Provider-specific voice ID (e.g., EXAVITQu4vr4xnSDxMaL)")
    gender = models.CharField(max_length=20, blank=True, null=True, help_text="Voice gender if available")
    voice = models.URLField(blank=True, null=True, help_text="Preview audio URL from the provider")
    cost = models.PositiveIntegerField(default=0, help_text="Token cost for selecting this voice")

    class Meta:
        db_table = "narrator_voices"
        unique_together = ("vid", "model")


    def __str__(self):
        return str(self.name)

    def save(self, *args, **kwargs):
        if self.pk is None and (self.icon or self.upload):
            saved_icon = self.icon
            saved_upload = self.upload
            self.icon = None
            self.upload = None
            super().save(*args, **kwargs)
            self.icon = saved_icon
            self.upload = saved_upload
            update_fields = []
            if saved_icon:
                update_fields.append('icon')
            if saved_upload:
                update_fields.append('upload')
            if update_fields:
                super().save(update_fields=update_fields)
        else:
            super().save(*args, **kwargs)


STORY_END_TYPE_CHOICES = [

    ("happy", "😊 Happy Ending"),
    ("moral", "🌟 Moral Lesson"),
    ("twist", "😲 Surprise Twist"),
    ("sad", "😢 Sad Ending"),
    ("hopeful", "🌈 Hopeful Ending"),
    ("funny", "😂 Funny Ending"),
    ("magical", "✨ Magical Ending"),
    ("tragic", "💔 Tragic Ending"),
    ("cliffhanger", "🚪 Cliffhanger"),
    ("mystery", "🕵️‍♂️ Mysterious Ending"),
]

class StoryEnd(DefaultFields):
    name = models.CharField( max_length=50, choices=STORY_END_TYPE_CHOICES, help_text="Select or type how the story should end.")
    icon = models.CharField(max_length=10, blank=True, help_text="Optional emoji or icon for this ending type (e.g. 😊, 🌟, 😲).")
    context = models.TextField(blank=True, help_text="Optional short description or example for this ending type.")

    class Meta:
        db_table = "story_ends"

    def __str__(self):
        icon = f" {self.icon}" if self.icon else ""
        return f"{self.name}{icon}"
    


def storybook_cover_upload_path(instance, filename):
    ext = os.path.splitext(filename)[1]
    folder = instance.pk or 'temp'
    return f"stories/books/{folder}/cover{ext}"


def storybook_pdf_upload_path(instance, filename):
    ext = os.path.splitext(filename)[1]
    folder = instance.pk or 'temp'
    return f"stories/books/{folder}/storybook{ext}"


def storybook_page_image_upload_path(instance, filename):
    ext = os.path.splitext(filename)[1]
    folder = instance.book.pk or 'temp'
    return f"stories/books/{folder}/pages/{instance.page}/image{ext}"


def storybook_character_image_upload_path(instance, filename):
    return f"stories/books/{instance.pk or 'temp'}/images/{filename}"


def storybook_page_audio_upload_path(instance, filename):
    ext = os.path.splitext(filename)[1]
    folder = instance.book.pk or 'temp'
    return f"stories/books/{folder}/pages/{instance.page}/audio{ext}"


def storybook_thumbnail_upload_path(instance, filename):
    return f"stories/books/{instance.pk or 'temp'}/thumbnails/{filename}"


class StoryBook(DefaultFields):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_books", help_text="Owner of this Story Book.")
    slug = models.SlugField(max_length=220, null=True, blank=True, help_text="URL-friendly identifier for the Story Book.")
    title = models.CharField(max_length=200, help_text="Enter the title of the Story Book.")
    description = models.TextField(blank=True, help_text="Optional description of the Story Book.")
    char_name = models.CharField(max_length=100, blank=True, null=True, help_text="Main character's name.")
    char_desc = models.TextField(blank=True, null=True, help_text="Description of the main character.")
    char_img = models.ImageField(upload_to=storybook_character_image_upload_path, blank=True, null=True, help_text="Reference image of the main character.")
    prompt = models.TextField(blank=True, null=True, help_text="Optional prompt used to generate the Story Book.")
    agegroup = models.ForeignKey(ChildAgeRange, on_delete=models.SET_NULL, null=True, blank=True, help_text="Target age group for the Story Book.")
    setting = models.ForeignKey(StorySetting, on_delete=models.SET_NULL, null=True, blank=True, help_text="Main setting of the Story Book.")
    plot = models.ForeignKey(StoryPlot, on_delete=models.SET_NULL, null=True, blank=True, help_text="Story plot type.")
    theme = models.ForeignKey(StoryTheme, on_delete=models.SET_NULL, null=True, blank=True, help_text="Story theme.")
    tone = models.ForeignKey(StoryTone, on_delete=models.SET_NULL, null=True, blank=True, help_text="Story tone or mood.")
    length = models.ForeignKey(StoryLength, on_delete=models.SET_NULL, null=True, blank=True, help_text="Approximate length of the Story Book.")
    imagestyle = models.ForeignKey(ImageStyle, on_delete=models.SET_NULL, null=True, blank=True, help_text="Preferred illustration style.")
    language = models.ForeignKey(LanguageOption, on_delete=models.SET_NULL, null=True, blank=True, help_text="Language of the Story Book.")
    narrator = models.ForeignKey(NarratorVoice, on_delete=models.SET_NULL, null=True, blank=True, help_text="Narrator voice for audio generation.")
    image = models.ImageField(upload_to=storybook_cover_upload_path, blank=True, null=True, help_text="Cover image of the Story Book.")
    thumbnail = models.ImageField(upload_to=storybook_thumbnail_upload_path, blank=True, null=True, help_text="Auto-generated compressed thumbnail from cover image.")
    pdf = models.FileField(upload_to=storybook_pdf_upload_path, blank=True, null=True, help_text="Optional PDF version of the Story Book.")
    storyend = models.TextField(blank=True, null=True, help_text="Optional text describing how the story should end.")
    tokens = models.PositiveIntegerField(default=0, help_text="Number of tokens used to create this Story Book.")
    status = models.CharField(max_length=20, choices=[("pending", "Pending"), ("completed", "Completed"), ("failed", "Failed")], default="pending", help_text="Current generation status of the Story Book.")

    class Meta:
        db_table = "story_books"
        indexes = [
            models.Index(fields=['user', 'is_active', 'status', '-created_at'], name='user_active_status_created_idx'),
            models.Index(fields=['user', 'is_active', 'status', 'tokens', 'id'], name='user_active_status_tokens_idx'),
            models.Index(fields=['user', 'is_active', 'status', '-tokens', 'id'], name='user_active_tokens_desc_idx'),
            models.Index(fields=['user', 'is_active', 'status', '-created_at', 'id'], name='user_active_created_id_idx'),
            models.Index(fields=['user', 'status'], name='user_status_idx'),
            models.Index(fields=['status'], name='story_status_idx'),
            models.Index(fields=['title'], name='story_title_idx'),
            models.Index(fields=['slug'], name='story_slug_idx'),
            models.Index(fields=['user', 'agegroup', 'is_active', 'status'], name='user_agegroup_active_idx'),
            models.Index(fields=['user', 'plot', 'is_active', 'status'], name='user_plot_active_idx'),
            models.Index(fields=['user', 'theme', 'is_active', 'status'], name='user_theme_active_idx'),
            models.Index(fields=['user', 'narrator', 'is_active', 'status'], name='user_narrator_active_idx'),
            models.Index(fields=['user', 'imagestyle', 'is_active', 'status'], name='user_imagestyle_active_idx'),
        ]

    def __str__(self):
        return str(self.title)
    
    def save(self, *args, **kwargs):
        if self.pk is None:
            saved_image = self.image
            self.image = None
            self.thumbnail = None
            super().save(*args, **kwargs)
            self.image = saved_image
            if saved_image:
                self._generate_thumbnail()
                super().save(update_fields=['image', 'thumbnail'])
        else:
            if self.image and not self.thumbnail:
                self._generate_thumbnail()
            super().save(*args, **kwargs)

    def _generate_thumbnail(self):
        self.image.seek(0)
        img = PILImage.open(self.image)
        img.thumbnail((300, 400), PILImage.LANCZOS)
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        buffer = BytesIO()
        img.save(buffer, format="WEBP", quality=75, optimize=True)
        buffer.seek(0)
        filename = f"thumb_{self.image.name.split('/')[-1].rsplit('.', 1)[0]}.webp"
        self.thumbnail.save(filename, ContentFile(buffer.read()), save=False)


class StoryBookPage(DefaultFields):
    book = models.ForeignKey(StoryBook, on_delete=models.CASCADE, related_name="pages", help_text="The Story Book this page belongs to.")
    prompt = models.TextField(blank=True, null=True, help_text="Prompt used for generating the image of this page.")
    page = models.PositiveIntegerField(help_text="Page number within the Story Book.")
    text = models.TextField(help_text="Text content of this page.")
    image = models.ImageField(upload_to=storybook_page_image_upload_path, blank=True, null=True, help_text="Optional illustration image for this page.")
    audio = models.FileField(upload_to=storybook_page_audio_upload_path, blank=True, null=True, help_text="Optional audio narration file for this page.")

    class Meta:
        db_table = "story_book_pages"
        ordering = ["page"]
        unique_together = ("book", "page")
        indexes = [
            models.Index(fields=['book', 'page'], name='story_book_page_idx'),
            models.Index(fields=['book', 'image'], name='story_book_image_idx'),
        ]

    def __str__(self):
        return f"{self.book.title} - Page {self.page}"