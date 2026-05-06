import logging
from stories.models import (
    ChildAgeRange, StorySetting, StoryPlot, StoryTheme, StoryTone,
    StoryLength, ImageStyle, LanguageOption, NarratorVoice, AIModel
)
import re
logger = logging.getLogger(__name__)


class StoryContext:
    def __init__(self, **kwargs):
        self.character_name = kwargs.get("character_name", "Hero")
        self.character_desc = kwargs.get("character_desc", "brave and clever")
        self.agegroup_id = kwargs.get("agegroup_id")
        self.setting_id = kwargs.get("setting_id")
        self.setting_desc = kwargs.get("setting_description")
        self.plot_id = kwargs.get("plot_id")
        self.plot_desc = kwargs.get("plot_description")
        self.theme_id = kwargs.get("theme_id")
        self.theme_desc = kwargs.get("theme_description")
        self.tone_id = kwargs.get("tone_id")
        self.length_id = kwargs.get("length_id")
        self.imagestyle_id = kwargs.get("imagestyle_id")
        self.language_id = kwargs.get("language_id")
        self.narrator_id = kwargs.get("narrator_id")
        self.load_active_records()
        self.load_ai_models()

    def load_active_records(self):
        self.agegroup = ChildAgeRange.objects.filter(id=self.agegroup_id).first()
        self.setting = StorySetting.objects.filter(id=self.setting_id).first()
        self.plot = StoryPlot.objects.filter(id=self.plot_id).first()
        self.theme = StoryTheme.objects.filter(id=self.theme_id).first()
        self.tone = StoryTone.objects.filter(id=self.tone_id).first()
        self.length = StoryLength.objects.filter(id=self.length_id).first()
        self.imagestyle = ImageStyle.objects.filter(id=self.imagestyle_id).first()
        self.language = LanguageOption.objects.filter(id=self.language_id).first()
        self.narrator = NarratorVoice.objects.filter(id=self.narrator_id).first()
        logger.info(
            "Loaded active story records: agegroup=%s, setting=%s, plot=%s, theme=%s, tone=%s",
            self.agegroup, self.setting, self.plot, self.theme, self.tone
        )

    @property
    def age_group(self):
        return self.agegroup.content if self.agegroup else "2-3"

    @property
    def setting_name(self):
        return self.setting.content if self.setting else "Fun"

    @property
    def setting_description(self):
        return self.setting_desc or (self.setting.content if self.setting else "")

    @property
    def plot_name(self):
        return self.plot.content if self.plot else "Fun"

    @property
    def plot_description(self):
        return self.plot_desc or (self.plot.content if self.plot else "")

    @property
    def theme_name(self):
        return self.theme.content if self.theme else "Fun"

    @property
    def theme_description(self):
        return self.theme_desc or ""

    @property
    def tone_name(self):
        return self.tone.content if self.tone else "Playful"

    @property
    def story_length(self):
        return f"{self.length.min}-{self.length.max}" if self.length else "1-5"

    @property
    def image_style(self):
        return self.imagestyle.content if self.imagestyle else "Cartoon"

    @property
    def output_language(self):
        return self.language.content if self.language else "English"

    @property
    def narrator_voice_id(self):
        return self.narrator.vid if self.narrator else None

    def load_ai_models(self):
        self.text_model = AIModel.objects.filter(type="text", is_active=True).first()
        self.image_model = AIModel.objects.filter(type="image", is_active=True).first()
        self.tts_model = AIModel.objects.filter(type="tts", is_active=True).first()
        self.text_api_key = self.text_model.apikey if self.text_model else None
        self.text_model_name = self.text_model.name if self.text_model else "gpt-4-turbo"
        self.image_model_name = self.image_model.name if self.image_model else "dall-e-3"
        tts_endpoint = getattr(self.tts_model, 'endpoint', None)
        self.tts_endpoint = (re.sub(r'(?<!:)//+', '/', tts_endpoint).rstrip('/') if tts_endpoint else None)
        self.tts_api_key = self.tts_model.apikey if self.tts_model else None
        logger.info("Loaded AI models: text=%s, image=%s, tts=%s",
                    self.text_model_name, self.image_model_name, self.tts_model.name if self.tts_model else None)

    def to_prompt(self):
        return " ".join(filter(None, [
            f"Include a brave character named {self.character_name}" + (f" ({self.character_desc})" if self.character_desc else "") + "." if self.character_name or self.character_desc else "",
            f"Write a children's story for age {self.age_group}.",
            f"Set the story in {self.setting_name}" + (f" ({self.setting_description})" if self.setting_description else "") + "." if self.setting_name or self.setting_description else "",
            f"Use the plot: {self.plot_name}" + (f" ({self.plot_description})" if self.plot_description else "") + "." if self.plot_name or self.plot_description else "",
            f"Theme: {self.theme_name}" + (f" ({self.theme_description})" if self.theme_description else "") + "." if self.theme_name or self.theme_description else "",
            f"Tone: {self.tone_name}.",
            f"Language: {self.output_language}.",
            f"Story length: {self.story_length} pages.",
            "The story must have a clear title at the top like 'Title: <story title>' and then the story text.",
            "The story must end naturally at the last page without cutting off sentences."
        ]))