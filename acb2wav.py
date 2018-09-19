import io
import os
import time
import logging
import configparser

from modules import acb
import hcapy


config = configparser.ConfigParser()
try:
    config.read("config.ini", encoding="utf-8")
except configparser.MissingSectionHeaderError:
    config.read("config.ini", encoding="utf-8-sig")

logger = logging.getLogger("acb")
save_wav = config.getboolean("acb2wav", "save_wav")


def save(file_name, data_source, cue_id, decoder):
    ext = ".wav" if save_wav else ".hca"
    with open(file_name + ext, "wb") as named_out_file:
        sound_data = data_source.file_data_for_cue_id(cue_id)
        if save_wav:
            # HCA -> WAV 인코딩
            sound_data = decoder.decode(sound_data).read()
        named_out_file.write(sound_data)


def extract_acb(acb_file, target_dir):
    utf = acb.UTFTable(acb_file)
    cue = acb.TrackList(utf)
    embedded_awb = io.BytesIO(utf.rows[0]["AwbFile"])
    data_source = acb.AFSArchive(embedded_awb)
    d = hcapy.Decoder(1)  # 22397
    os.makedirs(target_dir, exist_ok=True)

    if len(data_source.files) > len(cue.tracks):
        logger.warning("Cannot find all cue info")
        for file_ent in data_source.files:
            cue_id = file_ent.cue_id
            logger.info("{0}_{1}".format(target_dir.split("/")[-1], cue_id))
            name = "{0}_{1}".format(target_dir.split("/")[-1], cue_id)
            save(os.path.join(target_dir, name), data_source, cue_id, d)
    else:
        for track in cue.tracks:
            # cue_id, name, wav_id, enc_type, is_stream = track
            logger.info(track.name)
            save(os.path.join(target_dir, track.name), data_source, track.wav_id, d)


def acb2wav(file_dir: str, output_dir: str):
    with open(file_dir, "rb") as f:
        file_name = os.path.split(file_dir)[1].split('.')[0]
        extract_acb(f, os.path.join(output_dir, f"wav/{file_name}"))


if __name__ == "__main__":
    start_time = time.time()
    acb2wav("9A91.acb.bytes")
    print("--- %s seconds ---" % (time.time() - start_time))
