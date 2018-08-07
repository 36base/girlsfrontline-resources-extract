import io
import os
import time
import logging

from modules import acb
import hcapy

logger = logging.getLogger("acb")


def save(file_name, data_source, cue_id, decoder):
    with open(file_name, "wb") as named_out_file:
        hca_data = data_source.file_data_for_cue_id(cue_id)
        wav_data = decoder.decode(hca_data).read()
        named_out_file.write(wav_data)


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
            name = "{0}_{1}{2}".format(target_dir.split("/")[-1], cue_id, ".wav")
            save(os.path.join(target_dir, name), data_source, cue_id, d)
    else:
        for track in cue.tracks:
            # cue_id, name, wav_id, enc_type, is_stream = track
            logger.info(track.name)
            name = "{0}{1}".format(track.name, ".wav")
            save(os.path.join(target_dir, name), data_source, track.wav_id, d)


def acb2wav(file_dir: str):
    with open(file_dir, "rb") as f:
        file_name = os.path.split(file_dir)[1].split('.')[0]
        extract_acb(f, f"wav/{file_name}")


if __name__ == "__main__":
    start_time = time.time()
    acb2wav("9A91.acb.bytes")
    print("--- %s seconds ---" % (time.time() - start_time))