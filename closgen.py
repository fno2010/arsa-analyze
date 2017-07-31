#!/usr/bin/env python2.7

def generate_flows(N, K, conf_file, matrix_file, multi_tcp=False):
    from random import sample
    import json

    flows = []
    K2 = K / 2

    L = K * K2 * K2
    D1 = K2 * K2
    D2 = K2
    ports = list(range(L))
    breakdown = lambda p: [p / D1, p % D1 / D2, p % D2]
    A = []
    for n in range(N):
        s, d = sample(ports, 2)
        a = [0] * L * 2
        a[s] = a[d + L] = 1
        A += [a]
        s, d = breakdown(s), breakdown(d)
        if multi_tcp:
            flows += [{'tcp': 'vegas' if s[2] % 2 else 'reno', 'from': s, 'to': d}]
        else:
            flows += [{'tcp': 'vegas', 'from': s, 'to': d}]

    with open(conf_file, 'w') as f:
        json.dump(flows, f)

    with open(matrix_file, 'w') as f:
        for i in range(len(A)):
            f.write(' '.join(map(str, A[i])) + '\n')
    return flows

def simulate_flows(K, flows, conf_file):
    import simulation
    simulation.simulate([
        '--test', 'clos',
        '--duration', '240',
        '--delay', '100us',
        '--json', conf_file,
        str(K)
    ])

def analyze_flows(flows, throughput_file):
    import re
    throughput = []
    for i in range(len(flows)):
        with open('%d.log' % i, 'r') as f:
            for line in f.readlines():
                if re.search('sender', line) is None:
                    continue

                m = re.search('(\d+) ([MmKk])bits/sec', line)
                v, u = float(m.group(1)), m.group(2).upper()
                unit = 10**9 if u == 'G' else 10**6 if u == 'M' else 10**3
                throughput += [str(v * unit) + '\n']

    with open(throughput_file, 'w') as f:
        f.writelines(throughput)

if __name__ == '__main__':
    import sys
    N, K, conf_file, matrix_file, throughput_file = sys.argv[1:6]
    N, K = int(N), int(K)

    flows = generate_flows(N, K, conf_file, matrix_file)
    simulate_flows(K, flows, conf_file)
    analyze_flows(flows, throughput_file)
