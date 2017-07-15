#!/bin/bash

FILE=$1
N=$2
TITLE=$3

rm -rf tmp
cp $FILE "tmp"

rm -rf tmp_plot_cwnd.m

for i in $(seq 2 $(python -c "print("$N"+1)")); do
	cat tmp | grep '^'$i > "tmp_data$i"
	echo "d$i = load('tmp_data"$i"');" >> tmp_plot_cwnd.m
	echo "x$i = d$i(:,2);" >> tmp_plot_cwnd.m
	echo "y$i = d$i(:,3);" >> tmp_plot_cwnd.m
	echo "hold on" >> tmp_plot_cwnd.m
	echo "plot(x$i, y$i, \";$i;\")" >> tmp_plot_cwnd.m
	rm -f _tmp
done

echo "legend()" >> tmp_plot_cwnd.m

echo "print $TITLE.png" >> tmp_plot_cwnd.m

octave tmp_plot_cwnd.m 2>/dev/null || echo "Capture plot error"

rm -f tmp*

echo "Finished"
