import pandas as pd
import pickle

def listSurveyEntry2dicts(listSurveyEntry):
    for se in listSurveyEntry: 
        # note anotations are 'mark':str(se.listMark), but it makes it very slow
        yield {**{'mass':se.precurmass, 'precurmass':None},**se.dictIntensity}
        for ms2 in se.listMSMS:
            yield {**{'mass':ms2.mass, 'precurmass':se.precurmass},**ms2.dictIntensity}

def scan2df(sc_filepath):
    # Read the pickle file
    with open(pickle_file, 'rb') as f:
        scan = pickle.load(f)
    
    # Create a DataFrame from the list
    df = pd.DataFrame(listSurveyEntry2dicts(scan.listSurveyEntry))

    return df

# Usage example
pickle_file = r'c:\Users\mirandaa\Downloads\LX1 Dump-Out\LX1 Dump-Out\Trim.sc'
df = scan2df(pickle_file)
print(df)
