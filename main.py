import asyncio
import telegram
import json
import random
import openai
import six
from google.oauth2 import service_account
from google.cloud import translate_v2 as translate


tg_token = 'TOKEN'
openai.api_key = 'TOKEN'
channel_id = '@science_art_at_least_once_a_week'
MAX_POST_LENGTH = 4096
MAX_CAPTION_LENGTH = 1024

# BIG_ID = '23770'
# MEDIUM_ID = '23874'
# SMALL_ID = '12024'


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


def translate_text(target, text):
    """
    Translates text into the target language.
    """

    service_account_info = json.load(open('google-translate-auth.json'))
    credentials = service_account.Credentials.from_service_account_info(
        service_account_info)
    translate_client = translate.Client(credentials=credentials)

    if isinstance(text, six.binary_type):
        text = text.decode("utf-8")

    result = translate_client.translate(text, target_language=target, format_='text')
    return result["translatedText"]


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
    bot = telegram.Bot(tg_token)
    async with bot:
        message = get_message_text(artwork)
        if len(message) >= MAX_POST_LENGTH:
            len_wo_desc = len(message) - len(artwork['description_ru'])
            message = get_message_text(artwork, len_wo_desc, to_cut=True)
            print(await bot.send_message(chat_id=channel_id, text=message, parse_mode='markdown', read_timeout=60))
            images = [telegram.InputMediaPhoto(photo) for photo in artwork['img_list'][:5]]
            if len(images) > 0:
                caption = get_caption_text(artwork)
                print(await bot.send_media_group(chat_id=channel_id, media=images, caption=caption,
                                                 parse_mode='markdown', read_timeout=60))
        elif MAX_CAPTION_LENGTH <= len(message) < MAX_POST_LENGTH:
            print(await bot.send_message(chat_id=channel_id, text=message, parse_mode='markdown', read_timeout=60))
            images = [telegram.InputMediaPhoto(photo) for photo in artwork['img_list'][:5]]
            if len(images) > 0:
                caption = get_caption_text(artwork)
                print(await bot.send_media_group(chat_id=channel_id, media=images, caption=caption,
                                                 parse_mode='markdown', read_timeout=60))
        elif len(message) < MAX_CAPTION_LENGTH:
            if len(artwork['img_list']) > 0:
                print(await bot.send_photo(chat_id=channel_id, photo=artwork['img_list'][0],
                                           caption=message, parse_mode='markdown', read_timeout=60))
            else:
                print(await bot.send_message(chat_id=channel_id, text=message, parse_mode='markdown', read_timeout=60))
        if artwork['category'] != 'Visionary Pioneers of Media Art':
            print(await bot.send_message(chat_id=channel_id, text=review_ru, parse_mode='markdown', read_timeout=60))


async def main():
    try:
        await run_bot()
    except Exception:
        data[key]['description_ru'] = remove_markdown(data[key]['description_ru'])
        await run_bot()


if __name__ == '__main__':
    data = json.load(open('ars_electronica_prizewinners_ru.json', 'r', encoding='utf-8'))
    path = 'not_posted.txt'
    not_posted = open(path, 'r').readline().split(',')
    key = random.choice(not_posted)
    print(f'Key is {key}')
    artwork = data[key]
    prompt = f'Compose an art review that emulates the distinctive style of ' \
             f'a contemporary professional art critic who is an expert in art history,' \
             f' contemporary and science art, and modern technologies such as AI and programming.' \
             f' The review should provide a profound analysis of the visual and technical elements ' \
             f'of the artwork, including the technique and medium employed, the subject matter, ' \
             f'and any underlying symbolism. Discuss the possible intentions of the artist and ' \
             f'how they relate to broader themes or movements within the art world. Offer a personal ' \
             f'interpretation of the artwork, delving into its emotional impact on viewers, and consider ' \
             f'its significance within the oeuvre of artist and the contemporary art scene. Additionally, ' \
             f'draw comparisons between the piece in question and the works of 1 or 2 other contemporary artists, ' \
             f'highlighting any similarities or contrasts in terms of artistic approach, themes, or techniques. ' \
             f'Here is a description of the artwork "{artwork["name"]}" by {artwork["authors"]} ' \
             f'created in {artwork["year"]} year: ' \
             f'\nDescription:\n{delete_apostrophe(artwork["description"])}'
    review = generate_review(prompt)
    review_ru = remove_markdown(translate_text('ru', review)) + '\n\n_Рецензия GPT-4_'
    asyncio.run(main())
    update_posted(path, key)
