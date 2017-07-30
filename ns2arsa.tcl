#Create a simulator object
set ns [new Simulator]

#Define a 'finish' procedure
proc finish {} {
        exit 0
}

source arsa/TraceApp.tcl

source arsa/clos.tcl

#Run the simulation
$ns run
