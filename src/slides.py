
import os 
import s3

from typing import Optional
from typing import List, Tuple, Dict

from scenedetect import open_video, open_video, VideoStream
from scenedetect.frame_timecode import FrameTimecode
from scenedetect.scene_manager import SceneManager
from scenedetect.platform import (get_and_create_path, get_cv2_imwrite_params)
from slide_change_detector import SlideChangeDetector

import csv
import pytesseract
from difflib import SequenceMatcher

import cv2
import numpy as np

import time

SCENE_THRESHOLD=8.0
FRAME_SKIP=149

TESSERACT_OCR_THRESHOLD = 85
OCR_DUP_THRESHOLD = 0.75
OCR_TOO_MANY_RECTS_THRESHOLD = 100
OCR_IGNORE_LOWER = 0.1

IMAGE_FORMAT = "jpg"
IMAGE_COMPRESSION = 90

def detect(
    video_path: str,
) -> List[Tuple[FrameTimecode, FrameTimecode]]:

    video = open_video(video_path)
    scene_manager = SceneManager()
    scene_manager.add_detector(SlideChangeDetector(threshold=SCENE_THRESHOLD))
    scene_manager.detect_scenes(
        video=video,
        show_progress=False,
        frame_skip=FRAME_SKIP
    )
    return scene_manager.get_scene_list(start_in_scene=False)


def detect_slides(project):

    start_time = time.time()
    scene_list = detect(project['input'])
    print(f"scene_detect: {time.time() - start_time}")

    video = open_video(project['input'])

    frames_path = None
    if project['save_frames']:
        frames_path = os.path.join(project['path'], "frames")
        os.makedirs(frames_path)

    start_time = time.time()
    deduped_scene_list = dedup_scene_list(scene_list, video, output_dir=frames_path)
    print(f"dedup/OCR: {time.time() - start_time}")
          
    for i, scene in enumerate(deduped_scene_list):
        scene_record = {'id': i, 'frame_num': scene['frame_num'], 'frame_text': scene['frame_text']}
        if 'frame_file' in scene:
            filepath = frames_path + "/" + scene['frame_file']
            frame_url = s3.upload_file(project, 'frames', filepath)
            scene_record['frame_url'] = frame_url

        scene_record['start'] = scene['start']
        scene_record['end'] = scene['end']
        #print(scene_record)
        project['scenes'].append(scene_record)
    #print(project['scenes'])

def dedup_scene_list(scene_list: List[Tuple[FrameTimecode, FrameTimecode]],
                video: VideoStream,
                output_dir: Optional[str] = None) -> Dict[int, List[str]]:
 
    imwrite_param = [get_cv2_imwrite_params()[IMAGE_FORMAT], IMAGE_COMPRESSION]

    video.reset()

    framerate = scene_list[0][0].framerate

    NUM_IMAGES = 1
    timecode_list = [
        [
            FrameTimecode(int(f), fps=framerate) for f in [
                                                                                               # middle frames
                a[len(a) // 2]
                                                                                               # for each evenly-split array of frames in the scene list
                for j, a in enumerate(np.array_split(r, NUM_IMAGES))
            ]
        ] for i, r in enumerate([
                                                                                               # pad ranges to number of images
            r if 1 + r[-1] - r[0] >= NUM_IMAGES else list(r) + [r[-1]] * (NUM_IMAGES - len(r))
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
    current_scene = None
    for i, scene_timecodes in enumerate(timecode_list):
        for image_timecode in scene_timecodes:
            video.seek(image_timecode)
            frame_im = video.read()
            if frame_im is not None:
                dup, last_frame_text = frame_to_text(frame_im, last_frame_text)
                if dup is False:
                    if current_scene != None:
                        deduped_scene_list.append(current_scene)
                    if len(last_frame_text) > 0:
                        current_scene = {"start":scene_list[i][0].get_seconds(), "end":scene_list[i][1].get_seconds(), "frame_num": image_timecode.get_frames(), "frame_text": last_frame_text}
                        if output_dir is not None:
                            file_path = f"{i + 1}-{image_timecode.get_frames()}.{IMAGE_FORMAT}"
                            cv2.imwrite(get_and_create_path(file_path, output_dir), frame_im, imwrite_param)
                            current_scene["frame_file"] = file_path
                else:
                    #print("dup frame, extend")
                    if current_scene != None:
                        current_scene["end"] = scene_list[i][1].get_seconds()
            else:
                break
    if current_scene is not None:
        deduped_scene_list.append(current_scene)

    return deduped_scene_list

def tesseract_ocr(frame_im):
        img_gray = cv2.cvtColor(frame_im, cv2.COLOR_BGR2GRAY)
        thresh_img = cv2.threshold(img_gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]

        text_frames = pytesseract.image_to_data(thresh_img, lang='eng')

        frame_text = []
        reader = csv.DictReader(text_frames.split("\n"), delimiter="\t", quoting=csv.QUOTE_NONE)
        rects = [r for r in reader]
        height, width = frame_im.shape[:2]

        block_num = -1
        block_text = []
        block_conf = []
        block_top = 0

        for rect in rects:
            if int(rect['block_num']) != block_num and block_num != -1:

                #print(f"block_top={block_top}, block_conf={np.mean(block_conf)}, len(block_text)={len(block_text)}, block_text={block_text}")
                if len(block_text) > 0 and len(block_text) < OCR_TOO_MANY_RECTS_THRESHOLD and block_top < height-(height * OCR_IGNORE_LOWER) and np.mean(block_conf) > TESSERACT_OCR_THRESHOLD:
                    frame_text.append(" ".join(block_text))

                block_text = []
                block_conf = []
                block_top = 0

            if float(rect['conf']) != -1 and rect['text'].strip() != "":
                block_text.append(rect['text'].strip())
                #print(float(rect['conf']))
                block_conf.append(float(rect['conf']))
                if int(rect['top']) > block_top:
                    block_top = int(rect['top'])
            block_num = int(rect['block_num'])

        #print(f"block_top={block_top}, block_conf={np.mean(block_conf)}, len(block_text)={len(block_text)}, block_text={block_text}")
        if len(block_text) > 0 and len(block_text) < OCR_TOO_MANY_RECTS_THRESHOLD and block_top < height-(height * OCR_IGNORE_LOWER) and np.mean(block_conf) > TESSERACT_OCR_THRESHOLD:
            frame_text.append(" ".join(block_text))

        #print(frame_text)
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
