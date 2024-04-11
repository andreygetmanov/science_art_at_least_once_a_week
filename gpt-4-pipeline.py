import json
import os
import random

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
client = OpenAI(api_key=OPENAI_API_KEY)

from core.artwork_analysis import Artwork, ArtworkRetriever, ArtworkAnalyser

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
source = 'ars_electronica_prizewinners_ru.json'
with open(source, 'r', encoding='utf-8') as f:
    data = json.load(f)
path = 'not_posted.txt'
with open(path, 'r') as f:
    not_posted = f.readline().split(',')

key = random.choice(not_posted)

main_artwork_data = data[key]

main_artwork = Artwork(main_artwork_data)

artwork_retriever = ArtworkRetriever(source)
related_artworks = artwork_retriever.get_related_artworks(main_artwork)

analysis = ArtworkAnalyser(OPENAI_API_KEY)
analysis_result = analysis.analyze_artworks(main_artwork, related_artworks)

print(analysis_result)
