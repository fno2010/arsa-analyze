#Create a simulator object
set ns [new Simulator]

#Define a 'finish' procedure
proc finish {} {
        exit 0
}

source TraceApp.tcl

source clos.tcl

#Run the simulation
$ns run
