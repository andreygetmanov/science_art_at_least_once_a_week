import asyncio
import telegram
import json
import random

token = 'TOKEN'
channel_id = '@science_art_at_least_once_a_week'
MAX_POST_LENGTH = 4096
MAX_CAPTION_LENGTH = 1024

# BIG_ID = '23770'
# MEDIUM_ID = '23874'
# SMALL_ID = '12024'


def get_message_text(artwork: dict, message_length: int = 0, to_cut=False):
    if to_cut:
        return f'*{artwork["name"]}*\n\n{artwork["authors"]}\n\n_{artwork["award"]}, {artwork["year"]}_\n' \
               f'_{artwork["category"]}_\n\n{cut(artwork["description_ru"], message_length)}\n\n{artwork["url"]}'
    return f'*{artwork["name"]}*\n\n{artwork["authors"]}\n\n_{artwork["award"]}, {artwork["year"]}_\n' \
           f'_{artwork["category"]}_\n\n{artwork["description_ru"]}\n\n{artwork["url"]}'


def get_caption_text(artwork: dict):
    return f"*{artwork['name']}*\n\n_{artwork['authors']} ({artwork['year']})_\n\n{artwork['url']}"


def cut(text: str, length: int):
    cut_length = MAX_POST_LENGTH - length
    return text[:cut_length - 3] + '...'


def update_posted(path: str, key: str):
    keys = list(open(path, 'r').readline().split(','))
    new_keys = [old_key for old_key in keys if old_key != key]
    new_text = ','.join([new_key for new_key in new_keys])
    with open(path, 'w') as f:
        f.write(new_text)
        f.close()


async def main():
    """
    If the description is too long, it will be cut. Not more than 5 photos will be posted in the next message.
    If the description is too long for caption, <= 5 photos will be posted in the next message.
    If the description is short, it will be posted with one photo as caption.
    """
    bot = telegram.Bot(token)
    async with bot:
        message = get_message_text(artwork)
        if len(message) >= MAX_POST_LENGTH:
            len_wo_desc = len(message) - len(artwork['description_ru'])
            message = get_message_text(artwork, len_wo_desc, to_cut=True)
            print(await bot.send_message(chat_id=channel_id, text=message, parse_mode='markdown'))
            images = [telegram.InputMediaPhoto(photo) for photo in artwork['img_list'][:5]]
            if len(images) > 0:
                caption = get_caption_text(artwork)
                print(await bot.send_media_group(chat_id=channel_id, media=images, caption=caption,
                                                 parse_mode='markdown', read_timeout=60))
        elif MAX_CAPTION_LENGTH <= len(message) < MAX_POST_LENGTH:
            print(await bot.send_message(chat_id=channel_id, text=message, parse_mode='markdown'))
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
                print(await bot.send_message(chat_id=channel_id, text=message, parse_mode='markdown'))


if __name__ == '__main__':
    data = json.load(open('IA_AI_prizewinners_ru.json', 'r', encoding='utf-8'))
    path = 'not_posted.txt'
    not_posted = open(path, 'r').readline().split(',')
    key = random.choice(not_posted)
    artwork = data[key]
    asyncio.run(main())
    update_posted(path, key)
