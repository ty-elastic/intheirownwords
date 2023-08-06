import numpy as np
import pandas as pd
from pyannote.audio import Pipeline
from typing import Optional, Union
import torch

class DiarizationPipeline:
    def __init__(
        self,
        model_name="pyannote/speaker-diarization@2.1",
        use_auth_token=None,
        device: Optional[Union[str, torch.device]] = "cpu",
    ):
        print("WAITWAIT")
        if isinstance(device, str):
            device = torch.device(device)
        print("WAITWAIT2", use_auth_token, device, model_name)
        self.model = Pipeline.from_pretrained(model_name, use_auth_token=use_auth_token).to(device)
        print("DONE1")

    def __call__(self, audio, min_speakers=None, max_speakers=None):
        print("CALL")

        segments, embeddings = self.model(audio, min_speakers=min_speakers, max_speakers=max_speakers, return_embeddings=True)

        diarize_df = pd.DataFrame(segments.itertracks(yield_label=True))
        diarize_df['start'] = diarize_df[0].apply(lambda x: x.start) 

        diarize_df['end'] = diarize_df[0].apply(lambda x: x.end)
        diarize_df.rename(columns={2: "speaker"}, inplace=True)

        print("DONE2")

        #print(diarize_df)
        return diarize_df, embeddings


def assign_word_speakers(diarize_df, transcript_result, speakers, fill_nearest=False):
    transcript_segments = transcript_result["segments"]
    for seg in transcript_segments:
        # assign speaker to segment (if any)
        diarize_df['intersection'] = np.minimum(diarize_df['end'], seg['end']) - np.maximum(diarize_df['start'], seg['start'])
        diarize_df['union'] = np.maximum(diarize_df['end'], seg['end']) - np.minimum(diarize_df['start'], seg['start'])
        # remove no hit, otherwise we look for closest (even negative intersection...)
        if not fill_nearest:
            dia_tmp = diarize_df[diarize_df['intersection'] > 0]
        else:
            dia_tmp = diarize_df
        if len(dia_tmp) > 0:
            # sum over speakers
            speaker = dia_tmp.groupby("speaker")["intersection"].sum().sort_values(ascending=False).index[0]
            seg["speaker"] = speaker
            seg["speaker_id"] = speakers[speaker]
        
        # assign speaker to words
        if 'words' in seg:
            for word in seg['words']:
                if 'start' in word:
                    diarize_df['intersection'] = np.minimum(diarize_df['end'], word['end']) - np.maximum(diarize_df['start'], word['start'])
                    diarize_df['union'] = np.maximum(diarize_df['end'], word['end']) - np.minimum(diarize_df['start'], word['start'])
                    # remove no hit
                    if not fill_nearest:
                        dia_tmp = diarize_df[diarize_df['intersection'] > 0]
                    else:
                        dia_tmp = diarize_df
                    if len(dia_tmp) > 0:
                        # sum over speakers
                        speaker = dia_tmp.groupby("speaker")["intersection"].sum().sort_values(ascending=False).index[0]
                        word["speaker"] = speaker
                        word["speaker_id"] = speakers[speaker]
        
    return transcript_result            


class Segment:
    def __init__(self, start, end, speaker=None):
        self.start = start
        self.end = end
        self.speaker = speaker
