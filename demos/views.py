import asyncio
import base64
import json
import os
import re
import subprocess
import tempfile
import time
from io import BytesIO
from pathlib import Path
from datetime import datetime

import openai
import requests
from PIL import Image
# from weasyprint import HTML, CSS
from playwright.async_api import async_playwright

from django.conf import settings
from django.core.cache import cache
from django.core.files import File
from django.db.models import Max
from django.http import HttpResponse, JsonResponse, FileResponse, HttpResponseServerError
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.text import slugify
from django.contrib import messages

from payments.models import Coupon, Order, PaymentTransaction
from stories.helper.views import get_story_options
from stories.models import *
from products.models import *
from products.builder import ProductBookBuilder
from logs.models import Log
from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from django.urls import reverse

