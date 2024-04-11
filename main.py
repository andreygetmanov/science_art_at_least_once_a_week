import asyncio
import json
import random
import os
from core.artwork_analysis import Artwork, ArtworkRetriever, ArtworkAnalyser
import openai
import telegram

from dotenv import load_dotenv

load_dotenv()

TELEGRAM_API_KEY = os.getenv('TG_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
channel_id = '@science_art_at_least_once_a_week'
MAX_POST_LENGTH = 4096
MAX_CAPTION_LENGTH = 1024


def get_message_text(artwork: dict, message_length: int = 0, to_cut=False):
    if to_cut:
        return f'*{artwork["name"]}*\n\n{artwork["authors"]}\n\n_{artwork["award"]}, {artwork["year"]}_\n' \
               f'_{artwork["category"]}_\n\n{cut(artwork["description_ru"], message_length)}\n\n{artwork["url"]}\n\n' \
               f'{to_hashtag(artwork["award"])} {to_hashtag(artwork["category"])} {to_hashtag(artwork["year"]) + "year"}'
    return f'*{artwork["name"]}*\n\n{artwork["authors"]}\n\n_{artwork["award"]}, {artwork["year"]}_\n' \
           f'_{artwork["category"]}_\n\n{artwork["description_ru"]}\n\n{artwork["url"]}\n\n' \
           f'{to_hashtag(artwork["award"])} {to_hashtag(artwork["category"])} {to_hashtag(artwork["year"]) + "year"}'


def get_caption_text(artwork: dict):
    return f'*{artwork["name"]}*\n\n_{artwork["authors"]} ({artwork["year"]})_\n\n{artwork["url"]}\n\n' \
           f'{to_hashtag(artwork["award"])} {to_hashtag(artwork["category"])} {to_hashtag(artwork["year"]) + "year"}'


def cut(text: str, length: int):
    cut_length = MAX_POST_LENGTH - length
    return text[:cut_length - 3] + '...'


def to_hashtag(text: str) -> str:
    return '#' + text.lower().replace('-', '').replace('–', '')\
        .replace('(', '').replace(')', '').replace('/', ' ').replace('&', '')\
        .replace('   ', ' ').replace('  ', ' ').replace(' ', '\_')


def delete_apostrophe(text):
    return text.replace("'", "")


def remove_markdown(text: str) -> str:
    # removes all markdown symbols from text
    return text.replace('*', '').replace('_', '')


def generate_review(prompt: str) -> str:
    completion = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        timeout=120
    )
    return completion['choices'][0]['message']['content']


def update_posted(path: str, key: str):
    keys = list(open(path, 'r').readline().split(','))
    new_keys = [old_key for old_key in keys if old_key != key]
    new_text = ','.join([new_key for new_key in new_keys])
    with open(path, 'w') as f:
        f.write(new_text)
        f.close()


async def run_bot():
    """
    If the description is too long, it will be cut. Not more than 5 photos will be posted in the next message.
    If the description is too long for caption, <= 5 photos will be posted in the next message.
    If the description is short, it will be posted with one photo as caption.
    """
    bot = telegram.Bot(TELEGRAM_API_KEY)
    async with bot:
        message = get_message_text(main_artwork_data)
        if len(message) >= MAX_POST_LENGTH:
            len_wo_desc = len(message) - len(main_artwork_data['description_ru'])
            message = get_message_text(main_artwork_data, len_wo_desc, to_cut=True)
            print(await bot.send_message(chat_id=channel_id, text=message, parse_mode='markdown', read_timeout=60))
            images = [telegram.InputMediaPhoto(photo) for photo in main_artwork_data['img_list'][:5]]
            if len(images) > 0:
                caption = get_caption_text(main_artwork_data)
                print(await bot.send_media_group(chat_id=channel_id, media=images, caption=caption,
                                                 parse_mode='markdown', read_timeout=60))
        elif MAX_CAPTION_LENGTH <= len(message) < MAX_POST_LENGTH:
            print(await bot.send_message(chat_id=channel_id, text=message, parse_mode='markdown', read_timeout=60))
            images = [telegram.InputMediaPhoto(photo) for photo in main_artwork_data['img_list'][:5]]
            if len(images) > 0:
                caption = get_caption_text(main_artwork_data)
                print(await bot.send_media_group(chat_id=channel_id, media=images, caption=caption,
                                                 parse_mode='markdown', read_timeout=60))
        elif len(message) < MAX_CAPTION_LENGTH:
            if len(main_artwork_data['img_list']) > 0:
                print(await bot.send_photo(chat_id=channel_id, photo=main_artwork_data['img_list'][0],
                                           caption=message, parse_mode='markdown', read_timeout=60))
            else:
                print(await bot.send_message(chat_id=channel_id, text=message, parse_mode='markdown', read_timeout=60))
        if main_artwork_data['category'] != 'Visionary Pioneers of Media Art':
            print(await bot.send_message(chat_id=channel_id, text=review_ru, parse_mode='markdown', read_timeout=60))


async def main():
    try:
        await run_bot()
    except Exception:
        data[key]['description_ru'] = remove_markdown(data[key]['description_ru'])
        await run_bot()


if __name__ == '__main__':
    source = 'ars_electronica_prizewinners_ru.json'
    data = json.load(open(source, 'r', encoding='utf-8'))
    path = 'not_posted.txt'
    not_posted = open(path, 'r').readline().split(',')
    key = random.choice(not_posted)
    print(f'Key is {key}')
    main_artwork_data = data[key]
    main_artwork = Artwork(main_artwork_data)
    artwork_retriever = ArtworkRetriever(source)
    related_artworks = artwork_retriever.get_related_artworks(main_artwork)

    analysis = ArtworkAnalyser(OPENAI_API_KEY)
    analysis_result = analysis.analyze_artworks(main_artwork, related_artworks)
    review_ru = analysis_result + '\n\n_Рецензия GPT-4_'
    asyncio.run(main())
    update_posted(path, key)
