import json
import random
import torch
import gc
from dotenv import load_dotenv
from core.artwork_analysis import Artwork, ArtworkRetriever, HFArtworkAnalyser

load_dotenv()

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

del artwork_retriever
torch.cuda.empty_cache()  # Clear memory cache if using CUDA
gc.collect()
t = torch.cuda.get_device_properties(0).total_memory
r = torch.cuda.memory_reserved(0)
a = torch.cuda.memory_allocated(0)
f = r-a
print(f)  # free inside reserved
hf_analysis = HFArtworkAnalyser()
hf_analysis_result = hf_analysis.analyze_artworks(main_artwork, related_artworks)

print(hf_analysis_result)
