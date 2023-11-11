import mysql.connector
import time
import socketio
import os.path
import os
from paapi5_python_sdk.api.default_api import DefaultApi
from paapi5_python_sdk.models.condition import Condition
from paapi5_python_sdk.models.get_items_request import GetItemsRequest
from paapi5_python_sdk.models.get_items_resource import GetItemsResource
from paapi5_python_sdk.models.partner_type import PartnerType
from paapi5_python_sdk.rest import ApiException
from datetime import date
from decimal import *
import subprocess
import athos_lock

######################################################################################################################################################################################################################################

cred = athos_lock.load_config()
sql_ip = '10.0.80.1'
sql_user = cred[1]
sql_pass = cred[2]
sql_db = cred[3]
amazon_access_key = cred[4]
amazon_secret_key = cred[5]
amazon_partner_tag = cred[6]
sio = socketio.Client()
wss_location = 'http://10.0.80.2:8000/live'
sio.connect(wss_location)
print('Athos Connected')
cat = 'Amazon_Warehouse'


######################################################################################################################################################################################################################################

def parse_response(item_response_list):
	mapped_response = {}
	for item in item_response_list:
		mapped_response[item.asin] = item
	return mapped_response

######################################################################################################################################################################################################################################

def sql_connect():
	mydb = mysql.connector.connect(
	  host=sql_ip,
	  user=sql_user,
	  password=sql_pass,
	  database=sql_db
	)
	return mydb

######################################################################################################################################################################################################################################

def sql_add(item_name, item_sale_price, item_price, item_url, item_asin, item_pic, cat, date):
	today = date.today()
	mydb = sql_connect()
	mycursor = mydb.cursor() 
	val = (item_name, item_sale_price, item_price, item_url, item_asin, item_pic, 1, cat, today)
	sql = 'INSERT INTO item_information (name, sale_price, reg_price, url, asin, pic_url, active, category, date) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)'
	mycursor.execute(sql, val)
	mydb.commit()

######################################################################################################################################################################################################################################

def read_loop():
	ten_asin = []
	x = 0
	while x < 10:
		with open('/system/files/asins.txt','r') as asin_file:
			for line in asin_file:
				if x > 9:
					break
				if line is not None:
					ten_asin.append(str(line.strip('\n')))
					subprocess.run(["/bin/bash", "-c", "sed -i -e '1d' /system/files/asins.txt"])
					x += 1
				else:
					pass
	return ten_asin
	
######################################################################################################################################################################################################################################

def get_cat(the_list, asin):
	for i, s in enumerate(the_list):
		if asin in s:
			return s.split('^')[1]
	return 'no_category'

######################################################################################################################################################################################################################################

def get_items():
	try:
		full_item_info = read_loop()
		item_ids = []
		for just_asin in full_item_info:
			item_ids.append(just_asin.split('^')[0])

		host = 'webservices.amazon.com'
		region = 'us-east-1'
		default_api = DefaultApi(
			access_key=amazon_access_key, secret_key=amazon_secret_key, host=host, region=region
		)
		get_items_resource = [
			GetItemsResource.ITEMINFO_TITLE,
			GetItemsResource.OFFERS_LISTINGS_PRICE,
			GetItemsResource.OFFERS_SUMMARIES_LOWESTPRICE,
			GetItemsResource.OFFERS_SUMMARIES_OFFERCOUNT,
			GetItemsResource.IMAGES_PRIMARY_MEDIUM,
		]
		try:
			get_items_request = GetItemsRequest(
				partner_tag=amazon_partner_tag,
				partner_type=PartnerType.ASSOCIATES,
				marketplace='www.amazon.com',
				item_ids=item_ids,
				resources=get_items_resource,
			)
		except ValueError as exception:
			print('Error in forming GetItemsRequest: ', exception)
			return
		response = default_api.get_items(get_items_request)
		if response.items_result is not None:
			response_list = parse_response(response.items_result.items)
			if __name__ == '__main__':
				pass
			for item_id in item_ids:
				if item_id in response_list:
					item = response_list[item_id]
					if item is not None:
						if item.asin is not None:
							item_asin = item.asin
							if item.detail_page_url is not None:
								item_url = item.detail_page_url + '&aod=1&ie=UTF8&condition=ALL'
								
								
								if (
									item.item_info is not None
									and item.item_info.title is not None
									and item.item_info.title.display_value is not None
								):
									item_name = item.item_info.title.display_value
									
									
									if (
										item.offers is not None
										and item.offers.listings is not None
										and item.offers.listings[0].price is not None
										and item.offers.listings[0].price.display_amount is not None
										
									):
										item_price = item.offers.listings[0].price.display_amount
										item_price_raw = float(item_price.replace('$','').replace(',',''))
										if (
											item.offers.listings[0].price.savings is not None
											and item.offers.listings[0].price.savings.amount is not None
										):
											item_price = '$' + str(Decimal(item.offers.listings[0].price.savings.amount).quantize(Decimal('.01')) + Decimal(item_price.replace('$','').replace(',','')))
											item_price_raw = float(item_price.replace('$','').replace(',',''))
											if (
												item.images is not None
												and item.images.primary is not None
												and item.images.primary.medium is not None
												and item.images.primary.medium.url is not None
											):
												item_pic = item.images.primary.medium.url
												if (
													item.offers.summaries is not None
													and item.offers.summaries[0].lowest_price is not None
													and item.offers.summaries[0].lowest_price.display_amount is not None
												):
													
													for offers in item.offers.summaries:
														offers_list =[]
														offer_number = 0
														offer_price = item.offers.summaries[offer_number].lowest_price.display_amount
														if offer_price != item_price:
															offers_list.append(offer_price)
														if offers_list:
															item_sale_price = min(offers_list)
															item_sale_price_raw = float(item_sale_price.replace('$','').replace(',',''))
														offer_number += 1
													if (
														item_sale_price_raw > 0.0
														and item_price_raw > 0.0
														and item_price_raw > item_sale_price_raw
														and offers_list
													):
														item_percent_off = str(int((item_price_raw - item_sale_price_raw) / item_price_raw * 100)) + '%'
														time.sleep(1)
														sio.emit('new_deal', {
														'item_name': item_name,
														'item_price': item_price,
														'item_sale_price': item_sale_price,
														'item_url': item_url,
														'item_pic': item_pic,
														'item_percent_off': item_percent_off
														})
														cat = get_cat(full_item_info, item_asin)
														sql_add(item_name, item_sale_price, item_price, item_url, item_asin, item_pic, cat, date)
				else:
					print('Item not found, check errors')
		if response.errors is not None:
			print('\nPrinting Errors:\nPrinting First Error Object from list of Errors')
			print('Error code', response.errors[0].code)
			print('Error message', response.errors[0].message)
	except ApiException as exception:
		print('Error calling PA-API 5.0!')
		print('Status code:', exception.status)
		print('Errors :', exception.body)
		print('Request ID:', exception.headers['x-amzn-RequestId'])
	except TypeError as exception:
		print('TypeError :', exception)
	except ValueError as exception:
		print('ValueError :', exception)
	except Exception as exception:
		print('Exception :', exception)
	time.sleep(1)

######################################################################################################################################################################################################################################

while True:
	try:
		get_items()
	except Exception as e:
		print(e)

