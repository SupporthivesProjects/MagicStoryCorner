from django.db import models
from django.contrib.auth import get_user_model
from stories.models import StoryBook  
from storybook.utils.models import DefaultFields
from stories.models import ChildAgeRange, StorySetting, StoryPlot, StoryTheme, StoryTone, ImageStyle, LanguageOption, NarratorVoice, StoryLength
import os
from io import BytesIO
from django.core.files.base import ContentFile
from PIL import Image as PILImage

User = get_user_model()

def productbook_image_upload_path(instance, filename):
    return f"products/books/{instance.pk or 'temp'}/images/{filename}"


def productbook_pdf_upload_path(instance, filename):
    return f"products/books/{instance.pk or 'temp'}/pdf/{filename}"


def productbook_page_image_upload_path(instance, filename):
    ext = os.path.splitext(filename)[1]
    folder = instance.book.pk or 'temp'
    return f"products/books/{folder}/pages/{instance.page}/image{ext}"


def productbook_page_audio_upload_path(instance, filename):
    ext = os.path.splitext(filename)[1]
    folder = instance.book.pk or 'temp'
    return f"products/books/{folder}/pages/{instance.page}/audio{ext}"

def productbook_character_image_upload_path(instance, filename):
    return f"products/books/{instance.pk or 'temp'}/images/{filename}"

def productbook_thumbnail_upload_path(instance, filename):
    return f"products/books/{instance.pk or 'temp'}/thumbnails/{filename}"


class ProductBook(DefaultFields):
    title = models.CharField(max_length=200, help_text="Title of the Product Book.")
    slug = models.SlugField(max_length=220, null=True, blank=True, help_text="URL-friendly slug for the Product Book.")
    description = models.TextField(blank=True, help_text="Short description of the Product Book.")
    char_name = models.CharField(max_length=100, blank=True, null=True, help_text="Main character's name.")
    char_desc = models.TextField(blank=True, null=True, help_text="Description of the main character.")
    char_img = models.ImageField(upload_to=productbook_character_image_upload_path, blank=True, null=True, help_text="Reference image of the main character.")
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Price of the Product Book.")
    currency = models.CharField(max_length=5, default="$", help_text="Currency symbol used for pricing.")
    prompt = models.TextField(blank=True, null=True, help_text="Prompt used for generating the Product Book.")
    agegroup = models.ForeignKey(ChildAgeRange, on_delete=models.SET_NULL, null=True, blank=True, help_text="Target age group.")
    setting = models.ForeignKey(StorySetting, on_delete=models.SET_NULL, null=True, blank=True, help_text="Main setting of the story.")
    plot = models.ForeignKey(StoryPlot, on_delete=models.SET_NULL, null=True, blank=True, help_text="Plot type of the story.")
    theme = models.ForeignKey(StoryTheme, on_delete=models.SET_NULL, null=True, blank=True, help_text="Theme of the story.")
    tone = models.ForeignKey(StoryTone, on_delete=models.SET_NULL, null=True, blank=True, help_text="Tone or mood of the story.")
    length = models.ForeignKey(StoryLength, on_delete=models.SET_NULL, null=True, blank=True, help_text="Approximate story length.")
    imagestyle = models.ForeignKey(ImageStyle, on_delete=models.SET_NULL, null=True, blank=True, help_text="Preferred illustration style.")
    language = models.ForeignKey(LanguageOption, on_delete=models.SET_NULL, null=True, blank=True, help_text="Language of the story.")
    narrator = models.ForeignKey(NarratorVoice, on_delete=models.SET_NULL, null=True, blank=True, help_text="Narrator voice for audio playback.")
    image = models.ImageField(upload_to=productbook_image_upload_path, blank=True, null=True, help_text="Cover image of the Product Book.")
    thumbnail = models.ImageField(upload_to=productbook_thumbnail_upload_path, blank=True, null=True, help_text="Auto-generated compressed thumbnail from cover image.")
    pdf = models.FileField(upload_to=productbook_pdf_upload_path, blank=True, null=True, help_text="PDF version of the Product Book.")
    storyend = models.TextField(blank=True, null=True, help_text="Optional custom ending for the story.")
    tokens = models.PositiveIntegerField(default=0, help_text="Tokens required to unlock this Product Book.")
    status = models.CharField(max_length=20, choices=[("pending", "Pending"), ("completed", "Completed"), ("failed", "Failed")], default="pending", help_text="Book generation status.")

    class Meta:
        db_table = "product_books"
        indexes = [
            models.Index(fields=['is_active', 'status', '-created_at'], name='active_status_created_idx'),
            models.Index(fields=['is_active', 'status', 'tokens', 'id'], name='active_status_tokens_idx'),
            models.Index(fields=['is_active', 'status', '-tokens', 'id'], name='active_status_tokens_desc_idx'),
            models.Index(fields=['is_active', 'status', '-created_at', 'id'], name='active_status_created_id_idx'),
            models.Index(fields=['status'], name='status_idx'),
            models.Index(fields=['title'], name='title_idx'),
            models.Index(fields=['agegroup', 'is_active', 'status'], name='agegroup_active_status_idx'),
            models.Index(fields=['plot', 'is_active', 'status'], name='plot_active_status_idx'),
            models.Index(fields=['theme', 'is_active', 'status'], name='theme_active_status_idx'),
            models.Index(fields=['narrator', 'is_active', 'status'], name='narrator_active_status_idx'),
            models.Index(fields=['imagestyle', 'is_active', 'status'], name='imagestyle_active_status_idx'),
        ]

    def __str__(self):
        return self.title
    
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


class ProductBookPage(DefaultFields):
    book = models.ForeignKey(ProductBook, on_delete=models.CASCADE, related_name="pages", help_text="Product Book this page belongs to.")
    prompt = models.TextField(blank=True, null=True, help_text="Prompt used for generating the image of this page.")
    page = models.PositiveIntegerField(help_text="Page number inside the Product Book.")
    text = models.TextField(help_text="Text content of the page.")
    image = models.ImageField(upload_to=productbook_page_image_upload_path, blank=True, null=True, help_text="Optional image for this page.")
    audio = models.FileField(upload_to=productbook_page_audio_upload_path, blank=True, null=True, help_text="Optional audio narration for this page.")

    class Meta:
        db_table = "product_book_pages"
        ordering = ["page"]
        unique_together = ("book", "page")
        indexes = [
            models.Index(fields=['book', 'page'], name='book_page_idx'),
            models.Index(fields=['book', 'image'], name='book_image_idx'),
        ]

    def __str__(self):
        return f"{self.book.title} - Page {self.page}"


class ProductBookPurchase(DefaultFields):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="purchased_productbooks")
    book = models.ForeignKey(ProductBook, on_delete=models.CASCADE, related_name="purchases")

    class Meta:
        db_table = "product_book_purchases"
        unique_together = ("user", "book")

    def __str__(self):
        return f"{self.user.username} purchased {self.book.title}"
    

class Configuration(DefaultFields):
    CONFIG_TYPES = (
        ("admin", "Admin"),
        ("user", "User"),
    )
    type = models.CharField( max_length=20, choices=CONFIG_TYPES, default="admin",help_text="Configuration for admin or user side.")
    chars_per_page = models.IntegerField(default=400, help_text="Characters allowed per page.")
    max_pages = models.IntegerField(default=25, help_text="Maximum story pages.")
    img_retries = models.IntegerField(default=3, help_text="Image generation retry count.")
    tts_retries = models.IntegerField(default=3, help_text="TTS retry count.")
    workers = models.IntegerField(default=10, help_text="Number of parallel workers.")
    consistency_checks = models.IntegerField(default=3, help_text="How many characters (main + side) must stay visually consistent.")
    story_retries = models.IntegerField(default=3, help_text="Story generation retry attempts.")
    min_story_len = models.IntegerField(default=75, help_text="Minimum percentage of required story length before retry.")

    class Meta:
        verbose_name = "Configuration"
        verbose_name_plural = "Configurations"
