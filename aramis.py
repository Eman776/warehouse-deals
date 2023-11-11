			#Imports#

from bs4 import BeautifulSoup
from requests import ConnectionError
import gc
import requests
import time
import aramis_lock
import subprocess
import os
import os.path
from datetime import datetime

######################################################################################################################################################################################################################################

			#Variables#

cred = aramis_lock.load_config()
zyte = cred[0]
retry_count = 0
tools = 'https://www.amazon.com/s?i=tools&bbn=10158976011&rh=n%3A10158976011%2Cn%3A228013%2Cn%3A328182011%2Cn%3A551236&dc&page=1'
computers = 'https://www.amazon.com/s?i=computers&bbn=10158976011&rh=n%3A10158976011%2Cn%3A172282%2Cn%3A493964%2Cn%3A541966%2Cn%3A13896617011&page=1'
kitchen = 'https://www.amazon.com/s?i=kitchen&bbn=10158976011&rh=n%3A10158976011%2Cn%3A1055398%2Cn%3A1063498%2Cn%3A284507%2Cn%3A289913&page=1'
amazon_devices = 'https://www.amazon.com/s?i=warehouse-deals&rh=n%3A16270727011&page=1'
cameras = 'https://www.amazon.com/s?i=photo&bbn=10158976011&rh=n%3A10158976011%2Cn%3A172282%2Cn%3A493964%2Cn%3A502394%2Cn%3A281052&page=1'
video_games = 'https://www.amazon.com/s?i=videogames&bbn=10158976011&page=1'
automotive = 'https://www.amazon.com/s?i=automotive&bbn=10158976011&rh=n%3A10158976011%2Cn%3A15684181&page=1'
phones = 'https://www.amazon.com/s?i=mobile&bbn=7072561011&rh=n%3A7072561011%2Cp_n_feature_twenty-one_browse-bin%3A21596696011%2Cp_n_feature_twenty-seven_browse-bin%3A24426371011|24426374011&dc&page=1'
furniture = 'https://www.amazon.com/s?i=garden&bbn=10158976011&rh=n%3A10158976011%2Cn%3A1055398%2Cn%3A1063498%2Cn%3A1063306&page=1'
television = 'https://www.amazon.com/s?i=electronics&bbn=10158976011&rh=n%3A10158976011%2Cn%3A172282%2Cn%3A493964%2Cn%3A1266092011%2Cn%3A172659&page=1'
grocery = 'https://www.amazon.com/s?i=grocery&bbn=10158976011&page=1'
baby = 'https://www.amazon.com/s?i=baby-products&bbn=10158976011&rh=n%3A10158976011%2Cn%3A165796011&page=1'
outdoor_cooking = 'https://www.amazon.com/s?i=lawngarden&bbn=10158976011&rh=n%3A10158976011%2Cn%3A2972638011%2Cn%3A3238155011%2Cn%3A553760&page=1'
outdoor_rec = 'https://www.amazon.com/s?i=outdoor-recreation&bbn=10158976011&rh=n%3A10158976011%2Cn%3A3375251%2Cn%3A3375301%2Cn%3A706814011%2Cn%3A3400371&page=1'
lawn = 'https://www.amazon.com/s?i=lawngarden&bbn=10158976011&page=1'
next_page = phones
current_category = phones
skip_item_search = False
if os.path.exists('/system/files/dupe_lists/') == False:
	os.makedirs('/system/files/dupe_lists/')

######################################################################################################################################################################################################################################

			#Selectable Starting URL's#

def cat_change(current_url):
	if current_url == tools:
		return computers
	if current_url == computers:
		return kitchen
	if current_url == kitchen:
		return amazon_devices
	if current_url ==  amazon_devices:
		return cameras
	if current_url == cameras:
		return video_games
	if current_url == video_games:
		return automotive
	if current_url == automotive:
		return phones
	if current_url == phones:
		return furniture
	if current_url == furniture:
		return television
	if current_url == television:
		return grocery
	if current_url == grocery:
		return baby
	if current_url == baby:
		return outdoor_cooking
	if current_url == outdoor_cooking:
		return outdoor_rec
	if current_url == outdoor_rec:
		return lawn
	if current_url == lawn:
		return tools

######################################################################################################################################################################################################################################

			#Get The Requested Variables Name#

def var_name_to_var(obj, namespace=globals()):
	return [name for name in namespace if namespace[name] is obj]

######################################################################################################################################################################################################################################

			#Getting First HTML#

def getting_HTML(requested_page):
	page = requests.get(
		requested_page,
		proxies={
	        'http': 'http://' + zyte + ':@proxy.crawlera.com:8011/',
	        'https': 'http://' + zyte + ':@proxy.crawlera.com:8011/',
	    },
		verify='/system/config/zyte-smartproxy-ca.crt'
		).text
	soup = BeautifulSoup(page, 'lxml')
	gc.collect()
	return soup

######################################################################################################################################################################################################################################

			#Page Mesh Search#
			
def quick_change(current_cat_next_url):
	global current_category
	cat = var_name_to_var(current_category)
	saved_file_path = '/system/files/' + str(cat[0]) + '.txt'
	current_category = cat_change(current_category)
	cat = var_name_to_var(current_category)
	next_file_path = '/system/files/' + str(cat[0]) + '.txt'
	with open(saved_file_path, 'w') as cat_file:
		cat_file.write(current_cat_next_url)	
	try:
		with open(next_file_path, 'r') as cat_file:
			next_url = str(cat_file.readline())
	except Exception as e:
		print(e)
		next_url = current_category
	return next_url

######################################################################################################################################################################################################################################

			#Get ASIN Loop#
			
def castor():
	global next_page, current_category, retry_count, skip_item_search
	soup = getting_HTML(next_page)
	for item_box in soup.find_all('div', class_='a-section a-spacing-base'):
		if skip_item_search == True:
			skip_item_search = False
			break
		try:
			url = None
			asin = None
			url = str(item_box.find('a', class_='s-no-outline')['href'])
			asin_next = False
			for section in url.split('/'):
				if asin_next is True:
					asin = (str(section))
					break
				if section == 'dp':
					asin_next = True
			if (
			url is None
			or asin is None
			):
				return	
			dupe_list = '/system/files/dupe_lists/' + str(var_name_to_var(current_category)[0])
			if os.path.exists(dupe_list) == False:
				with open(dupe_list, 'w') as c:
					pass
			with open(dupe_list,'r+') as ignore_list:
				ignore = False
				line_count = 0
				for line in ignore_list.readlines():
					line_count += 1
					if asin == str(line.strip('\n')):
						print('found ' + asin + ' in list')
						ignore = True
				if line_count > 50:
					subprocess.run(["/bin/bash", "-c", "sed -i -e '1d' " + dupe_list])
				ignore_list.write(asin + '\n')
				if ignore == False:
					with open('/system/files/asins.txt','a') as asins:
						asin_and_cat = asin + '^' + str(var_name_to_var(current_category)[0])
						asins.write(asin_and_cat + '\n')
		except AttributeError as e:
			print(e)
			return			
	if soup.find(class_='s-pagination-next') is None:
		retry_count += 1
		skip_item_search = True
		if retry_count < 4:
			retry_count = 0
			skip_item_search = False
			print('Category ' + str(var_name_to_var(current_category)[0]) + ' failed to many times, skipping')
			next_page = quick_change(current_category)
	elif soup.find(class_='s-pagination-next').get('href') == None:
		next_page = quick_change(current_category)
		retry_count = 0
		skip_item_search = False
		time.sleep(40)
	else:
		time.sleep(40)
		retry_count = 0
		skip_item_search = False
		next_url = 'https://www.amazon.com' + str(soup.find(class_='s-pagination-next')['href'])
		next_page = quick_change(next_url)
	gc.collect()
	return

######################################################################################################################################################################################################################################

while True:
	try:
		castor()
		datetime.now().strftime('%Y-%m-%d %H:%M:%S')
	except Exception as e:
		print(e)
	

