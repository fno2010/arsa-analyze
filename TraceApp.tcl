# Define "TraceApp" as a child class of "Application"
Class TraceApp -superclass Application

# Define (override) "init" method to create "TraceApp" object
TraceApp instproc init {args} {
        $self set bytes_ 0
        eval $self next $args
}

# Define (override) "recv" method for "TraceApp" object
TraceApp instproc recv {byte} {
        $self instvar bytes_
        set bytes_ [expr $bytes_ + $byte]
        return $bytes_
}

proc plotThroughput {id tcpSink outfile} {
    global ns

    set now [$ns now]
    set nbytes [$tcpSink set bytes_]
    $tcpSink set bytes_ 0

    set time_incr 1.0

    set throughput [expr ($nbytes * 8.0 / 1000000) / $time_incr]

    ###Print TIME throughput for  gnuplot to plot progressing on throughput
    puts  $outfile  "$id $now $throughput"

    $ns at [expr $now+$time_incr] "plotThroughput $id $tcpSink  $outfile"
}
