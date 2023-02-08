# Replication Package

This replication package includes all the artefacts in Themis+, i.e., the instrumented bugs and their bug automata, the source code of DDroid, and the app instrumentation tool ([DDroid-instrumentator](https://github.com/DDroid-Android/Android_Instrumentation)).


Themis+ is a benchmark suite, enhanced by DDroid (an automata-based trace analysis approach) for aiding diagnosing automated GUI testing tools for Android against the missed bugs. Specifically, it helps find the clues of potential tool weaknesses on the basis of three automata-based coverage metrics. Themis+ is build on top of Themis, a representative benchmark suite of real-world Android app bugs.

<div align="center">
    <img src="./figures/workflow.png" width="70%"/>
</div>

## 1. Contents of Themis+

Themis+ contains 47 real-world bugs from Themis.

The directory structure of Themis+ is as follows:

    Themis+
        |
        |--- ddroid-core: the script to match the logged event traces against the bug automaton to compute the three coverage metrics
            |
            |--- templates: templates for visualizing Themis+'s clues
                |
                |--- basetmpl.html
                |--- resulttmpl.html
                |--- summarytmpl.html
                |
            |--- analyze.py: the script analyzing the event logs
            |--- convert.py: the script converting one .jff file to .json file
            |--- dfa.py: the script defining the DFA in python class format
            |--- display.py: the script for display Themis+'s clues
            |--- dtypes.py: the script defining data structures or classes required in DDroid
            |--- error.py: the script defining the expection types
            |--- main.py: the main script to run automaton-based trace analysis (DDroid)
            |--- utils.py: the script defining some auxiliary functions
        |
        |--- scripts:                    scripts for running testing tools (borrowed from Themis) and analyzing the testing results 
            |
            |--- *themis.py*:            the main script for deploying different GUI testing tools on the instrumeted apps to log relevant event traces     
            |
            |--- check_crash.py:         the script to check whether a tool find the bugs.
            |
            |--- run_monkey.sh           the internal shell script to run Monkey
            |--- run_ape.sh              the internal shell script to run Ape
            |--- run_humanoid.sh         the internal shell script to run Humanoid
            |--- run_qtesting.sh         the internal shell script to run Q-testing
            |--- run_combodroid.sh       the internal shell script to run Combodroid
            |--- run_weighted.sh         the internal shell script to run Stoat (its weighted strategy)
            |--- run_wetest.sh           the internal shell script to run WCTester
            |--- run_fastbot.sh          the internal shell script to run FasttBot
            |
        |--- app_1:                            The bugs collected from app_1.
            |  
            | --- xxx-NFA.jff                 The epsilon-NFA for the bug with id xxx
            | --- configuration-xxx.json      The configuration file for the bug with id xxx
            | --- crash_stack_xxx.txt         The crash trace for the bug with id xxx
            | --- instrumented-xxx.apk        The instrumented APK for the bug with id xxx
            | --- script-xxx.py               The bug-triggering trace in the form of uiautomator script for the bug with id xxx
            | --- video-xxx.mp4               The bug-reproducing video for the bug with id xxx
        |
        |--- app_2:                            The bugs collected from app_2.
        |
        |--- ...
        |
        |--- app_N                             The bugs collected from app_n.

## 2. Instructions for using Themis+

Before using Themis+, you need to install Android SDK and emulators. Then you can follow the steps below to run Themis+.

**Step 1. open a terminal and switch to the scripts directory**

```
cd scripts/
```

**Step 2. run Monkey on one target bug for 6 hours**

```
python3 themis.py --no-headless --avd Android7.1 --apk ../ActivityDiary/instrumented-Scarlet-Notes-#114.apk --time 6h -o ../monkey-results/ --monkey
```

Here, 
* `--no-headless` shows the emulator GUI. 
* `--avd Android7.1` specifies the name of the emulator (which has already been created in the VM).
* `--apk ../Scarlet-Notes/instrumented-Scarlet-Notes-#114.apk` specifies the target bug which is `ScarletNotes`'s bug `#114` in `v1.1.8`.
* `--time 6h` allocates 6 hours for the testing tool to find the bug 
* `-o ../monkey-results/` specifies the output directory of testing results
* `--monkey` specifies the testing tool

**Step 3. run the analysis script to analyze the effectiveness of Monkey**

First, we need to change the cwd to `/home/ddroid-core`:

```
cd ../ddroid-core/
```

* To analyze one single round of testing results which is outputted under `../monkey-results/`:

```
python3 main.py ../monkey-results/instrumented-Scarlet-Notes-#114.apk.monkey.result
```

Here, `../monkey-results/instrumented-Scarlet-Notes-#114.apk.monkey.result` is generated by **Step 2**


* To analyze multiple rounds of testing results which are outputted under `../monkey-results/`:

```
python3 main.py -b ../monkey-results/
```

Here, 
* `-b` (`--batch`) is used to output the all detailed coverage statistics in terms of event coverage, event-pair coverage and trace-based minimal distance under a specific directory
* Use `-v` option to generate html format clues

## 3. Themis+'s clues

### **Textual Report**

A example textual coverage report (this is the example report from `instrumented-Scarlet-Notes-#114.apk` ran by FastBot):

```
***********************************[ ScarletNote-#114 (fastbot) ]***********************************
----------------------------------[ The statistics of each event ]----------------------------------
          [ #114 ] Event 1/5:  77-0  . (0:04:20/6:00:00)
              > Event info: Created a new notebook.
          [ #114 ] Event 2/5:  96-0  . (0:04:48/6:00:00)
              > Event info: Entered a notebook.
          [ #114 ] Event 3/5:  10-0  . (0:08:33/6:00:00)
              > Event info: Clicked the "X" icon on the left bottom to close the notebook.
          [ #114 ] Event 4/5:   3-0  . (0:30:23/6:00:00)
              > Event info: Clicked the "Locked" option in the main menu.
          [ #114 ] Event 5/5:   0-0  . (None/6:00:00)
              > Event info: Clicked the menu on the left bottom.
----------------------------------------[ Themis+'s clues ]----------------------------------------
                    Event Coverage(%)     Event-Pair Coverage(%)    Min Distance
          [ #114 ]    4/5 (80.00%)            10/21(47.62%)               3
***************************************[ Analysis finished ]***************************************
```

We can also get a brief overview of the three metrics using Themis+.

```
[Scarlet-Notes]
    [#114] ['60.00% / 38.10% / 3 / False', '80.00% / 47.62% / 3 / False', '80.00% / 52.38% / 3 / False', '80.00% / 47.62% / 3 / False', '80.00% / 47.62% / 3 / False']
    [#114-best] 80 & 52 & 3
```

---

### **HTML Report**

With option `-v`, we can get the clues in HTML format (which can be viewed on a browser). And those text is generated by Themis+.
```
python3 main.py ../monkey-results/instrumented-Scarlet-Notes-#114.apk.monkey.result -v
```
**Bug-Triggering Trace**

At the beginning of the clues, the minimal bug-triggering trace is shown, in which pivot events are highlighted by an red box.

<div align="center">
    <img src="./figures/bug-triggering-trace.png" width="90%"/>
</div>


**Themis+'s Clues**

Then the three metrics (event coverage, event-pair coverage and minimal distance) visualied are given. 
- *Event coverage* and *Event Pair Coverage* show how many events and event pairs are covered or missed by the specific numbers and percentages.
- *Distance Statistics* shows the distances experienced when running the tool. The distances here are all shortest distances between one states and the final state (i.e., the crash state).  And the distances are sorted from largest to smallest. For example, the minimal distance in the figure below is [3].

<div align="center">
    <img src="./figures/themis-plus-clues.png" width="90%"/>
</div>

**Details**

Next is the details of event executions and the minimal distance. 
- At the top of the figure below, event execution times are shown next to the event ID and the *black vertical line* implies the minimal distance to the crash state (i.e., the testing tool needs to follow the minimal bug-triggering trace to execute $E_3$, $E_4$ and $E_5$ to trigger the bug). 

<div align="center">
    <img src="./figures/event-details.png" width="90%"/>
</div>

- At the bottom is the event statistics. 
This chart visualizes the event execution times and the time of first execution of each pivot event, showing the difference in aforementioned two aspects between the different events.

<div align="center">
    <img src="./figures/event-statistics.png" width="60%"/>
</div>

**Batch Analysis**

If the option `-b` (`--batch`) is enabled, the analysis summary file generated looks like the following figure. The green entry means that the testing tool triggers the bug in the corresponding run. Each entry shows the event coverage, event pair coverage and minimal distance succintly.

<div align="center">
    <img src="./figures/summary.png" width="100%"/>
</div>




