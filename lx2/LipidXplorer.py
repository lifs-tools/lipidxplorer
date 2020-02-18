import mfql_Parser
from MS_reader import SpectraUtil
from targets import Targets_util
import parse_adapter
import logging, os
log = logging.getLogger(os.path.basename(__file__))

if __name__ == "__main__":
    mzml_file =  'test_resources\\small_test\\190321_Serum_Lipidextract_368723_01.mzML'
    mfql_file =  'test_resources\\small_test\\170213_CE_pos_MSMS.mfql'

    mfql = mfql_Parser.fromFile(mfql_file)
    targets = [Targets_util.var2Target(var) for var in mfql['variables']]

    spectra = SpectraUtil.fromFile(mzml_file)
    MS1 = spectra
    MS2 = spectra.get_reset_copy()
    MS1.set_mode()
    MS1.set_ms_level()
    MS2.set_mode()
    MS2.set_ms_level(2)

    PR = targets[0]
    FR = targets[1]
    MS1_match = MS1.get_nearest(PR._df)
    MS2_match = MS2.get_nearest(FR._df)

    MS1_match = Targets_util.set_max_daltons(MS1_match)
    MS2_match = Targets_util.set_max_daltons(MS2_match)

    all_match = Targets_util.makeAllCombo(MS1_match, MS2_match)
    st = parse_adapter.suchthat2txt(mfql['suchthat'])
    ST = all_match.query(st)

    pr_df, fr_df = Targets_util.devideAllCombo(ST)

    sum_df = Targets_util.summaryDF(pr_df, quantile=1)

    # plt = Targets_util.lollipop_plot(pr_df.PR_m, pr_df.PR_i)
    # plt.show()
    # plt = Targets_util.lollipop_plot(fr_df.FR_m, fr_df.FR_i)
    # plt.show()

    # Targets_util.showAll_lollipop(pr_df, sample = True)

    reportCols = parse_adapter.report2exec_txt(mfql['report'])
    res = parse_adapter.reportCols2DF(reportCols, all_match)
    print(res.head())