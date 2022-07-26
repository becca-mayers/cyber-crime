#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jul 12 16:05:16 2022

@author: rebecca
"""

#cyber
from selenium.common.exceptions import (ElementClickInterceptedException,
                                        StaleElementReferenceException,
                                        NoSuchElementException, 
                                        WebDriverException,
                                        TimeoutException)
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup as bs
from calendar import month_name
from selenium import webdriver
from time import sleep,time
from requests import get
import pandas as pd
import tweepy
import csv
import re

start_time = time()

#%% Helper functions
def parse_it(table):       
    rows = []
    trs = table.find_all('tr')
    header_row = [td.get_text(strip=True) for td in trs[0].find_all('th')] # header row
    if header_row: # if there is a header row include first
        rows.append(header_row)
        trs = trs[1:]
    for tr in trs: # for every table row
        rows.append([td.get_text(strip=True) for td in tr.find_all('td')]) # data row
    return rows

def scroll_to_bottom(driver):
    return driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

#%%

#initialize automation
ignored_exceptions = (ElementClickInterceptedException,
                      StaleElementReferenceException,
                      NoSuchElementException, 
                      WebDriverException,
                      TimeoutException)

chrome_options = Options()
#chrome_options.add_argument("--headless")

driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options) 
wait = WebDriverWait(driver, 6, poll_frequency=6, ignored_exceptions=ignored_exceptions)
actions = ActionChains(driver);

#%% IC3

ic3_years = list(range(2016,2022))

#initialize data list
ic3_list = []

victim_count_list = []
loss_amount_list = []
subject_count_list = []

for ic3_year in ic3_years:
    
    ic3_url = 'https://www.ic3.gov/Media/PDF/AnnualReport/{}State/StateReport.aspx'.format(str(ic3_year))
    
    driver.get(ic3_url)
    
    for i in range(2,59):  
    
        #get selected state from site title
        state_dropdown_xpath = '/html/body/div/form/header/div[2]/h1'
        selected_state = wait.until(EC.element_to_be_clickable((By.XPATH, state_dropdown_xpath))).text
        
        print(ic3_year, selected_state)
    
        #switch to soup
        soup = bs(driver.page_source, 'lxml') 
    
        #find all the page tables
        ic3_tables = soup.find_all('table', class_ = 'crimetype')

        for ic3_table in ic3_tables:

            #parse table
            this_ic3_table = parse_it(ic3_table)
            #convert to dataframe, set headers
            this_ic3_table_df = pd.DataFrame(this_ic3_table, columns = this_ic3_table[0])
            this_ic3_table_df = this_ic3_table_df.drop(this_ic3_table_df.index[0])
            
            #get the 3rd and 4th column
            first_ic3_subset_df = this_ic3_table_df.iloc[:,0:2]
            second_ic3_subset_df = this_ic3_table_df.iloc[:,2:4]
            
            final_ic3_df = pd.concat([first_ic3_subset_df, second_ic3_subset_df])
            #insert state and source
            final_ic3_df['state'] = selected_state
            final_ic3_df['year'] = ic3_year
            final_ic3_df['url'] = ic3_url
            
            if 'Victim Count' in final_ic3_df.columns.values:
                 victim_count_list.append(final_ic3_df)
            
            elif 'Loss Amount' in final_ic3_df.columns.values:
                loss_amount_list.append(final_ic3_df)
            
            elif 'Subject Count' in final_ic3_df.columns.values:
                subject_count_list.append(final_ic3_df)
            
            ic3_list.append(final_ic3_df)

        updated_url = ic3_url + '#?s={}'.format(str(i))

        driver.get(updated_url)
        
        sleep(1)        

victim_count_df = pd.concat(victim_count_list)
victim_count_df.to_csv('Victim Count.csv')

loss_amount_df = pd.concat(loss_amount_list)

#clean up the formatting
loss_amount_df['Loss Amount'] = loss_amount_df['Loss Amount'].str.replace('$','').str.replace(',','')
loss_amount_df = loss_amount_df.reset_index().drop('index', axis = 1)
for i in range(0, len(loss_amount_df.index)):
    loss_amount = loss_amount_df.loc[i, 'Loss Amount']
    if loss_amount is not None:
        loss_amount = int(loss_amount)
        loss_amount_df.loc[i,'Loss Amount'] = loss_amount
loss_amount_df.to_csv('Loss Amount.csv')

subject_count_df = pd.concat(subject_count_list)
subject_count_df.to_csv('Subject Count.csv')

#free up some memory
del victim_count_list
del loss_amount_list
del subject_count_list

#%% Google Exploit DB

def google_processing_check(wait):
    #Checks for the 'Processing' modal
    try:
        wait.until(EC.visibility_of_element_located((By.ID, 'exploits-table_processing')))
    except ignored_exceptions:
        pass
    
google_exploit_db = 'https://www.exploit-db.com/' 
driver.get(google_exploit_db)

google_processing_check(wait)

#change show dropdown to 120
show_xpath = '/html/body/div/div[2]/div[2]/div/div/div[2]/div[2]/div/div[1]/div[1]/div/label/select'
wait.until(EC.element_to_be_clickable((By.XPATH, show_xpath))).click()

show120_xpath = '/html/body/div/div[2]/div[2]/div/div/div[2]/div[2]/div/div[1]/div[1]/div/label/select/option[4]'
wait.until(EC.element_to_be_clickable((By.XPATH, show120_xpath))).click()

scroll_to_bottom(driver)

total_pages = 376
    
google_exploit_list = []

for i in range(1, total_pages + 1): 
    
    google_processing_check(wait)
    
    print(i)

    soup = bs(driver.page_source, 'lxml') 

    #find all the page tables
    google_table = soup.find('table', class_ = 'table table-striped table-bordered display dataTable no-footer dtr-inline')            

    try:
        this_google_table = parse_it(google_table)
        #convert to dataframe and drop the first row
        this_google_table_df = pd.DataFrame(this_google_table, columns = this_google_table[0])
        this_google_table_df = this_google_table_df.drop(this_google_table_df.index[0])
        google_exploit_list.append(this_google_table_df)
    
    except:
        pass
           
    #check for processing modal                    
    google_processing_check(wait)
    
    #scroll to bottom
    scroll_to_bottom(driver)
    
    try:
        next_css = '#exploits-table_next'
        wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, next_css))).click()
    
    except TimeoutException:
        
        try:
            #check for processing modal
            google_processing_check(wait)
            wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'paginate_button page-item next'))).click() # id="exploits-table_next"><a href="#" aria-controls="exploits-table" data-dt-idx="9" tabindex="0" class="page-link">Next</a></li>       
        except:
            break

#concatenate the list of dataframes
google_exploits_df = pd.concat(google_exploit_list)    
google_exploits_df['Date'] = pd.to_datetime(google_exploits_df['Date'])
google_exploits_df.to_csv('Google Exploits.csv')

#free up some memory
del google_exploit_list

#%% CVES
#loop through the years + months & collect results

cve_details_list = []

years = list(range(2016,2023))
month_numbers = list(range(1,13))

for year in years:
    for month_number in month_numbers:
    
        cve_details_url = 'https://www.cvedetails.com/vulnerability-list/year-{}/month-{}/{}.html'.format(str(year), str(month_number), month_name[month_number])
        driver.get(cve_details_url)

        #move to the bottom to get all of the page links
        scroll_to_bottom(driver)
        page_section = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="pagingb"]')))
        page_links = [i for i in page_section.find_elements(By.TAG_NAME,'a')]
        
        for l in range(0,len(page_links)):
            
            print(year, month_name[month_number], l)
            
            try:
                #redeclare stale elements
                scroll_to_bottom(driver)
                page_section = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="pagingb"]')))
                link = [i for i in page_section.find_elements(By.TAG_NAME,'a')][l]
                
                link.click()
                
                soup = bs(driver.page_source, 'lxml') 
        
                #find the page table
                cve_table = soup.find('table', class_ = 'searchresults sortable')            
        
                try:
                    this_cve_table = parse_it(cve_table)
                    #create dataframe from results
                    this_cve_table_df = pd.DataFrame(this_cve_table, columns = this_cve_table[0])
                    #drop out the first row
                    this_cve_table_df = this_cve_table_df.drop(this_cve_table_df.index[0])
                    cve_details_list.append(this_cve_table_df)
                  
                except:
                     pass
            
            except TimeoutException:
                pass

cve_details_df = pd.concat(cve_details_list)

#add the even indices under column '#' as descriptions to the prior row
descriptions = cve_details_df['#'][1::2]
descriptions_df = pd.DataFrame(descriptions)
descriptions_df = descriptions_df.reset_index().drop('index', axis = 1).rename(columns = {'#':'description'})

#drop out odd rows
cve_details_to_keep = cve_details_df[::2]
cve_details_to_keep = cve_details_to_keep.reset_index().drop('index', axis = 1)
final_cve_details_df = cve_details_to_keep.merge(descriptions_df, left_index = True, right_index = True)
final_cve_details_df.to_csv('CVE Details.csv')

#free up some memory
del cve_details_list

driver.close()

end_time = time()

total_time = (end_time - start_time)/60

print('total runtime: ', total_time)