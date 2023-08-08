from scenedetect import open_video, open_video, VideoStream
import os 
import s3
from typing import Optional

from typing import List, Tuple, Dict
from scenedetect.frame_timecode import FrameTimecode
from scenedetect.scene_manager import SceneManager
from scenedetect.platform import (tqdm, get_and_create_path, get_cv2_imwrite_params)
from slide_change_detector import SlideChangeDetector

import csv
import pytesseract

import cv2
import numpy as np

from difflib import SequenceMatcher

SCENE_THRESHOLD=8.0
FRAME_SKIP=149

TESSERACT_OCR_THRESHOLD = 90
OCR_DUP_THRESHOLD = 0.75

def detect(
    video_path: str,
) -> List[Tuple[FrameTimecode, FrameTimecode]]:

    video = open_video(video_path)
    scene_manager = SceneManager()
    scene_manager.add_detector(SlideChangeDetector(threshold=SCENE_THRESHOLD))
    scene_manager.detect_scenes(
        video=video,
        show_progress=True,
        frame_skip=FRAME_SKIP
    )
    return scene_manager.get_scene_list(start_in_scene=False)


def detect_slides(project):

    frames_path = os.path.join(project['path'], "frames")
    os.makedirs(frames_path)
    project['frames_path'] = frames_path

    scene_list = detect(project['input'])
    video = open_video(project['input'])
    deduped_scene_list = save_images(scene_list, video, num_images=1, output_dir=frames_path)

    for i, scene in enumerate(deduped_scene_list):

        filepath = frames_path + "/" + scene['frame_file']
        frame_url = s3.upload_file(project, 'frames', filepath)

        scene_record = {'id': i, 'frame_path': filepath, 'frame_num': scene['frame_num'], 'frame_url': frame_url, 'frame_text': scene['frame_text']}
        scene_record['start'] = scene['start']
        scene_record['end'] = scene['end']
        #print(scene_record)
        project['scenes'].append(scene_record)


#
# TODO(v1.0): Refactor to take a SceneList object; consider moving this and save scene list
# to a better spot, or just move them to scene_list.py.
#
def save_images(scene_list: List[Tuple[FrameTimecode, FrameTimecode]],
                video: VideoStream,
                num_images: int = 3,
                image_extension: str = 'jpg',
                encoder_param: int = 90,
                output_dir: Optional[str] = None) -> Dict[int, List[str]]:
 

    imwrite_param = [get_cv2_imwrite_params()[image_extension], encoder_param
                    ] if encoder_param is not None else []

    video.reset()

    progress_bar = tqdm(total=len(scene_list) * num_images, unit='images', dynamic_ncols=True)

    framerate = scene_list[0][0].framerate

    timecode_list = [
        [
            FrameTimecode(int(f), fps=framerate) for f in [
                                                                                               # middle frames
                a[len(a) // 2]
                                                                                               # for each evenly-split array of frames in the scene list
                for j, a in enumerate(np.array_split(r, num_images))
            ]
        ] for i, r in enumerate([
                                                                                               # pad ranges to number of images
            r if 1 + r[-1] - r[0] >= num_images else list(r) + [r[-1]] * (num_images - len(r))
                                                                                               # create range of frames in scene
            for r in (
                range(
                    start.get_frames(),
                    start.get_frames() + max(
                        1,                                                                     # guard against zero length scenes
                        end.get_frames() - start.get_frames()))
                                                                                               # for each scene in scene list
                for start, end in scene_list)
        ])
    ]

    deduped_scene_list = []
    last_frame_text = []
    for i, scene_timecodes in enumerate(timecode_list):
        for j, image_timecode in enumerate(scene_timecodes):
            video.seek(image_timecode)
            frame_im = video.read()
            if frame_im is not None:
                dup, last_frame_text = frame_to_text(frame_im, last_frame_text)
                if dup is False and len(last_frame_text) > 0:
                    file_path = f"{i + 1}-{image_timecode.get_frames()}.{image_extension}"
                    cv2.imwrite(get_and_create_path(file_path, output_dir), frame_im, imwrite_param)
                    deduped_scene_list.append({"start":scene_list[i][0].get_seconds(), "end":scene_list[i][1].get_seconds(), "frame_file":file_path, "frame_num": image_timecode.get_frames(), "frame_text": last_frame_text})
                # else:
                #     print("DROPPED", {"start":scene_list[i][0].get_seconds(), "end":scene_list[i][1].get_seconds(), "frame_num": image_timecode.get_frames(), "frame_text": last_frame_text})
            else:
                break
            if progress_bar is not None:
                progress_bar.update(1)

    return deduped_scene_list


def tesseract_ocr(frame_im):
        img_rgb = cv2.cvtColor(frame_im, cv2.COLOR_BGR2RGB)
        text_frames = pytesseract.image_to_data(img_rgb, lang='eng')

        frame_text = []
        reader = csv.DictReader(text_frames.split("\n"), delimiter="\t", quoting=csv.QUOTE_NONE)
        rects = [r for r in reader]
        for rect in rects:
            rect['text'] = rect['text'].strip()
            if float(rect['conf']) > TESSERACT_OCR_THRESHOLD and rect['text'] != "":
                frame_text.append(rect['text'])
        return frame_text

def frame_to_text(frame_im, last_frame_text):

    frame_text = tesseract_ocr(frame_im)

    f1_text = " ".join(frame_text)
    f2_text = " ".join(last_frame_text)
    ratio = SequenceMatcher(None, f1_text, f2_text).ratio()
    if ratio > OCR_DUP_THRESHOLD:
        return True, frame_text
    else:
        return False, frame_text
