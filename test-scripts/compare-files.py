import filecmp
import sys
import argparse

def compare_files(resultfile, expectedfile, message):
    result=filecmp.cmp(resultfile, expectedfile)
    if result:
        print(f"PASS: {message}", file=sys.stderr)
        return True
    else:
        print(f"FAIL: {message} [Try: sdiff {resultfile} {expectedfile}]", file=sys.stderr)
        return False

def config_args(): # add --anonymize
    parser = argparse.ArgumentParser(description='Redact call transcriptions or chat logs.')
    parser.add_argument('resultfile', help='The test being performed')
    parser.add_argument('expectfile', help='The expected result file')
    parser.add_argument('message',    help='The result file to test')
    
    _args=parser.parse_args()
    return _args
    
if __name__ == "__main__":
    # get command line params.
    args = config_args()
   
    try:
        compare_files(args.resultfile,args.expectfile,args.message)
    except Exception as e:
        print(f"ERROR. Terminating compare-files with error:  {e}",file=sys.stderr)
        