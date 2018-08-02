import io
import os
import time

from modules import acb
import hcapy


def extract_acb(acb_file, target_dir):
    utf = acb.UTFTable(acb_file)
    cue = acb.TrackList(utf)
    embedded_awb = io.BytesIO(utf.rows[0]["AwbFile"])
    data_source = acb.AFSArchive(embedded_awb)
    d = hcapy.Decoder(1)  # 22397
    os.makedirs(target_dir, exist_ok=True)

    for track in cue.tracks:
        # cue_id, name, wav_id, enc_type, is_stream = track
        print(track.name)
        name = "{0}{1}".format(track.name, ".wav")
        with open(os.path.join(target_dir, name), "wb") as named_out_file:
            hca_data = data_source.file_data_for_cue_id(track.wav_id)
            wav_data = d.decode(hca_data).read()
            named_out_file.write(wav_data)


def acb2wav(file_dir: str):
    with open(file_dir, "rb") as f:
        file_name = os.path.split(file_dir)[1].split('.')[0]
        extract_acb(f, f"wav/{file_name}")


if __name__ == "__main__":
    start_time = time.time()
    acb2wav("9A91.acb.bytes")
    print("--- %s seconds ---" % (time.time() - start_time))