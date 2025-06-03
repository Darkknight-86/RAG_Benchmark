import yliveticker
import helpers
import time


def on_new_msg(ws, msg):
    #print(f"Msg: {msg}")
    asx_open_status = helpers.is_asx_open()
    
    print("round(xxx, " + str(msg['priceHint']) + ")")
    
    pre_s3_format = {
        'security': str(msg['id']),
        'price': round(msg['price'], msg['priceHint']),
        'changePercent': round(msg['changePercent'], int(msg['priceHint'])),
        'tradeVolume': int(msg['dayVolume']),
        'isMarketOpen': asx_open_status['is_open'],
        'marketStatus': asx_open_status['status'],
        'timestamp': helpers.epoch_to_json_date(msg['timestamp'])
    }
    
    file_name = str(msg['id']) + "-" + str(round(time.time())) + ".json"
    helpers.upload_to_s3(file_name, pre_s3_format)
    
    print("[DEBUG] inserted 1 record to S3, w/ title of " + file_name)

# {
#     'id': 'WBC.AX',
#     'exchange': 'ASX',
#     'quoteType': 8,
#     'price': 32.619998931884766,
#     'timestamp': 1748931012000,
#     'marketHours': 1,
#     'changePercent': 1.3673045635223389,
#     'dayVolume': 0,
#     'change': 0.4399986267089844,
#     'priceHint': 2
# }

# Meaning of the JSON above:
# priceHint: how many decimals should be shown for the price
#            (keep in mind prices are in AUD)
# dayVolume: amount traded today, will be 0 if after hours
# quoteType: should always be 8 for equity (stock)


# Format that will be uploaded to Amazon S3:


yliveticker.YLiveTicker(
    on_ticker=on_new_msg,
    ticker_names=["CBA.AX", "BHP.AX", "WBC.AX", "NAB.AX", "ANZ.AX"]
)
