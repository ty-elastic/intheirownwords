import argparse
import prj
import job
import api_import_server
import storage

def main():
    storage.clean_temp_folders()

    api_import_server.start()
    job.start()


main()