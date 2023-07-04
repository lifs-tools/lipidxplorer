import pandas as pd
import pickle


def listSurveyEntry2dicts(listSurveyEntry):
    for se in listSurveyEntry:
        # note anotations are 'mark':str(se.listMark), but it makes it very slow
        yield {
            **{"mass": se.precurmass, "precurmass": None},
            **se.dictIntensity,
        }
        for ms2 in se.listMSMS:
            yield {
                **{"mass": ms2.mass, "precurmass": se.precurmass},
                **ms2.dictIntensity,
            }


def scan2df(sc_filepath):
    # Read the pickle file
    with open(sc_filepath, "rb") as f:
        scan = pickle.load(f)

    # Create a DataFrame from the list
    df = pd.DataFrame(listSurveyEntry2dicts(scan.listSurveyEntry))

    return df
