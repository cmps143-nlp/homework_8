

import os
import sys

if __name__  ==  '__main__' :
    result_file = sys.argv[1]
    log_file = sys.argv[2]
    #for filename in os.listdir("."):

    # read result file
    lines = []
    with open(result_file, 'r') as infile:
        for line in infile:
            if line.startswith("AVERAGE"):
                lines.append(line)

    # output to log
    with open(log_file, 'a') as outfile:
        outfile.write('\nFINAL RESULTS\n')
        for line in lines:
            outfile.write(line)
        outfile.write('\n')
        outfile.write('*' * 70 + '\n')
