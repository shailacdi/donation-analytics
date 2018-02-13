'''
Insight Donation Analytics coding Challenge

This program takes a file listing individual campaign contributions for multiple years, 
determine which ones came from repeat donors, calculate and ouput the info in the specified file and format
For each recipient, zip code and calendar year, calculate these three values for contributions coming from repeat donors:
    total dollars received
    total number of contributions received
    donation amount in a given percentile
Note : if a donor had previously contributed to any recipient listed in the input file in any prior calendar year, 
that donor is considered a repeat donor

@author: Shaila Iyengar
Created on 9-Feb-2018
'''

import numpy as np
from sys import argv
import time
import math
import yaml
import mmap
from tqdm import *

"""
Donorlist is a dict subclass. A dictionary cannot save records with duplicate keys, hence had to adapt to
the needs of this challenge.
If a row with duplicate key is added, it stores the values for that key as a list

"""
class Donorlist(dict):
    def __setitem__(self, key, value):
        try:
            self[key]
        except KeyError:
            super(Donorlist, self).__setitem__(key, [])
        self[key].append(value)
        
"""
Class Donation_Analytics
This is the main class that handles the data and the processing. 
Data is held mainly in two Donorlist objects - one for Master donor list, and one for Repeat donor list
For more details on the data structure used, please refer to the README document

Attributes:
    Constants for position of interested fields in the CSV for extraction
    master_donor_dict (type Donorlist)
    repeat_donor_dict (type Donorlist)
Methods:  
    process_data
        This is the main method to read the input line by line. Invokes process_input_record for further processing
    process_input_record
        This processes one line of input data at a time, identifies repeat donors, generate keys and mainly builds the data structures for 
        master donor list and repeat donor list.
    add_to_master_donor_list       
        Inserts a record into the master donor list look-up data structure. Master donor list is a Donorlist of Donorlists. 
        For a specific key, it saves a Donorlist as the value
    add_to_repeat_donor_dict
        Inserts record into repeat donor list. After it processes one record, it writes to output, one line at a time
    get_percentile_totals_transactions
        Mainly calculates the aggregates and percentile for the repeat donors
    Others..
        Validation methods
"""

class Donation_Analytics():

    # Constants - Denote required positions in the input file
    CMTE_ID = 0
    NAME = 7
    ZIP_CODE = 10
    TRANSACTION_DATE = 13
    TRANSACTION_AMOUNT = 14
    OTHER_ID = 15

    #Initialize few attributes
    def __init__(self, input_file=None, percentile_file=None, output_file=None):
        self.input_file = input_file
        self.output_file = output_file
        self.percentile_file = percentile_file
        self.master_donor_dict = Donorlist()
        self.repeat_donor_dict = Donorlist()
    
    #Fetch percentile value from the input file    
    def get_percentile_value(self, percentile_file):   
        try:
            file = open(percentile_file)
            for line in file:
                percentile_val = int(line.strip())
                if (percentile_val in range(1,100)):
                    return percentile_val
        except:
            print("Please provide a valid Percentile file")  
            raise Exception

    
    """
     Add a record in master_donor_dict (donor_key is NAME|ZIP_CODE , transaction amount )
     Since master donor list is a Donorlist of Donorlists, this method creates a donorlist and adds it to the master list
     For more details on datastructure, please refer to the README file
    """
    def add_to_master_donor_list(self, donor_key,cmte_id, year, transaction_amount):
        donor = Donorlist()
        #The inner Dictlist uses YEAR as key
        donor[year] = {"amount": transaction_amount, "cmte_id":cmte_id}
        self.master_donor_dict[donor_key] = donor
        return
    
    
    """
     Add a record in repeat_donor_dict (repeat_donor_key is CMTE_ID| , transaction amount )
     Since master donor list is a Donorlist of Donorlists, this method creates a donorlist and adds it to the master list
     For more details on datastructure, please refer to the README file
    """
    # Add a record in repeat_donor_dict (key is cmte_id, name and zipcode )
    def add_to_repeat_donor_dict(self, repeat_donor_key, transaction_amount, percentile_val):
        (percentile_amount, total_amount_by_repeat_donors, no_of_transactions) = self.get_percentile_totals_transactions(repeat_donor_key, transaction_amount, percentile_val)
        self.repeat_donor_dict[repeat_donor_key] = {"amount":transaction_amount, "total_amount":total_amount_by_repeat_donors,"percentile_amount":percentile_amount, "no_of_transactions":no_of_transactions}
        # Output the first 3 fields from the repeat_donor_key and append percentile, total and no_of_transactions
        percentile_amount = str(self.round_to_whole_dollar(percentile_amount))
        repeat_donor_string_output = "|".join([repeat_donor_key,percentile_amount,str(total_amount_by_repeat_donors),str(no_of_transactions)])
        #write to repeat donor output file
        print(repeat_donor_string_output, file=self.output_file_fp)
        return

    
    # This method validates the transaction date
    def is_transaction_date_valid(self, transaction_date):
        try:
            time.strptime(transaction_date, '%m%d%Y')
        except ValueError:
            return False
        return True


    # This method validates zip code (Only the first 5 digits are used here)
    def validate_zip(self, zip):
        if(zip != None):
            return len(zip) == 5
        return False
    
    #This method rounds up or down the percentile amount
    # 0.5 and above will be upper whole dollar 
    # Anything less than 0.5 will be the lower whole dollar
    def round_to_whole_dollar(self, any_number):
        if (float(any_number) % 1) >= 0.5:
            return(math.ceil(any_number))
        else:
            return(round(any_number))
   

    """
        process_input_record (cmte_id, name, zip_code, year, transaction_amount, percentile_val)
        This processes one line of input data at a time, identifies repeat donors, generate keys and mainly builds the data structures for 
        master donor list and repeat donor list.
        
        For master donor, the key  NAME|ZIP_CODE is created. The inner donorlist uses key YEAR
        For repeat donor the key CMTE_ID|ZIP_CODE|YEAR is created 
    """    
    def process_input_record(self, cmte_id, name, zip_code, year, transaction_amount, percentile_val):
        #create donor key for current record from file
        donor_key = name + '|' + zip_code
        try:
            #create donor key for the current record
            repeat_donor_key = cmte_id + '|' + zip_code + '|' + year
            
            #Checks if repeat donor : If he is repeat donor the donor key should exist in master donor list 
            if(self.master_donor_dict[donor_key]):
                
                # Current donor is a repeat donor. But check whether record is listed out of order 
                # Eg., Lets say a record for the key NAME|ZIP calendar year 2017 is already processed.
                # Now, the current record has calendar year 2015 for the same donor -- Skip this record           
                if not (self.is_data_listed_out_of_order(donor_key,year)):  
                    #valid record to output - Add the repeat donor to repeat donor list
                    self.add_to_repeat_donor_dict(repeat_donor_key, transaction_amount, percentile_val)
                
                    #add current donor to master donor list 
                    self.add_to_master_donor_list(donor_key,cmte_id, year, transaction_amount)
            else:         
                #Current donor is NOT a repeat donor, just add to master donor list
                self.add_to_master_donor_list(donor_key,cmte_id, year, transaction_amount)
        except KeyError:
            #Indicates that this is the first occurance of the valid donor . Add to master donor list
            self.add_to_master_donor_list(donor_key,cmte_id, year, transaction_amount)
        return
    
    # This method returns the number repeat donors for a CMTE_ID|ZIP|YEAR key. 
    # It simply is the number of records by key in the repeat donor list
    def get_number_of_repeat_donor_transactions_byKey(self, repeat_donor_key):
        return len(self.repeat_donor_dict[repeat_donor_key])    


    #This method checks if data is out of order.
    # Eg., Lets say a record for the key NAME|ZIP calendar year 2017 is already processed.
    # Now, the current record has calendar year 2015 for the same donor  -- Need to Skip record 
   
    def is_data_listed_out_of_order(self, donor_key, current_record_year):
        year_list = []   
        # NOTE : master donor list is Dictlist of Dictlists. 
        # Get all values for key NAME|ZIP from master donor list - this returns a list of Dictlist
        # the Key for the inner Dictlist is YEAR. Get the Max_value of Keys
        # Let's say current record has calendar year 2015, the Maximum year key returned is 2017
        # The current record being processed ie, calendar year 2015 needs to be skipped
        try:
            for row in self.master_donor_dict[donor_key]:
                for key in row:
                    year_list.append(int(key))
            current_record_year = int(current_record_year)   
            #Most recent calendar year where a transaction was processed for NAME|ZIP key (a donor)
            max_year = max(year_list)
            # Check calendar year of the transaction date in the Current record
            if(current_record_year < max_year):
                return True
            else:
                return False        
        except:    
            raise (Exception("Failed while checking for year disorder"))    

 
    # This method calculates the percentile amount for the repeat donor record to be output   
    def get_percentile_totals_transactions(self, repeat_donor_key, amount, percentile_val):
        #Initialize as default value with the contribution amount of current repeat donor
        list_of_contribution_amounts = [amount]
                 
        #Initialize as default value with one transaction for the current repeat donor
        no_of_transactions = 1
        #calculate totals, transactions and percentile if there are more repeat donors with key CMTE_ID|ZIP|YEAR
        
        #Check of this record happens to be the first repeat donor for the key CMTE_ID|ZIP|YEAR
        try:
            repeat_donors = self.repeat_donor_dict[repeat_donor_key]
        except KeyError:
            return (amount,amount,no_of_transactions)
        
        #Find the total contributions of the repeat donors by key
        for item in repeat_donors:
            temp_amount = item["amount"] 
            amount += temp_amount  
            list_of_contribution_amounts.append(temp_amount)
        
        #Calculate percentile amount for all transactions by repeat donor for CMTE_ID|ZIP|YEAR based on percentile value provided
        percentile_amount = np.percentile(np.array(list_of_contribution_amounts),percentile_val,  interpolation='nearest')    
        
        # Get # of transactions for CMTE_ID|ZIP|YEAR 
        no_of_repeat_donors = self.get_number_of_repeat_donor_transactions_byKey(repeat_donor_key)
        no_of_transactions += no_of_repeat_donors   
        return (percentile_amount,amount,no_of_transactions)
    """
    process_data
    This is the main method to read the input line by line. Invokes process_input_record for further processing
    Reads input file line by line, tokenizes, invokes few validations and method process_input_recod

    """    
        
    def process_data(self):
        if self.input_file is None:
            print("Input file not provided")
            return
        if self.percentile_file is None:
            print("Percentile file not provided")
            return

        try:
            # get the percentile value from input percentile file
            percentile_val = self.get_percentile_value(percentile_file)            
            
            # gets file handlers for input data and output files
            self.input_file_fp = open(self.input_file, 'r')            
            self.output_file_fp = open(self.output_file, 'w')           
            
            # Repeats for every line read from input data file . 
            # Since the process may take longer for huge files, a progress bar has been added  using the tqdm module
            # This takes a few extra seconds since calculates the progress and does i/o too at intervals
            # for line in self.input_file_fp:
            for line in tqdm(self.input_file_fp, total=self.get_num_lines()):
                #split into tokens by delimiter |
                fields = line.strip().split('|')
                
                #required fields for processing
                
                #recipient
                cmte_id = fields[self.CMTE_ID]    
                
                #donor
                name = fields[self.NAME]          
                
                #zip code of donor, only first 5 digits are required
                zip_code = fields[self.ZIP_CODE][:5] 
                
                # transaction occured date
                transaction_date = fields[self.TRANSACTION_DATE]
                
                #transaction amount read as either float or whole amounts using yaml
                transaction_amount = yaml.load(fields[self.TRANSACTION_AMOUNT])                
                
                #other id --> elimination criteria - not individual donor
                other_id = fields[self.OTHER_ID]
                
                # Validate the fields 
                if other_id.strip() == '' and cmte_id != '' and transaction_amount != '' :
                    if self.is_transaction_date_valid(transaction_date):
                        # The last 4 digits of the year is needed
                        year = transaction_date[-4:]
                        
                        #process the record
                        self.process_input_record(cmte_id, name, zip_code, year, transaction_amount, percentile_val)
                        
        except FileNotFoundError as f:            
            print("Please provide valid Input files.. : ", f)
        except Exception as e:
            print("Aborted data processing ", e)   
        except Error as e:
            print ("Aborting data processing ", e)    
        finally:    
            #cleanup code
            if(self.input_file_fp):
                self.input_file_fp.close()
            if(self.output_file_fp):
                self.output_file_fp.close()
            
        return    

    # This is to support the progress bar display. It gets the total lines from input file.
    # Based on number of lines processed, it displays rate of progress
    def get_num_lines(self):
        fp = open(self.input_file, "r+")
        buf = mmap.mmap(fp.fileno(), 0)
        lines = 0
        while buf.readline():
            lines += 1
        return lines

"""
Main funtion for this Donation analysis. Process the command line arguments which is the input, percentile and the output files
Instanciate the main class, and calls its main method to process data
"""
if __name__ == "__main__":
    if (len(argv) < 4):
        print('Invalid : Please provide valid command line arguments')
        exit(1)
        
    # parse command line arguments    
    (script, input_file, percentile_file, output_file) = argv
     
    print("Processing data for Donation Analytics. It may take some time, please wait..")
    analyzer = Donation_Analytics(input_file, percentile_file, output_file)
    analyzer.process_data()
    print("Processing data for Donation Analytics COMPLETE!")            
