#!/bin/bash

N=$1 # number of host data
M=$2 # length of conv vector
INPUT=$3 # directory/file to the input
OUTPUT_DIR=$4 # directory to store the output
K=$5 # the number of extra hosts
PEAK_N=$6 # threshold to filter out peaks

function script() {
    echo "$1" >> tmp_plot.m
}

function plot_col() {
    local factor="$(python2.7 -c "print $N + 1") / $N"
    script "cutoff = $PEAK_N * mean([$(printf "mean(a%s(:,$2))," $(seq $N))0]) * $factor;"
    for i in $(seq $N); do
        script "$(echo "$3" | sed 's/$i/'$i'/g;s/$2/'$2'/g')"
        script "y = y("$4:"length(a$i(:,1))"$5");"
        script "y = y .* (y <= cutoff) + cutoff .* (y > cutoff);"
        script "plot(a$i(:,1), y, \";$i;\");"
        script "hold on"
    done
    script "print $1.png"
    script "hold off"
}

function plot_cdf() {
    local factor="$(python2.7 -c "print $N + 1") / $N"
    script "cutoff = $PEAK_N * mean([$(printf "mean(a%s(:,$2))," $(seq $N))0]) * $factor;"
    for i in $(seq $N); do
        script "$(echo "$3" | sed 's/$i/'$i'/g;s/$2/'$2'/g')"
        script "y = y .* (y <= cutoff) + cutoff .* (y > cutoff);"
        script "cdfplot(y, \";$i;\");"
        script "hold on"
    done
    script "print $1-cdf.png"
    script "hold off"
}

function plot_col_raw() {
    plot_col "$1" "$2" 'y = a$i(:,$2);'
}

function prepare_conv_func() {
    script "conv_vec = $(python2.7 -c "print [1] * $M");"
}

function plot_col_conv() {
    plot_col "$1" "$2" 'y = conv(conv_vec/sum(conv_vec), a$i(:,$2));' "$M/2" '+'$M'/2-1'
    plot_cdf "$1" "$2" 'y = conv(conv_vec/sum(conv_vec), a$i(:,$2));' "$M/2" '+'$M'/2-1'
}

function plot_col_reg() {
    plot_col "$1" "$2" '[y, lambda] = regdatasmooth(a$i(:,1), a$i(:,$2));' 1
    plot_cdf "$1" "$2" '[y, lambda] = regdatasmooth(a$i(:,1), a$i(:,$2));' 1
}

function load_data() {
    script "pkg load data-smoothing nan"

    # load the data
    for i in $(seq $N); do
        script "a$i = load('"$OUTPUT_DIR"/"$i".data');"
    done
}

function reset_time() {
    local first_seen=$(printf "a%s(1,1)," $(seq $1))
    local mstate="first_seen = min(["$first_seen"1e300]);"
    script "$mstate"
    for i in $(seq $1); do
        script "a$i = a$i - ones(size(a$i)) * [first_seen, 0, 0; 0, 0, 0; 0, 0, 0];"
    done
}

function plot_pcap_linear() {
    local N1=$(python2.7 -c "print $N-1")
    for i in $(seq $N1); do
        local a=$(python2.7 -c "print $i+1")
        local b=$(python2.7 -c "print $i-1")
        echo $a $b
        python2.7 analyze_tcp.py "$INPUT/h$b.pcap" \
                  "10.0.1.$i" "10.0.1.$a" > "$OUTPUT_DIR/$i.data"
    done
    python2.7 analyze_tcp.py "$INPUT/e0.pcap" \
              "10.0.2.1" "10.0.2.2" > "$OUTPUT_DIR/$N.data"

    load_data
    prepare_conv_func
    reset_time $N

    plot_col_conv "$OUTPUT_DIR/RTT-conv" 2
    plot_col_conv "$OUTPUT_DIR/throughput-conv" 3
}

function plot_iperf_data() {
    for i in $(seq $N); do
        cat $IPERF_DATA | grep "^$(python2.7 -c "print $i+1")" \
            | awk '{print $2" "$3}' | sort -n > "$OUTPUT_DIR/$i.data"
    done

    load_data
    prepare_conv_func

    plot_col_conv "$OUTPUT_DIR/cwnd-conv" 2
}

rm -f tmp_plot.m
mkdir -p $OUTPUT_DIR

# plot time series graph
plot_pcap_linear

# plot_iperf_data

octave tmp_plot.m

rm -f tmp*
