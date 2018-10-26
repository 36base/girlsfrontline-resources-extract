import io
import os
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
override = config.getboolean("main", "override")
save_wav = config.getboolean("acb2wav", "save_wav")
wav_file_name_format = config.get("acb2wav", "wav_file_name_format")


def save(target_dir, file_name, data_source, cue_id, decoder):
    ext = ".wav" if save_wav else ".hca"
    path = os.path.join(target_dir, file_name) + ext
    if not override and os.path.isfile(path):
        logger.info("-> Pass(File already exists)")
        return
    with open(path, "wb") as named_out_file:
        sound_data = data_source.file_data_for_cue_id(cue_id)
        if save_wav:
            # HCA -> WAV 인코딩
            sound_data = decoder.decode(sound_data).read()
        named_out_file.write(sound_data)
        logger.info(f"-> {file_name}{ext}")
    return


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
            name = "{0}_{1}".format(target_dir.split("/")[-1], cue_id)
            save(target_dir, name, data_source, cue_id, d)
    else:
        for track in cue.tracks:
            # cue_id, name, wav_id, enc_type, is_stream = track
            save(target_dir, wav_file_name_format.format(**track._asdict()), data_source, track.wav_id, d)


def acb2wav(file_dir: str, output_dir: str):
    with open(file_dir, "rb") as f:
        file_name = os.path.split(file_dir)[1].split('.')[0]
        extract_acb(f, os.path.join(output_dir, f"wav/{file_name}"))


if __name__ == "__main__":
    import argparse

    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(levelname)s | %(message)s')
    stream_hander = logging.StreamHandler()
    stream_hander.setFormatter(formatter)
    logger.addHandler(stream_hander)
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("-o", "--output_dir", help="Master output dir", type=str, default="./")
    arg_parser.add_argument("target", help="*.acb.bytes file's path", type=str)
    args = arg_parser.parse_args()
    acb2wav(args.target, args.output_dir)
