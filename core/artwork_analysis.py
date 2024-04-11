import requests
import torch
from PIL import Image
from dotenv import load_dotenv
from openai import OpenAI
from transformers import LlavaNextProcessor, LlavaNextForConditionalGeneration

from core.document_retrieval import VectorDB, Retriever

load_dotenv()


class Artwork:
    def __init__(self, metadata):
        self.name = metadata.get("name")
        self.authors = metadata.get("authors")
        self.year = metadata.get("year")
        self.description = self.delete_apostrophe(metadata.get("description", ""))
        self.images = metadata.get("img_list", [])

    @staticmethod
    def delete_apostrophe(text):
        return text.replace("'", "")

    def __str__(self):
        return self.name


class ArtworkRetriever:
    def __init__(self, source):
        self.source = source
        self.vector_db = self.init_vector_db()
        self.retriever = Retriever(self.vector_db)

    def init_vector_db(self):
        vector_db = VectorDB(self.source)
        vector_db.load()
        vector_db.create_db()
        return vector_db

    def get_related_artworks(self, main_artwork, k=2):
        related_artworks_data = self.retriever.get_top_k(
            main_artwork.description, main_artwork.name, k
        )
        return [Artwork(doc.metadata) for doc in related_artworks_data]


class ArtworkAnalyser:
    def __init__(self, api_key):
        self.client = OpenAI(api_key=api_key)

    def analyze_artworks(self, main_artwork, related_artworks):
        prompt = self.create_prompt(main_artwork, related_artworks)
        print('Prompt: ', prompt)
        images = [main_artwork.images[0]] + [
            artwork.images[0] for artwork in related_artworks
        ]
        print('Images: ', images)
        response = self.client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt,
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": images[0],
                                "detail": "low"
                            },
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": images[1],
                                "detail": "low"
                            },
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": images[2],
                                "detail": "low"
                            },
                        },
                    ],
                }
            ],
            max_tokens=2000,
        )
        return response.choices[0].message.content

    @staticmethod
    def create_prompt(main_artwork, related_artworks):
        prompt = (
            f"Imagine you are an experienced art critic. "
            f"You are presented with descriptions of three artworks. "
            f"The first one is the main artwork and two related artworks are similar to the first one. "
            f"Artworks also have related images, analyze their content and use this analysis in your reviews.\n\n"
            f"**Main artwork**: name: **{main_artwork.name}**, authors: **{main_artwork.authors}**, year: **{main_artwork.year}**, description: {main_artwork.description}\n"
            f"**Related artwork 1**: name: **{related_artworks[0].name}**, authors: **{related_artworks[0].authors}**, year: **{related_artworks[0].year}**, description: {related_artworks[0].description}\n"
            f"**Related artwork 2**: name: **{related_artworks[1].name}**, authors: **{related_artworks[1].authors}**, year: **{related_artworks[1].year}**, description: {related_artworks[1].description}\n\n"
            f"Briefly explain all these artworks and similarities and differences between artworks. "
            f"Your text must look human-like, not a rigorous review. "
            f"Give your answer in Russian, but do not translate the names of artists and artworks. "
            f"Do not divide description and reasoning parts. "
            f"Use Markdown to structure your answer. "
            f"Make the names of artists and artworks bold."
            f"Do not explicitly divide your review into parts, simulate a true human speech. Do not use any titles or subtitles. "
            f"Do not explicitly refer to the artworks as Main or Related. Use their titles instead."
        )
        return prompt


class HFArtworkAnalyser:
    def __init__(self, model_name='llava-hf/llava-v1.6-mistral-7b-hf'):
        self.processor = LlavaNextProcessor.from_pretrained(model_name)
        self.model = LlavaNextForConditionalGeneration.from_pretrained(
            model_name,
            torch_dtype=torch.float16,
            low_cpu_mem_usage=True,
            load_in_4bit=True,
            # use_flash_attention_2=True,
        )

    def analyze_artworks(self, main_artwork, related_artworks):
        prompt = self.create_prompt(main_artwork, related_artworks)

        images_urls = [main_artwork.images[0]] + [artwork.images[0] for artwork in related_artworks]
        images = []
        for url in images_urls:
            image = Image.open(requests.get(url, stream=True).raw)
            # Resize the image to the required size for the model; you might need to adjust this size
            image = image.resize((256, 256))
            images.append(image)

        full_prompt = "[INST] " + "\n".join(["<image>"] * len(images)) + "\n" + prompt + " [/INST]"
        inputs = self.processor(full_prompt, images=images, return_tensors="pt").to("cuda:0")

        output = self.model.generate(**inputs, max_new_tokens=1000)
        return self.processor.decode(output[0], skip_special_tokens=True)

    @staticmethod
    def create_prompt(main_artwork, related_artworks):
        # Create a prompt based on the artwork descriptions
        prompt = (
            f"Below are the descriptions of three artworks, including one main artwork and two related artworks. "
            f"Analyze and compare these artworks based on their descriptions and the accompanying images.\n\n"
            f"**Main artwork**: name: **{main_artwork.name}**, authors: **{main_artwork.authors}**, "
            f"year: **{main_artwork.year}**, description: {main_artwork.description}\n"
            f"**Related artwork 1**: name: **{related_artworks[0].name}**, authors: **{related_artworks[0].authors}**, "
            f"year: **{related_artworks[0].year}**, description: {related_artworks[0].description}\n"
            f"**Related artwork 2**: name: **{related_artworks[1].name}**, authors: **{related_artworks[1].authors}**, "
            f"year: **{related_artworks[1].year}**, description: {related_artworks[1].description}"
        )
        return prompt
