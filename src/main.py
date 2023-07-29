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
    parser.add_argument("--disable_write", action='store_true', default=False, help="disable writing (test mode)")
    parser.add_argument("--disable_scenes", action='store_true', default=False, help="disable scene detect")
    args = parser.parse_args()
    config = vars(args)
    print(config)
    prj.process(args.input, args.source_url, args.title, args.date, args.kind, args.origin, args.disable_write == False, args.disable_scenes == False)

main()