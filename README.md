# TCP Congestion Control Simulation

## Use docker-compose

### Simple Linear Topology Test

``` sh
docker-compose run --rm -e MININET_SCRIPT_OPTIONS='3 --test simple --duration 120' mininet
```

### Mixed TCP Flows Test on a Single Bottleneck Link

``` sh
docker-compose run --rm -e MININET_SCRIPT_OPTIONS='0 --test single-mix --duration 240 --json /data/examples/single.json' mininet
```

### Mixed TCP Flows Test on a Linear Topology

``` sh
docker-compose run --rm -e MININET_SCRIPT_OPTIONS='0 --test linear-mix --duration 240 --json /data/examples/linear.json' mininet
```

## Use local mininet

``` sh
sudo python2.7 simulation.py --test simple 3 --duration 150 --tcp vegas || sudo mn -c
```

## Data collection and processing

### Copy the data to input directory

``` sh
mkdir -p input/vegas
mv *.pcap input/vegas
```

Or you can use `scp` or `rsync` if the Mininet is running on a different machine.

### Plot the data

``` sh
./arsaplot.sh 3 20 data/pcap/cubic output/cubic 1 2
```

The parameter list:
- number of flows
- number of data to calculate an average (as a smoothing technique)
- input directory (where the pcap files are)
- output directory (where the plots will be)
- number of extra flows (long flows), just set 1
- cut-off coefficient
