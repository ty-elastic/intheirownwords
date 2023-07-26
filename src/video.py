from scenedetect import detect, ContentDetector, open_video, save_images
import os 
import s3

SCENE_THRESHOLD=20.0

def detect_scenes(project):

    frames_path = os.path.join(project['path'], "frames")
    os.makedirs(frames_path)
    project['frames_path'] = frames_path

    scene_list = detect(project['input'], ContentDetector(threshold=SCENE_THRESHOLD))
    video = open_video(project['input'])
    save_images(scene_list, video, num_images=3, image_extension='jpg', encoder_param=90, image_name_template='$SCENE_NUMBER-$IMAGE_NUMBER', output_dir=frames_path, show_progress=False, video_manager=None)
    # assume last image is the most complete in slide build

    project['scenes'] = []
    for i, scene in enumerate(scene_list):
        frame_num = i+1
        filepath = frames_path + "/" + f"{frame_num:03}-03" + ".jpg"
        frame_url = s3.upload_file(project, 'frames', filepath)
        scene_record = {'frame_path': filepath, 'frame_num': frame_num, 'frame_url': frame_url}
        scene_record['start'] = scene[0].get_seconds()
        scene_record['end'] = scene[1].get_seconds()
        project['scenes'].append(scene_record)
