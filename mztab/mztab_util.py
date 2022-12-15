import pandas as pd
from datetime import date


def make_SMH1(dictQuery, count):

    dataDict = dictQuery.dataMatrix
    SMH_df = pd.DataFrame()

    k = next(iter(dataDict.keys()))
    SMH_df["SMH"] = ["SML"] * len(dataDict[k])
    SMH_df["SML_ID"] = SMH_df.index.values + 1
    SMH_df["SMF_ID_REFS"] = None
    SMH_df["database_identifier"] = dictQuery.name
    SMH_df["chemical_formula"] = dataDict.get("CHEMSC", None)
    SMH_df["smiles"] = None
    SMH_df["inchi"] = None
    SMH_df["chemical_name"] = None
    SMH_df["uri"] = None
    SMH_df["theoretical_neutral_mass"] = dataDict.get("MASS", None)
    SMH_df["adduct_ions"] = None
    SMH_df["reliability"] = 3  # putatively characterized compound class (3)
    SMH_df["best_id_confidence_measure"] = None
    SMH_df["best_id_confidence_value"] = None
    # TODO add abundance_assay into metadata
    for idx, k in enumerate(
        [k for k in dataDict.keys() if k.startswith("INT")], start=1
    ):
        SMH_df[f"abundance_assay[{idx}]"] = dataDict.get(k, None)
    SMH_df["abundance_study_variable[1]"] = None
    SMH_df["abundance_variation_study_variable[1]"] = dataDict.get("ERRppm", None)

    as_text = (
        SMH_df.fillna("null").to_csv(None, sep="\t", index=False).replace("\r\n", "\n")
    )
    return as_text


def make_MTD1(name):

    MTD_dict = {}
    MTD_dict["mzTab-version"] = "2.2.0-M"
    MTD_dict["mzTab-ID"] = f"LX{date.today().strftime('%Y%m%d%H%M')}-dev"
    MTD_dict["software[1]"] = "[,, lipidXplorer, 1.3.0]"

    lines = [f"MTD\t{m}\t{v}" for m, v in MTD_dict.items()]
    return "\n".join(lines)+"\n"


def make_MTD2(filename, count):

    MTD_dict = {}

    MTD_dict[f"ms_run[{count}]-location"] = filename
    MTD_dict[f"ms_run[{count}]-format"] = "[,, LipidXplorer mzTab output, 1.3.0]"
    MTD_dict[
        f"ms_run[{count}]-id_format"
    ] = "[MS, MS:1000768, Thermo nativeID format, ]"
    MTD_dict[f"ms_run[{count}]-scan_polarity[1]"] = f'[MS, MS:1000129, "positive scan", ]'
    MTD_dict[f"ms_run[{count}]-scan_polarity[2]"] = f'[MS, MS:1000129, "negative scan", ]'
    MTD_dict[f"ms_run[{count}]-format"] = "[MS, MS:1000584, mzML file, ]"

    lines = [f"MTD\t{m}\t{v}" for m, v in MTD_dict.items()]
    return "\n" + "\n".join(lines)


def make_MTD3(file_count):

    MTD_dict = {}
    MTD_dict[f"assay[1]-sample_ref"] = 'Sample[1]'
    MTD_dict[f"assay[1]-ms_run_ref"] = '|'.join((f'[ms_run[{idx}]' for idx in range(1,file_count+1)))

    # MTD_dict[f"study_variable[1]"] = 'BAL-WT'
    # MTD_dict[f"study_variable[{count+idx}]-assay_refs"] = f"assay[{count+idx}]"
    # MTD_dict[f"study_variable[{count+idx}]-description"] = f"{count+idx}"

    lines = [f"MTD\t{m}\t{v}" for m, v in MTD_dict.items()]
    return "\n" + "\n".join(lines)+"\n" 


def make_MTD4():

    MTD_dict = {}

    MTD_dict["cv[1]-label"] = "MS"
    MTD_dict["cv[1]-full_name"] = "PSI-MS controlled vocabulary"
    MTD_dict["cv[1]-version"] = "20-06-2018"
    MTD_dict["cv[1]-uri"] = "https://www.ebi.ac.uk/ols/ontologies/ms"

    MTD_dict["database[1]"] = "[,, no database, null ]"
    MTD_dict["database[1]-prefix"] = "null"
    MTD_dict["database[1]-version"] = "Unknown"
    MTD_dict["database[1]-uri"] = "null"

    MTD_dict["small_molecule-quantification_unit"] = "[,,XIC area,]"
    MTD_dict["small_molecule_feature-quantification_unit"] = "[,,XIC area,]"
    MTD_dict[
        "small_molecule-identification_reliability"
    ] = "[MS, MS:1002896, compound identification confidence level, ]"
    MTD_dict["id_confidence_measure[1]"] = "[,, Fragment presence (%), ]"
    MTD_dict[
        "quantification_method"
    ] = "[MS, MS:1001834, LC-MS label-free quantitation analysis, ]"

    lines = [f"MTD\t{m}\t{v}" for m, v in MTD_dict.items()]
    return "\n".join(lines)


def as_mztab(result):
    txt = ""
    txt += make_MTD1("_".join(result.dictQuery.keys()))
    files= [e[0] for e in result.resultSC.listFiles]
    for idx, k in enumerate(files, start=1):
        txt += make_MTD2(k, idx)
    txt += make_MTD3(len(files))
    txt += make_MTD4()
    for idx, k in enumerate(result.dictQuery, start=1):
        txt += make_SMH1(result.dictQuery[k], idx) if result.dictQuery[k].sc else ""

    return txt


def save_MZTab(txt, options):
    outfile = str(options['resultFile'])
    outfile = outfile.replace('-out.csv', '-mztab.csv')

    with open(outfile, "w") as f:
        f.write(txt)
