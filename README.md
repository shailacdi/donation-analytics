
#Donation Analytics README

# Table of Contents
1. [Solution Approach](README.md#approach)
2. [Solution Design](README.md#solution-design)
3. [Data structure considerations ](README.md#datastructures)
4. [Software/package dependencies ](README.md#dependencies)

# Solution Approach

This program is likely to handle large volume of data. Based on the requirement, and looking at few files in the FEC links provided, it is very evident that the Data Structure design is the key. This program iterates through the history of donor transactions, and with the requirement of computing running percentiles, data cannot be a small set any point of time - it accumulates.

Python is a very powerful language and is known for its versatile features. This program mainly exploits the datastructure support and a few python packages/modules.

# Solution Design

- Donor_Analytics : A simple main class with methods to process input file line by line  
- Main method to process a line
- Validation methods
- Other methods to compute totals etc.
- File operations
- Display progress bar - helpful since application runs for longer time to produce the output
- Key uses "|" . This helps in quicker query, and eliminates str operations while writing to output file

How is the data structure constructed?  
Master donor list is created with all valid donors - Dictlist(dict). This uses key as **NAME|ZIPCODE**. This is a Dictlist of Dictlists as shown below. YEAR is the key for the nested inner Dictlist, and it helps to query by YEAR. A structure of Dictlist of dicts could have been an alternative, however, this approach provides more flexibility for any future requirements. 

Sample Input data (showing only required fields). Please note that donor O'REGAN has multiple transactions for YR2017
> C00496679|O'REGAN, KATHLEEN|92253|12042016|110
> C00496679|O'REGAN, KATHLEEN|92253|12042017|25   
> C00496679|O'REGAN, KATHLEEN|92253|12042017|20   
> C00496680|WESTWOOD, ROBERT|92270|12042017|100    

Sample datastructure for Master donor list built during processing. As you see, if there is a duplicate key, a list of the values will be generated against the key.

{**"O'REGAN, KATHLEEN|92253"**: [{**'2016'**: [{'amount': 110, 'cmte_id': 'C00496679'}]}, {**'2017'**: [{'amount': 25, 'cmte_id': 'C00496679'}]}, {**'2017'**: [{'amount': 20, 'cmte_id': 'C00496679'}]}], **'WESTWOOD, ROBERT|92270'**: [{**'2017'**: [{'amount': 100, 'cmte_id': 'C00496680'}]}]} 


Repeat donor list is built for repeat donors. This uses key **CMTE_ID|ZIP_CODE|YEAR**. This ultimatately converts to the output.

Sample of datastructure for Repeat donor list shown below:
> {'**C00496679|92253|2017**': [{'amount': 25, 'total_amount': 25, 'percentile_amount': 25, 'no_of_transactions': 1}, {'amount': 20, 'total_amount': 45, 'percentile_amount': 20, 'no_of_transactions': 2}]}

The following points was considered while picking the Datastructure
	- key based for faster look-up
	- highly efficient inserts
	- mutable
	- inplace updates
	- nested

# Data structure considerations
Upon trying various built-in Data Structures, I have created Dictlist(dict).  Below are the options considered before making the decision.

a. DataFrames : While this was robust, Dataframe append was not found to be suitable. Would have worked best perhaps if it was a one-time load and read-only-processing

b. Dictionary : This was the next option. However, the challenge here is with valid duplicate keys [NAME|ZIP] which cannot be added into plain dict. Hence it was subclassed. 


# Software/package dependencies 

1. This program uses Python 3.6

	Run.sh:
	python3.6 ./src/donation-	analytics.py ./input/itcont.txt ./input/percentile.txt ./o	utput/repeat_donors.txt

2. The following packages are used, and needs to be installed using pip install
	- numpy v1.14.0
	- pyyaml v3.12  
	- tqdm v4.19.5

3. The following modules are imported
	- import numpy as np
	- from sys import argv
	- import time
	- import math
	- import yaml
	- import mmap
	- from tqdm import *	
	