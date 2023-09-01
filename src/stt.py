import whisperx
import gc 
import os
import torch
import ffmpeg 
import math
import pandas as pd

import stt_diarize
import es_voices

DEVICE = "cuda" 
BATCH_SIZE = 16 # reduce if low on GPU mem
COMPUTE_TYPE = "float16" # change to "int8" if low on GPU mem (may reduce accuracy)

# 30min
SPLIT_VIDEOS_SECS = 30*60
SAMPLE_RATE = 16000

def conform_audio(project, i=0, start=0, stop=-1):
    
    try:
        if stop == -1:
            path = project['path'] + "/" + project['id'] + ".wav"
            out, _ = (
                ffmpeg.input(project['input'], threads=0)
                .output(path, acodec="pcm_s16le", ac=1, ar=SAMPLE_RATE)
                .run(cmd=["ffmpeg", "-nostdin"], capture_stdout=True, capture_stderr=True)
            )
        else:
            path = project['path'] + "/" + project['id'] + "." + str(i) + ".wav"
            out, _ = (
                ffmpeg.input(project['input'], threads=0, ss=start, to=stop)
                .output(path, acodec="pcm_s16le", ac=1, ar=SAMPLE_RATE)
                .run(cmd=["ffmpeg", "-nostdin"], capture_stdout=True, capture_stderr=True)
            )
        return path
    except ffmpeg.Error as e:
        raise RuntimeError(f"Failed to load audio: {e.stderr.decode()}") from e

def diarize(stt_segments, project):

    end_time = stt_segments["segments"][len(stt_segments["segments"])-1]['end']
    audio_chunks = math.ceil(end_time / SPLIT_VIDEOS_SECS)
    #print(audio_chunks)

    _diarize_segments = []

    start = 0
    for i in range(audio_chunks):

        # 3. Assign speaker labels
        diarize_model = stt_diarize.DiarizationPipeline(use_auth_token=os.getenv('HF_TOKEN'), device=DEVICE)

        # print(f"start={start}, end={start+SPLIT_VIDEOS_SECS}")
        conformed_audio = conform_audio(project, i, start, start+SPLIT_VIDEOS_SECS)

        # add min/max number of speakers if known
        __diarize_segments, embeddings = diarize_model(conformed_audio, start)
        # diarize_model(audio_file, min_speakers=min_speakers, max_speakers=max_speakers)

        # print("hi")
        # print(len(__diarize_segments))
        # print(len(embeddings))

        speaker_id_map = {}
        for i, embedding in enumerate(embeddings):
            speaker_id = es_voices.lookup_speaker(embedding)
            if speaker_id == None:
                for j, speaker in enumerate(__diarize_segments['speaker']):
                    if speaker == f"SPEAKER_{i:02}":
                        #print("FOUND")
                        speaker_id = es_voices.add_speaker(project, embedding, project['media_url'], __diarize_segments['start'][j], __diarize_segments['end'][j])
                        break
            speaker_id_map[f"SPEAKER_{i:02}"] = speaker_id

        # apply labels
        speakers_ids = []
        for speaker in __diarize_segments['speaker']:
            speakers_ids.append(speaker_id_map[speaker])

        df2 = __diarize_segments.assign(speaker_id=speakers_ids)
        _diarize_segments.append(df2)

        # delete model if low on GPU resources
        del diarize_model
        gc.collect()
        torch.cuda.empty_cache()
        
        start = start+SPLIT_VIDEOS_SECS

    diarize_segments = pd.concat(_diarize_segments)
    # print(diarize_segments)
    return diarize_segments

def speech_to_text(project):

    conformed_audio = conform_audio(project)

    # 1. Transcribe with original whisper (batched)
    model = whisperx.load_model("large-v2", DEVICE, compute_type=COMPUTE_TYPE, asr_options={"word_timestamps": False}, language='en')
    audio = whisperx.load_audio(conformed_audio)
    result = model.transcribe(audio, batch_size=BATCH_SIZE, language='en')
    #print(result["segments"]) # before alignment

    # delete model if low on GPU resources
    del model
    gc.collect()
    torch.cuda.empty_cache()
    print("after transcribe")

    # 2. Align whisper output
    model_a, metadata = whisperx.load_align_model(language_code=result["language"], device=DEVICE)
    result = whisperx.align(result["segments"], model_a, metadata, audio, DEVICE, return_char_alignments=False)

    #print(result["segments"]) # after alignment

    # delete model if low on GPU resources
    del audio
    del model_a
    del metadata
    gc.collect()
    torch.cuda.empty_cache()
    print("after align")

    diarize_segments = diarize(result, project)
    print("after diarize_model")

    result = stt_diarize.assign_word_speakers(diarize_segments, result)
    # print(diarize_segments)
    # print(result["segments"]) # segments are now assigned speaker IDs

    #print(result["segments"])
    return result["segments"]