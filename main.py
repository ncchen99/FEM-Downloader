# %%
import re
from telethon import TelegramClient, events, sync
from pathlib import Path
from time import sleep
from ruamel.yaml import YAML
from pathvalidate import sanitize_filename
from telethon.tl.types import DocumentAttributeAudio

# %%
config_file_path = 'config.yaml'
record_file_path = 'record.yaml'

# %%
yaml = YAML()

config_file = Path(config_file_path)
config = yaml.load(config_file)

client = TelegramClient('session_name', config["api_id"], config["api_hash"])
client.start()

# %%
def create_folder(folder_name):
    if not Path(folder_name).exists():
        Path(folder_name).mkdir()

def path_join(folder_name, file_name):
    return Path(folder_name).joinpath(Path(file_name).name)

# %%
albums_folder = 'albums'
songs_folder = 'songs'
not_classified_name = 'Unknown'
albums_intro_file = 'intro.txt'

create_folder(albums_folder)
create_folder(songs_folder)

#%%
for child in Path(".").iterdir():
    if child.is_file() and ".mp3" in child.name:
        child.unlink()

# %%
record_file = Path(record_file_path)
record = yaml.load(record_file)

async def download_media(msg):
    audio_attributes = [attr for attr in msg.audio.attributes if isinstance(attr, DocumentAttributeAudio)]
    filename = f"{audio_attributes[0].performer} - {audio_attributes[0].title}.mp3" if audio_attributes[0].title and audio_attributes[0].performer else msg.file.name.replace('_', ' ')
    filename = sanitize_filename(filename)
    print(f"downloading {filename} ...")
    audio_file_path = await client.download_media(msg, file=filename)
    audio_file = Path(audio_file_path)
    
    if record["is_album"]:
        if not Path(record["album_path"]).exists():
            create_folder(record["album_path"])
        audio_file.rename(path_join(record["album_path"], audio_file_path))
    else:
        if not Path(record["song_style_path"]).exists():
            create_folder(record["song_style_path"])
        audio_file.rename(path_join(record["song_style_path"], audio_file_path))
        # record["song_name"] + (f'({record["song_amount_count"]})' if record["song_amount_count"] > 0 else '' ) + '.mp3' if audio_file_path.count('_') > 1 and record["song_name"] else 

    print("save", audio_file.name, "successfully!")

for msg in client.iter_messages('@fresh_electronic_music', reverse=True, offset_id=record["offset_id"]):
    if msg.audio :
        client.loop.run_until_complete(download_media(msg))
    elif msg.text:
        if "#fem_album" in msg.text or " EP" in msg.text:
            record["is_album"] = True
            
            album_name_re = re.search(r'(?<=\n)(.{1,}-.{1,})(?=\n)|(?<=\n)(.{1,})(?=\n)', msg.text)
            record["album_path"] = str(path_join(albums_folder, sanitize_filename(album_name_re.group().strip()) if album_name_re else not_classified_name))
            create_folder(record["album_path"])

            record["album_intro"] = msg.text
            path_join(record["album_path"], albums_intro_file).write_text(record["album_intro"])
        elif "#fem_hardstyle" in msg.text:
            record["is_album"] = False
            record["song_style_path"] = str(path_join(songs_folder, "Hardstyle"))
            create_folder(record["song_style_path"])

            record["song_name"] = ""
        elif "#fem_release" in msg.text:
            record["is_album"] = False
        
            song_name_re = re.search(r'(?<=\n)(.{1,}-.{1,})(?=\n)|(?<=\n)(.{1,})(?=\n)', msg.text)
            record["song_name"] = song_name_re.group().strip() if song_name_re else not_classified_name
            
            print("song_name:", record["song_name"])

            song_styles_re = re.search(r'(?<=Style:)(.*)(?=\n)', msg.text)
            song_styles = song_styles_re.group().strip().split(' / ') if song_styles_re else [not_classified_name]
            # here we only use the first style as the folder name
            song_style = song_styles[0].strip().replace('-', ' ')
            print("song_styles:", song_style)
            record["song_style_path"] = str(path_join(songs_folder, song_style))
            create_folder(record["song_style_path"])
        else:
            record["is_album"] = False
            record["song_style_path"] = str(path_join(songs_folder, not_classified_name))
            print("song_styles:", not_classified_name)
            create_folder(record["song_style_path"])
            
        # TODO: determine if the message contains spcific keyword 
        # and classify it as single song or album
        # store the song name, album name, style, artist, etc.
        

    # record last process message id to file
    # TODO: record the last process album or song name to file
    record["offset_id"] = msg.id
    yaml.dump(record, record_file)

# %%



