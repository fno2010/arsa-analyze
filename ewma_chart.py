#!/usr/bin/env python

import sys
import pandas
from matplotlib.pyplot import plot, savefig, figure

DEFAULT_EWMA_PARAMS = {'com': 0.5}

USAGE = """
%s <csv_file> [ewma_params]

The format of ewma_params like: com=0.5 span=1
Accepted ewma_params: com, span, halflife, min_periods

The format of the csv_file should be whitespace separated
csv with the header line "testcase time window".

For example:

testcase time window
2 0.1 19.8
2 0.2 31.1
2 0.3 42.4
2 0.4 53.7
2 0.5 36.8
2 0.6 21.2
""" % (sys.argv[0])

if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.stdout.write(USAGE)
        sys.exit(-1)

    filename = sys.argv[1]
    data = pandas.read_csv(filename, sep='\s+')
    testcases = set(data['testcase'])

    figure(figsize=(12, 4), dpi=300)

    ewma = True
    if len(sys.argv) > 2:
        if '-noewma' in sys.argv[2:]:
            ewma = False
        ewma_params = {x.split('=')[0]: float(x.split('=')[1])
                       for x in sys.argv[2:] if not x.startswith('-')}
    else:
        ewma_params = DEFAULT_EWMA_PARAMS

    for t in testcases:
        data_t = data[data['testcase'] == t]
        time = data_t['time']
        window_size = data_t['window']
        if ewma:
            window_size = window_size.ewm(**ewma_params).mean()
        plot(time, window_size)

    savefig(''.join(filename.split('.')[:-1]) + '.png')
