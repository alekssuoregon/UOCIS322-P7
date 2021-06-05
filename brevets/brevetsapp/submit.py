#This has all the logic for processing a submit to database request
#It expects data to be passed in python dict form and returns a response dict.
def process_submit(brevet_entry):
    return_json = {'success': False}
    prev_km = 2000
    #Iterate over controls backwards so removals don't affect iteration
    for i in range(len(brevet_entry['controls'])-1, -1, -1):
        km_str = brevet_entry['controls'][i]['km']
        #Remove empty entries
        if km_str == '':
            del brevet_entry['controls'][i]
        else:
            #Check for possible errors
            km = int(km_str)
            if km > prev_km:
                return_json['error'] = "Brevet controls out of order"
                return return_json
            elif km == prev_km:
                return_json['error'] = "Repeat brevet of value: " + km_str
                return return_json
            prev_km = km

    #Check to make sure the request was not empty
    if len(brevet_entry['controls']) != 0:
        return_json['success'] = True
    else:
        return_json['error'] = "No brevet controls input"
    return return_json


