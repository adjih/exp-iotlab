
This file documents the processing of results of experiments
(including existing datasets)

 <img src="/doc/RadioExpTool.png" align="right" alt="RadioExpTool" width="30%"/>

---------------------------------------------------------------------------

TL;DR - Quick Vizualisation of Exp. Results
===========================================

* Get this branch ``radio-exp`` of ``exp-iotlab``:

  ``git clone https://github.com/adjih/exp-iotlab.git -b radio-exp``
* Go to this directory ``tools/``

   ``cd exp-iotlab/tools``
* From [here](http://hipercom.inria.fr/IoT-LAB-dataset/), get an already parsed experiment dataset [exp-2015-02-04-23h02m50.zip](http://hipercom.inria.fr/IoT-LAB-dataset/exp-2015-02-04-23h02m50.zip) through:

   ``wget http://hipercom.inria.fr/IoT-LAB-dataset/exp-2015-02-04-23h02m50.zip``

* then: 
```
  unzip exp-2015-02-04-23h02m50.zip
  python parseRadioExp.py gui exp-2015-02-04-23h02m50
```
  (relaunch if nothing appears there seems to be a race condition somewhere)

---------------------------------------------------------------------------

Experiment Workflow
===================

[Run the experiments] -> [Raw/] -> [Parsed/] -> [GUI display]

(note: directories ``Raw``, ``Parsed`` were used only for exporting data, not
 present in any of the code, files/directories were manually moved)

---------------------------------------------------------------------------

parseRadioExp.py
================

It can do the steps [Raw/] -> [Parsed/] and [Parsed/] -> [GUI display]

*  [Raw/] -> [Parsed/]
  * ``python parseRadioExp.py merge <exp-dirname.tar.lzma>``
  * ``python parseRadioExp.py parse <exp-dirname.tar.lzma>``

*  [Parsed/] -> [GUI display]
  statistics, gui, etc:.
  * ``python parseRadioExp.py summary <exp-dirname>   # no .tar.lzma suffix``
  * ``python parseRadioExp.py gui <exp-dirname> [<exp-dirname2> ...]``

---------------------------------------------------------------------------

Interpret the results
=====================

See top of "ipython notebook radio-exp-analysis.ipynb" or of
radio-exp-analysis.pdf, to have information about how data was generated.

Older experiments are availabled
from [Parsed.zip](http://hipercom.inria.fr/IoT-LAB-dataset/Parsed.zip).

If you are curious, after downloading this file and extracting
the file, go in Parsed/
* look at the summary of the various experiments in summary.log
  * some of the experiments are older (the ones with slightly different
    format or firmware were thrown away)
  * some of the experiments have interval between packets 1ms, others 5ms
  * some (most) of the experiments explore frequencies (loop on channels), 
    some others explore radio chip power output
  * some failed, and their results are incomplete (e.g. not all channels etc.)
* you can look also in log-parsing.log to see the logs where there is 
  less/no run time errors:
  ``[in handle_irq() ERROR] invalid handle_irq 0 in RX state (radio state 0)``
  which happens at some points of the experiments, sometimes.
  Reason: unknown.

### To see the results ###
* ``python parseRadioExp.py gui <exp-dirname> [<exp-dirname2> ...]``
then in the gui:
* the top radio buttons allow to select the parameters for which one wants
  to see data: power, channel, mode

  Note: "(other)" is only used were two or more <exp-dirname> are specified;
  then the same parameter as the "previous" results are used; this allows
  to select parameters/nodes for one experiment and have the selection used
  in all the results for others experiments,
  
  See documentation in radio-exp-analysis.{ipynb,pdf} for the experiment 
  settings.
  There are 3 types of experiments:
  * transmission statistics: "rssi", "recv", "lqi" 
  * energy detection "ed"
  * so-called "errors": "radio-crc", "radio-length", "magic", etc...
 
* the top plot represents the position of the nodes of the testbed
  you can click on it to select a node.
  Depending on display parameters (top radio buttons), then bottom will 
  either display statistics related to the burst using this node as sender
  or ignore selected node.

* the bottom plot is a 3D-plot that can be rotated/scaled 
  (left/right mouse button). It displays information at each node, depending
  on "mode":
  * if energy detection "ed" is displayed, then the selected node is ignored
  and the data for one node is the average "energy detection" of the
  _sender_ when it sents its burst of many packets (there is one ed before
  each transmission)
  * if "rssi", "recv", "lqi" is displayed at bottom, then the program considers
  the data from the burst of the selected node. What is displayed is
  the average (on successfully received packets) of the _receiver_ node.
  * if a so-called "error" is selected: depending on radio button "sum error"
    at the top of the frame, either 
    . (unselected) behavior is as for "rssi", "recv", "lqi", top plot selects
    sender node.
    . (selected) the selected node is ignored and a sum of the errors over
    all sender nodes is displayed. this is because some "errors" are rare.
    

The following was discussed (2014-09-05) with Grenoble Dream Team:
* there are some Wifi access points. These are CISCO access points that
  may switch dynamically frequencies (based on channel access)
  Grenoble guys might be able to see switching during the logs
* there is some nodes which are transmitting on radio, and not present
  in testbed, these are:
  * nodes near the dev testbed (not in production) [could be switched off
    on demand]
  * failed nodes that are not answering to ping (gw), but M3 is still running
    (maybe there would be some way to turn them off ???)
* there is significantly more energy(interference) in channel 22 specifically. 
  They don't know were it comes from. It is spread all over the testbed.
* Gaetan asked: should one do exp-mean instead of arithmetic mean for rssi ?

---------------------------------------------------------------------------

Raw/* : where does it comes from ?
==================================

Running experiments (up to getting .lzma):
* run experiments: 
  * ``killall ssh`` # brutal, remove previous ssh forwarding
  * make a IoT-LAB reservation
  * run a loop like (if you want to run experiments while sleeping):
```
      while [ `date +"%H"` != "05" ] ; do 
         python RunMultiExp.py --flash conf-radio-freq.pyconf ;
         sleep 240 ;
      done
```
  * tar + lzma compress files (gain x15) semi-manually from the shell

One of the Raw/*.lzma is shorter, the experiment was made on purpose to test 
parsing code with only a few nodes, you can look at the content of .tar.lzma
with the different files

---------------------------------------------------------------------------

Parsed/* : where does it comes from ?
=====================================

```
# How the files in Parsed/ where generated

# --- First: parse all .lzma in ../Raw (and this generates directory)

(for i in ../Raw/*.lzma ; do \
   N=$(basename $i) ; \
   ln -s $i $N \
   && python parseRadioExp.py merge $N \
   && python parseRadioExp.py parse $N \
   && rm $N ; \
done ) | tee log-parsing.log

# see the errors
less -R log-parsing.log

# --- Second: create a summary of all the experiments (identify incomplete ones)
for i in exp-* ; do \
    python -c "print '*'*50, '$i'" \
    && python parseRadioExp.py summary $i ; \
done  > summary.log 2>&1
```

---------------------------------------------------------------------------

The following assumes "exp-iot-lab" master branch is in '~/ep'
and the 'branch-exp' is in '~/e'

----

Reservation:
```
cd ~/ep/tools/misc/demo
./democtl --no-cache --site grenoble plot
./democtl --site lille reserve
```

---------------------------------------------------------------------------
First exp:
==========

```
cd ~/ep/tools/misc/demo
./democtl --no-cache --site lille plot
`./democtl --site lille reserve` -d 120 -n "testFreqMap"

cd ~/e/tools
python RunMultiExp.py --flash conf-radio-freq.pyconf
```

---------------------------------------------------------------------------

Content of http://hipercom.inria.fr/IoT-LAB-dataset/
====================================================

* [Raw/*](http://hipercom.inria.fr/IoT-LAB-dataset/Raw/):
   files obtained after running and compressing some past experiments

* [Parsed/*, compressed in Parsed.zip](http://hipercom.inria.fr/IoT-LAB-dataset/Parsed.zip)
   files obtained after merging and parsing the experiment, except for the
   latest one (below)

* [exp-2015-02-04-23h02m50.zip](http://hipercom.inria.fr/IoT-LAB-dataset/exp-2015-02-04-23h02m50.zip)
   latest experiment, files obtained after 'merging' and parsing the logs

* [Analysis-IoT-LAB-Trace.pdf](http://hipercom.inria.fr/IoT-LAB-dataset/Analysis-IoT-LAB-Trace.pdf) -
   slides/presentation of the article analysing the dataset ``exp-2015-02-04-23h02m50.zip``:
   *"Lessons Learned from Large-scale Dense IEEE802.15.4 Connectivity Traces"*, Thomas Watteyne, Cedric Adjih, Xavier Vilajosana, IEEE CASE 2015, Gothenburg, Sweden, 24-28 August 2015.

* [obsolete-radio-exp-analysis.pdf](http://hipercom.inria.fr/IoT-LAB-dataset/obsolete-radio-exp-analysis.pdf):
   * a old version of some analysis 
   * a pdf version of the following file ;
   * documents how the radio experiments were made and then some specific 
     statistics were made
   * the notebook was run twice (without hack and with hack, search for "HACK:")
     to obtain and later interpret results for OPERA-OCARI (for EDF)

* obsolete-radio-exp-analysis.ipynb:

   the actual ipython notebook of the above
   run "ipython notebook obsolete-radio-exp-analysis.ipynb"

---------------------------------------------------------------------------

Reproduce published figures 
===========================

To reproduce figures from the article
"Lessons Learned from Large-scale Dense IEEE802.15.4 Connectivity Traces":

* Extract ``exp-2015-02-04-23h02m50.zip`` mentionned previous section
  in directory ``tools``

* In directory ``tools``, start ``make -f Makefile.figures``

* Wait a little bit, and have fun with the newly generated figures in directory ``analysis``

---------------------------------------------------------------------------







