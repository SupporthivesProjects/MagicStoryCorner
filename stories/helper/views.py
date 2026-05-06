from stories.models import *

def get_story_options():
    return {
        "agegroups": ChildAgeRange.objects.filter(is_active=True),
        "settings": StorySetting.objects.filter(is_active=True),
        "plots": StoryPlot.objects.filter(is_active=True),
        "themes": StoryTheme.objects.filter(is_active=True),
        "tones": StoryTone.objects.filter(is_active=True),
        "lengths": StoryLength.objects.filter(is_active=True),
        "imagestyles": ImageStyle.objects.filter(is_active=True),
        "languages": LanguageOption.objects.filter(is_active=True),
        "narrators": NarratorVoice.objects.filter(is_active=True),
        "endings": StoryEnd.objects.filter(is_active=True),
    }