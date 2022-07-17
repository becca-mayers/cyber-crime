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
import re

start_time = time()


#%% Helper func
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
# ic3_2021_url = 'https://www.ic3.gov/Media/PDF/AnnualReport/2021State/StateReport.aspx'
# ic3_2020_url = 'https://www.ic3.gov/Media/PDF/AnnualReport/2020State/StateReport.aspx'
# ic3_2019_url = 'https://www.ic3.gov/Media/PDF/AnnualReport/2019State/StateReport.aspx'
# ic3_2018_url = 'https://www.ic3.gov/Media/PDF/AnnualReport/2018State/StateReport.aspx'
# ic3_2017_url = 'https://www.ic3.gov/Media/PDF/AnnualReport/2017State/StateReport.aspx'
# ic3_2016_url = 'https://www.ic3.gov/Media/PDF/AnnualReport/2016State/StateReport.aspx'

# ic3_urls = [ic3_2016_url, ic3_2017_url, ic3_2018_url, ic3_2019_url, ic3_2020_url, ic3_2021_url]

#initialize data list
victim_count_list = []
loss_amount_list = []
subject_count_list = []

for ic3_year in ic3_years:
    
    ic3_url = 'https://www.ic3.gov/Media/PDF/AnnualReport/{}State/StateReport.aspx'.format(str(ic3_year))
    
    driver.get(ic3_url)
    
    for i in range(2,59):  

        try:
    
            #get selected state from site title
            state_dropdown_xpath = '/html/body/div/form/header/div[2]/h1'
            selected_state = wait.until(EC.element_to_be_clickable((By.XPATH, state_dropdown_xpath))).text
            
            print(i,selected_state)

            #switch to soup
            soup = bs(driver.page_source, 'lxml') 
        
            #find all the page tables
            ic3_tables = soup.find_all('table', class_ = 'crimetype')
            
            for i in range(0,len(ic3_tables)):
                
                ic3_table = ic3_tables[i]
                #parse table
                this_ic3_table = parse_it(ic3_table)
                #convert to dataframe, set headers
                this_ic3_table_df = pd.DataFrame(this_ic3_table, columns = this_ic3_table[0])
                this_ic3_table_df = this_ic3_table_df.drop(this_ic3_table_df.index[0])
                #insert state and source
                this_ic3_table_df['state'] = selected_state
                this_ic3_table_df['url'] = ic3_url
                
                #store to corresponding list
                if i == 0:
                    victim_count_list.append(this_ic3_table_df)
                elif i == 1:
                    loss_amount_list.append(this_ic3_table_df)
                elif i == 2:
                    subject_count_list.append(this_ic3_table_df)
                    
        
        except TimeoutException:
            pass
        
        updated_url = ic3_url + '#?s={}'.format(str(i))
    
        driver.get(updated_url)
        
        sleep(1)        

victim_count_df = pd.concat(victim_count_list)
victim_count_df = victim_count_df.drop_duplicates()

loss_amount_df = pd.concat(loss_amount_list)
loss_amount_df = loss_amount_df.drop_duplicates()

subject_count_df = pd.concat(subject_count_list)
subject_count_df = subject_count_df.drop_duplicates()

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
    
google_exploit_db = 'https://www.exploit-db.com/' #''https://www.exploit-db.com/google-hacking-database'
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
google_exploits_df = google_exploits_df.drop_duplicates()    

#free up some memory
del google_exploit_list


#%% CVES
#loop through the years + months & collect results

cve_details_list = []

years = list(range(2002,2023))
month_numbers = list(range(1,13))

for year in years:
    for month_number in month_numbers:
    
        cve_details_url = 'https://www.cvedetails.com/vulnerability-list/year-{}/month-{}/{}.html'.format(str(year), str(month_number), month_name[month_number])
        driver.get(cve_details_url)
        
        print(cve_details_url)
        
        #move to the bottom to get all of the page links
        scroll_to_bottom(driver)
        page_section_xpath = '//*[@id="pagingb"]'
        page_section = wait.until(EC.element_to_be_clickable((By.XPATH, page_section_xpath)))
        page_links = [i for i in page_section.find_elements(By.TAG_NAME,'a')]
        
        for l in range(0,len(page_links)):
            
            print(year, month_name[month_number], l)
            
            #redeclare stale elements
            page_section = wait.until(EC.element_to_be_clickable((By.XPATH, page_section_xpath)))
            link = [i for i in page_section.find_elements(By.TAG_NAME,'a')][l]
            
            link.click()
            
            soup = bs(driver.page_source, 'lxml') 
    
            #find the page table
            cve_table = soup.find('table', class_ = 'searchresults sortable')            
    
            try:
                this_cve_table = parse_it(cve_table)
                this_cve_table_df = pd.DataFrame(this_cve_table, columns = this_cve_table[0])
                this_cve_table_df = this_cve_table_df.drop(this_cve_table_df.index[0])
                cve_details_list.append(this_cve_table_df)
              
            except:
                 pass

cve_details_df = pd.concat(cve_details_list)
cve_details_df = cve_details_df.drop_duplicates()

#free up some memory
del cve_details_list

driver.close()


#%% Google Scholar
#credit: https://medium.com/@nandinisaini021/scraping-publications-of-aerial-image-research-papers-on-google-scholar-using-python-a0dee9744728

#Helper Functions

def get_paper_info(paper_url):
    '''Collect page info'''
    headers = {'user-agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.5060.114 Safari/537.36'}
    response = get(paper_url,headers=headers)
    
    #check for successful response
    if response.status_code != 200:
        raise Exception('Failed to fetch web page ')
    
    #get page text
    paper_doc = bs(response.text,'html.parser')
    
    return paper_doc

def get_tags(doc):
    '''Collect element tags'''
    paper_tag = doc.select('[data-lid]')
    url_tag = doc.find_all('h3',{"class" : "gs_rt"})
    author_tag = doc.find_all("div", {"class": "gs_a"})
    return paper_tag, url_tag,author_tag

def get_title(paper_tag):
    '''Collect paper title'''
    paper_names = []
    for tag in paper_tag:
      paper_names.append(tag.select('h3')[0].get_text())
    return paper_names

# function for the getting link information
def get_urls(url_tag):
    '''Get urls'''
    links = []
    for i in range(len(url_tag)):
      links.append(url_tag[i].a['href']) 
    return links 

def get_author(author_tag):
    '''Get authors'''
    authors = []
    for i in range(len(author_tag)):
        author_tag_text = (author_tag[i].text).split()
        author = author_tag_text[0] + ' ' + re.sub(',','', author_tag_text[1])
        authors.append(author) 
    return authors

#collect results
paper_dict = { 'title': [],
              'author': [],
                 'url': []}

# adding information in repository
def results_table(paper_name, author, link):
  paper_dict['title'].extend(paper_name)
  paper_dict['author'].extend(author)
  paper_dict['url'].extend(link)

  return pd.DataFrame(paper_dict)

#%% Begin Google Scholar

google_scholar_list = []

years = list(range(2002,2023))

for year in years:
    
    for i in range (0,110,10):
    
        google_scholar_url = 'https://scholar.google.com/scholar?start={}&q=cybercrime&hl=en&as_sdt=0,44&as_ylo={}&as_rr=1&as_vis=1'.format(str(i), str(year))
        
        print(i, year, google_scholar_url)
          
        #get page content
        doc = get_paper_info(google_scholar_url)
    
        #collect tags
        paper_tag, url_tag, author_tag = get_tags(doc)
          
        #collect titles
        paper_name = get_title(paper_tag)
        
        #collect author
        author = get_author(author_tag)
        
        #get paper url
        paper_url = get_urls(url_tag)
        
        #put it all together
        google_scholar_results = results_table(paper_name, author, paper_url)
          
        google_scholar_results['year'] = year
        
        google_scholar_list.append(google_scholar_results)
          
        # use sleep to avoid status code 429
        sleep(5)

google_scholar_df = pd.concat(google_scholar_list)
google_scholar_df = google_scholar_df.drop_duplicates()

del google_scholar_list

#dolthub
dolthub_url = 'https://www.dolthub.com/discover'

#Vulnerability db 
vuldb_url = 'https://vuldb.com/?stats'

#cx security vulnerability database
cx_url = 'https://cxsecurity.com/exploit/'

#vulnerability lab https://www.vulnerability-lab.com/

end_time = time()

total_time = (end_time - start_time)/60

print('total runtime: ', total_time)