# bespin-cli
Command line client for Bespin


## Example usage

### Find workflow tag
List workflows:
```
bespin workflow list
```
Output:
```
bespin workflow list
  Id  Name                     Job Template Tag
----  -----------------------  ------------------------------------------
   1  WES GATK4 Preprocessing  wes-gatk4-preprocessing/v1/b37-human-xgen
```


### Init job file
```
bespin job-template create wes-gatk4-preprocessing/v1/b37-human-xgen --outfile job1.yml
```
Output:
```
Wrote job file job1.yml.
Edit this file filling in TODO fields then run `bespin job create job1.yml` .
```


### User edits job file
Example job file:
```
fund_code: <String Value>
job_order:
  library: <String Value>
  read_pair:
    name: <String Value>
    read1_files:
    - class: File
      path: dds://<Project Name>/<File Path>
    read2_files:
    - class: File
      path: dds://<Project Name>/<File Path>
name: <String Value>
tag: wes-gatk4-preprocessing/v1/b37-human-xgen
```
User will replace all TODO fields with actual values.


### Create job using job file
```
bespin job create job1.yml
```
Output:
```
Created job 1
```

### Check Status of the job
```
bespin job list
```
Output:
```
  Id  Name                      State    Step    Last Updated                   Elapsed Hours  Workflow Version Tag
----  ------------------------  -------  ------  ---------------------------  ---------------  ---------------------------
   1  My                        A                2018-11-15T17:02:44.224348Z                0  wes-gatk4-preprocessing/v1   
```

### Start running the job
Start running a job
```
bespin job start 1
```

### Create and start a job in one step
```
bespin job run job1.yml
```
