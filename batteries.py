import os 
import shutil
import uuid
import ffmpeg
import s3
from datetime import datetime
import re

SAMPLE_RATE = 16000

def strip_field_arrays(fields):
    out = {}
    for key in fields:
        out[key] = fields[key][0]
    return out

def delete_project(project):
    shutil.rmtree( project['path'], ignore_errors=True)

def conform_audio(project):
    project['conformed_audio'] = project['path'] + "/" + project['id'] + ".wav"
    try:
        # This launches a subprocess to decode audio while down-mixing and resampling as necessary.
        # Requires the ffmpeg CLI and `ffmpeg-python` package to be installed.
        out, _ = (
            ffmpeg.input(project['input'], threads=0)
            .output(project['conformed_audio'], acodec="pcm_s16le", ac=1, ar=SAMPLE_RATE)
            .run(cmd=["ffmpeg", "-nostdin"], capture_stdout=True, capture_stderr=True)
        )
        return project['conformed_audio']
    except ffmpeg.Error as e:
        raise RuntimeError(f"Failed to load audio: {e.stderr.decode()}") from e

def create_project(input, local, title, date, kind, origin, enable_write):

    project_id = str(uuid.uuid4())
    prj_path = os.path.join(os.getenv('PROJECT_DIR'), project_id)
    shutil.rmtree(prj_path, ignore_errors=True)
    os.makedirs(prj_path)

    path_file, extension = os.path.splitext(input)
    media_path = os.path.join(prj_path, project_id + extension)
    shutil.copyfile(input, media_path)

    project = {
        "id": project_id,
        "input": media_path,
        "title": title,
        "date": datetime.strptime(date, '%m/%d/%y'),
        "path": prj_path,
        "kind": kind,
        "origin": origin,
        "enable_write": enable_write
    }

    project['media_url'] = s3.upload_file(project, None, media_path)
    return project

#create_prj("/hack/test/otel.mp4", True)

def escape_markdown(text: str, version: int = 1, entity_type: str = None) -> str:
    """
    Helper function to escape telegram markup symbols.

    Args:
        text (:obj:`str`): The text.
        version (:obj:`int` | :obj:`str`): Use to specify the version of telegrams Markdown.
            Either ``1`` or ``2``. Defaults to ``1``.
        entity_type (:obj:`str`, optional): For the entity types ``PRE``, ``CODE`` and the link
            part of ``TEXT_LINKS``, only certain characters need to be escaped in ``MarkdownV2``.
            See the official API documentation for details. Only valid in combination with
            ``version=2``, will be ignored else.
    """
    if int(version) == 1:
        escape_chars = r'_*`['
    elif int(version) == 2:
        if entity_type in ['pre', 'code']:
            escape_chars = r'\`'
        elif entity_type == 'text_link':
            escape_chars = r'\)'
        else:
            escape_chars = r'_*[]()~`>#+-=|{}.!'
    else:
        raise ValueError('Markdown version must be either 1 or 2!')

    text = text.replace("$", "").strip()

    return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', text)