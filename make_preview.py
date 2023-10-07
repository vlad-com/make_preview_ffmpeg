from pathlib import Path
from time import time
import dateutil.parser
from json import loads
from subprocess import check_output, run, PIPE
import argparse

def with_ffprobe(filename):
    result = check_output(
        f'ffprobe -b quiet -show_streams -select_streams v:0 -of json "{filename}"',
        shell=True
    ).decode()
    fields = loads(result)['streams'][0]
    # fields['tags'] =  {k.lower(): v for k, v in fields['tags'].items()}
    # print("fields:",fields)

    duration = fields.get("duration")
    if duration == None:
        duration = run(
            f'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{filename}"', stdout=PIPE).stdout

    fps = fields['r_frame_rate']
    try:
        creation_time_str = fields['tags'].get('creation_time')
        if creation_time_str == None:
            creation_time_str = fields['tags']["_STATISTICS_WRITING_DATE_UTC"]
        creation_time = dateutil.parser.parse(
            creation_time_str, fuzzy=True).date()
    except Exception as e:
        print("ERR:", e)
        creation_time = "none"
    decodec = fields['codec_name']

    return float(duration), fps, creation_time, decodec


def make_preview(filename, split_by, part_duration, audio=True, hwaccel=None, preset="slow", codec="h264", quality=23, ios_hevc_support=True):
    print(split_by, part_duration, audio, hwaccel)
    duration, fps, creation_time, decodec = with_ffprobe(filename)
    if duration > split_by:
        crop = (duration*10)/split_by

        # if decodec=="wmv3":
        #     decodec="h264"
        if hwaccel == None or hwaccel.startswith("libx"):
            cmd = f'ffmpeg -y -i "{filename}" -c:v {codec} -preset {preset} '#-c:s copy -c:a copy
            quality_name = "crf" 
        else:
            ffmpeg_path="ffmpeg"
            decoders_hw=["vp9","vp8","vc1","mpeg4","mpeg2","mpeg1","mjpeg","hevc","h264","av1"]

            if hwaccel == "cuda":
                encoder = "nvenc"
                decoder = "cuvid"
                hwaccel_name = "nvdec"
                quality_name = "qp"
                for i in decoders_hw:
                    if i == decodec:
                        decoder_final=f"{decodec}_{decoder}"
                        break
                else:
                    decoder_final=decodec
                
            else:
                not_awaliable_in_qsv=["mpeg4","mpeg1"]
                encoder = hwaccel
                decoder = hwaccel
                hwaccel_name = hwaccel
                quality_name = "global_quality"
                for i in not_awaliable_in_qsv:
                    if i == decodec:
                        decoder_final=decodec
                        break
                else:
                    for i in decoders_hw:
                        if i == decodec:
                            decoder_final=f"{decodec}_{decoder}"
                            break
                    else:
                        decoder_final=decodec
                
            cmd = f'"{ffmpeg_path}" -hwaccel {hwaccel_name} -c:v {decoder_final} -y -i "{filename}" -c:v {codec}_{encoder} -preset {preset} '
            
        cmd += f'-filter_complex "[0:v]select=\'lt(mod(t,{crop}/10),{part_duration})\',setpts=N/(FRAME_RATE*TB)" '
        if audio:
            cmd += f'-af "aselect=\'lt(mod(t,{crop}/10),{part_duration})\',asetpts=N/(FRAME_RATE*TB)" '
        else:
            cmd += f'-an '
        #b-frames turned off becouse low support on platforms
        if codec == "hevc":
            cmd += "-b_ref_mode 0 "
            if ios_hevc_support:
                cmd += "-tag:v hvc1 "
        path_items = Path(filename)
        cmd += f'-{quality_name} {quality} "{path_items.parent}/{path_items.name}.prewiev.mp4"'#
        #if gpu does not support b-frames
        # cmd += f'-b_ref_mode 0 -qp {quality} "{path_items.parent}/{creation_time}.{path_items.name}.prewiev_na.mp4"'
        print("cmd:", cmd)
        st = time()
        result = check_output(cmd, shell=True).decode()
        et = time()
        elapsed_time = et - st
        print(path_items.name, 'Execution time:', elapsed_time, 'seconds')
    else:
        print("err: duration > than split_by")


# Initialize parser
parser = argparse.ArgumentParser()

# Adding optional argument
parser.add_argument("-f", "--file", help="Path to file")
parser.add_argument("-hw", "--hwaccel",
                    help="Hardware acceleration (can be: [qsv, cuda])")
parser.add_argument("-c", "--codec", help="Codec (default: h264)")
parser.add_argument("-a", "--audio", help="Turn on/off audio (default: True)")
parser.add_argument("-s", "--split", help="Split by parts (default: 12)")
parser.add_argument(
    "-p", "--part", help="Part duration in seconds (default: 0.766)")
parser.add_argument(
    "-q", "--quality", help="Video quality scale is 0–51, where 0 is lossless, 51 is worst quality possible (default: 23)")
parser.add_argument("-o", "--output", help="Show Output")

# Read arguments from command line
args = parser.parse_args()

if args.file == None:
    raise Exception("Error. Add file path.")

split_by = args.split if args.split else 12
part_duration = args.part if args.part else 0.766
audio = args.audio.lower() == "true" if args.audio else True
codec = args.codec if args.codec else "h264"
quality = args.quality if args.quality else 23
quality = float(quality)

print("FILE:", args.file)
duration, fps, creation_time, decodec = with_ffprobe(args.file)
print(duration, fps, creation_time)


make_preview(args.file, split_by=split_by, part_duration=part_duration,
             audio=audio, hwaccel=args.hwaccel, codec=codec, quality=quality)