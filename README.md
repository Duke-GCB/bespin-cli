# bespin-cli
Command line client for Bespin


## Example usage

### Find workflow slug
List workflows:
```
bespin workflows list
```
Output:
```
  Id  Name                          Latest Version Slug
----  ----------------------------  -------------------------
   1  QIIME2 Step 1                 qime2_step1/1/human
   2  QIIME2 Step 2 (DADA2 option)  qime2_step2_dada2/1/human
```


### Init job file
```
bespin jobs init --slug qime2_step1/1/human --outfile job1.yml
```
Output:
```
Wrote job file job1.yml.
Edit this file filling in TODO fields then run `bespin job create job1.yml` .
```


### User edits job file
Example job file:
```
fund_code: TODO
name: TODO
params:
  barcodes:
    class: File
    path: dds://TODO_PROJECT_NAME/TODO_FILE_PATH
  metadata_barcodes_column: TODO
  sample_metadata:
    class: File
    path: dds://TODO_PROJECT_NAME/TODO_FILE_PATH
  sequences:
    class: File
    path: dds://TODO_PROJECT_NAME/TODO_FILE_PATH
workflow_slug: qime2_step1/1/human
```
User will replace all TODO fields with actual values.


### Create job using job file
```
bespin jobs create job1.yml
```
Output:
```
Created job 1
```

### Check Status of the job
```
bespin jobs list
```
Output:
```
bespin jobs list
  Id  Name    State    Step      Fund Code  Created           Last Updated
----  ------  -------  ------  -----------  ----------------  ----------------
   1  My Job  New                       1   2018-06-07 17:00  2018-06-07 17:00
```

### Start running the job
```
bespin jobs start job1.yml
```
