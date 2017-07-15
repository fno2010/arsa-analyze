#!/usr/bin/env python2.7

def analyze_tcp(f):
    conn = {}
    ts = {}
    for line in f:
        data = line.split(' ')
        timestamp = float(data[0])
        sport, dport = int(data[1]), int(data[2])
        nxtseq, ack = int(data[3]), int(data[4])
        window_size, datalen = int(data[5]), int(float(data[6]))

        port = dport if sport == 5201 else sport

        if not port in conn:
            conn[port] = {'ts': {}}
            ts[port] = []
        if port == sport: # sender side
            if nxtseq == 0: # no data in packet
                continue
            conn[port]['cwnd'] = window_size
            conn[port]['ts'][nxtseq] = (timestamp, datalen) # record the sending time
        else: # receiver side
            if ack not in conn[port]['ts']:
                continue
            stimestamp, datalen = conn[port]['ts'][ack]
            rtt = timestamp - stimestamp
            throughput = datalen / rtt
            ts[port] += [(timestamp, rtt, throughput, conn[port]['cwnd'])]

    tsid = reduce(lambda x, y: x if len(ts[x]) > len(ts[y]) else y, ts.keys())
    for timestamp, rtt, throughput, cwnd in ts[tsid]:
        print timestamp, rtt, throughput, cwnd


if __name__ == '__main__':
    import sys
    with open(sys.argv[1]) as f:
        analyze_tcp(f)
