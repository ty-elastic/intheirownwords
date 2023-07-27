import project
import video
import itt
import stt
import split
import es_clauses
import time
import argparse

def main():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("input", help="input file")
    parser.add_argument("source_url", help="original video url")
    parser.add_argument("date", help="date")
    parser.add_argument("title", help="title")
    parser.add_argument("kind", help="kind (webinar)")
    parser.add_argument("origin", help="origin (elastic)")
    parser.add_argument("--disable_write", action='store_true', default=False, help="disable writing (test mode)")
    args = parser.parse_args()
    config = vars(args)
    print(config)
    process(args.input, args.source_url, args.title, args.date, args.kind, args.origin, args.disable_write == False)

def process(input, source_url, title, date, kind, origin, enable_write):
    start_time = time.time()

    project = project.create_project(input, source_url, title, date, kind, origin, enable_write)
    project.conform_audio(project)

    video.detect_scenes(project)
    itt.frames_to_text(project)

    segments = stt.speech_to_text(project)

    split.split(project, segments)

    print(project)
    if project['enable_write']:
        es_clauses.add_clauses(project)

    end_time = time.time()
    print (end_time - start_time)
    
    project.delete_project(project)

main()