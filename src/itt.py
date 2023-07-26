import pytesseract
import csv

TESSERACT_CONFIDENCE_THRESHOLD = 80

def frames_to_text(project):
    for scene in project['scenes']:
        text_frames = pytesseract.image_to_data(scene['frame_path'], lang='eng')
        scene['frame_text'] = []
        reader = csv.DictReader(text_frames.split("\n"), delimiter="\t", quoting=csv.QUOTE_NONE)
        rects = [r for r in reader]
        for rect in rects:
            rect['text'] = rect['text'].strip()
            if float(rect['conf']) > TESSERACT_CONFIDENCE_THRESHOLD and rect['text'] != "":
                scene['frame_text'].append(rect['text'])
        #print(scene['frame_text'])