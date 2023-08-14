import argparse
import prj

def main():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("input", help="input file")
    parser.add_argument("source_url", help="original video url")
    parser.add_argument("date", help="date")
    parser.add_argument("title", help="title")
    parser.add_argument("kind", help="kind (webinar)")
    parser.add_argument("origin", help="origin (elastic)")
    parser.add_argument("--save_frames", action='store_true', default=False, help="enable frame storage")
    args = parser.parse_args()
    config = vars(args)
    print(config)
    prj.process(args.input, args.source_url, args.title, args.date, args.kind, args.origin, args.save_frames == True)

main()