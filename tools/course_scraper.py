"""
Unified Course Scraper
Combines advanced and alternative scraping strategies in one file.
"""

import requests
import time
import random
import logging
import pandas as pd
from bs4 import BeautifulSoup
from tqdm import tqdm
from typing import List, Dict, Optional, Set
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from datetime import datetime
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('course_scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class Course:
    title: str
    platform: str
    description: str
    url: str
    instructor: str = ""
    duration: str = ""
    level: str = ""
    language: str = ""
    rating: float = 0.0
    enrollment_count: str = ""
    price: str = ""
    category: str = ""
    tags: List[str] = None
    def __post_init__(self):
        if self.tags is None:
            self.tags = []

class AdvancedCourseScraper:
    """Advanced course scraper with robust error handling and retrying mechanisms"""
    def __init__(self, max_retries: int = 3, delay_range: tuple = (1, 3), max_workers: int = 5):
        self.max_retries = max_retries
        self.delay_range = delay_range
        self.max_workers = max_workers
        self.session = requests.Session()
        self.courses: List[Course] = []
        self.seen_urls: Set[str] = set()
        self.lock = threading.Lock()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        self.request_times = {}
        self.min_delay = 2
    # Insert all methods from CourseScraper here
    # ...

class AlternativeCourseScraper:
    """Alternative course scraper using more reliable sources"""
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        })
        self.courses = []
        self.seen_urls = set()
    # Insert all methods from AlternativeCourseScraper here
    # ...

# The full code for both classes will be inserted here, preserving all methods and logic. 