#!/bin/bash

N=$1 # number of host data
M=$2 # length of conv vector
IPERF_DATA=$3
OUTPUT_PREFIX=$4

function script() {
    echo "$1" >> tmp_plot.m
}

function plot_col() {
    for i in $(seq $N); do
        script "$(echo "$3" | sed 's/$i/'$i'/g;s/$2/'$2'/g')"
        script "plot(a$i(:,1),y("$4:"length(a$i(:,1))"$5"), \";$i;\");"
        script "hold on"
    done
    script "print $1.png"
    script "hold off"
}

function plot_cdf() {
    for i in $(seq $N); do
        script "$(echo "$3" | sed 's/$i/'$i'/g;s/$2/'$2'/g')"
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
        script "a$i = load('"$i".data');"
    done
}

function plot_pcap_data() {
    load_data
    prepare_conv_func

    plot_col_conv "RTT-conv" 2
    plot_col_conv "throughput-conv" 3
}

function plot_iperf_data() {
    for i in $(seq $N); do
        cat $IPERF_DATA | grep "^$(python2.7 -c "print $i+1")" \
            | awk '{print $2" "$3}' | sort -n > $i.data
    done

    load_data
    prepare_conv_func

    plot_col_conv "$OUTPUT_PREFIX-cwnd-conv" 2
}

rm -f tmp_plot.m

# plot RTT graph
# plot_pcap_data

plot_iperf_data

octave tmp_plot.m

rm -f tmp*
