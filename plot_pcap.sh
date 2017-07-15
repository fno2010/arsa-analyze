#!/bin/bash

N=$1
M=$2

function script() {
    echo "$1" >> plot_pcap.m
}

function plot_col() {
    for i in $(seq 1 $N); do
        script "$(echo "$3" | sed 's/$i/'$i'/g;s/$2/'$2'/g')"
        script "plot(a$i(:,1),y("$4:"length(a$i(:,1))"$5"));"
        script "hold on"
    done
    script "print $1.png"
    script "hold off"
}

function plot_cdf() {
    for i in $(seq 1 $N); do
        script "$(echo "$3" | sed 's/$i/'$i'/g;s/$2/'$2'/g')"
        script "cdfplot(y);"
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

rm -f plot_pcap.m

script "pkg load data-smoothing nan"

# load the data
for i in $(seq 1 $N); do
    script "a$i = load('"$i".data');"
done

# plot RTT graph
prepare_conv_func

plot_col_conv "RTT-conv" 2
plot_col_conv "throughput-conv" 3

octave plot_pcap.m

rm -f plot_pcap.m
