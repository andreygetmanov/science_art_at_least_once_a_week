import json
import os
from dotenv import load_dotenv
from openai import OpenAI
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
        return response.choices

    @staticmethod
    def create_prompt(main_artwork, related_artworks):
        prompt = (
            f"Imagine you are an experienced art critic. "
            f"You are presented with descriptions of three artworks. "
            f"The first one is the main artwork and two related artworks are similar to the first one. "
            f"On the first step, you should provide a separate review of all the artworks. "
            f"Artworks also have related images, analyze their content and use this analysis in your reviews. "
            f"On the second step, summarize all of these artworks in terms of similarities and differences.\n\n"
            f"**Main artwork**: name: **{main_artwork.name}**, authors: **{main_artwork.authors}**, year: **{main_artwork.year}**, description: {main_artwork.description}\n"
            f"**Related artwork 1**: name: **{related_artworks[0].name}**, authors: **{related_artworks[0].authors}**, year: **{related_artworks[0].year}**, description: {related_artworks[0].description}\n"
            f"**Related artwork 2**: name: **{related_artworks[1].name}**, authors: **{related_artworks[1].authors}**, year: **{related_artworks[1].year}**, description: {related_artworks[1].description}\n\n"
            f"Give your answer in Russian, but do not translate the names of artists and artworks. "
            f"Do not divide description and reasoning parts, combine them into the one paragraph. "
            f"Use Markdown to structure your answer. Make the names of artists and artworks bold. "
            f"Give your answer step-by-step for each artwork."
        )
        return prompt
