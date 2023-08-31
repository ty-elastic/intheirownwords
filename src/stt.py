import whisperx
import gc 
import os
import torch

import stt_diarize
import es_voices

DEVICE = "cuda" 
BATCH_SIZE = 16 # reduce if low on GPU mem
COMPUTE_TYPE = "float16" # change to "int8" if low on GPU mem (may reduce accuracy)

def speech_to_text(project):

    # 1. Transcribe with original whisper (batched)
    model = whisperx.load_model("large-v2", DEVICE, compute_type=COMPUTE_TYPE, asr_options={"word_timestamps": False}, language='en')
    audio = whisperx.load_audio(project['conformed_audio'])
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

    # 3. Assign speaker labels
    diarize_model = stt_diarize.DiarizationPipeline(use_auth_token=os.getenv('HF_TOKEN'), device=DEVICE)

    # add min/max number of speakers if known
    diarize_segments, embeddings = diarize_model(project['conformed_audio'])
    # diarize_model(audio_file, min_speakers=min_speakers, max_speakers=max_speakers)

    # delete model if low on GPU resources
    del diarize_model
    gc.collect()
    torch.cuda.empty_cache()
    print("after diarize_model")

    speakers = {}
    for i, embedding in enumerate(embeddings):
        speaker_id = es_voices.lookup_speaker(embedding)
        if speaker_id == None:
            for j, speaker in enumerate(diarize_segments['speaker']):
                if speaker == f"SPEAKER_{i:02}":
                    #print("FOUND")
                    speaker_id = es_voices.add_speaker(project, embedding, project['media_url'], diarize_segments['start'][j], diarize_segments['end'][j])
                    break
        speakers[f"SPEAKER_{i:02}"] = speaker_id
    # print(speakers)

    result = stt_diarize.assign_word_speakers(diarize_segments, result, speakers)
    # print(diarize_segments)
    # print(result["segments"]) # segments are now assigned speaker IDs


    #print(result["segments"])
    return result["segments"]