from datetime import date
import pandas as pd
from statsmodels.tsa.stattools import adfuller
from statsmodels.tsa.vector_ar.var_model import VAR
from statsmodels.tsa.vector_ar.vecm import coint_johansen, select_coint_rank, VECM
import statsmodels.tsa.stattools as ts 
import sys
import numpy as np
from arch.unitroot import PhillipsPerron
import warnings
from selectLagOrderDynamic import selectLagOrderDynamic
from tqdm import tqdm
import matplotlib.pyplot as plt
import os
import glob
from statsmodels.tsa.stattools import kpss

def stationaryTest(marketData, threshold):
    #Note that we want our data to be stationary in order to work with it. See https://towardsdatascience.com/achieving-stationarity-with-time-series-data-abd59fd8d5a0
    ADFresult = adfuller(marketData, autolag='AIC', maxlag=6)
    ADFStatistic = ADFresult[0]
    ADFp_value = ADFresult[1]
    ADFn_lags = ADFresult[2]
    if (ADFp_value>=threshold):
        ADFisStationary = 'Failed to reject H0. H0 = the data has a unit root and is non-stationary. Interpet: the data has a unit root and is non-stationary'
    else:
        ADFisStationary = 'Reject H0. H0 = the data has a unit root and is non-stationary. Interpet: the data DOES NOT have a unit root and is stationary' 
    PPresult = PhillipsPerron(marketData, trend="n")
    PPp_value = PPresult.pvalue
    PPp_lags = PPresult.lags
    if (PPp_value>=threshold):
        PPisStationary = "Fail to reject H0. H0 = " +PPresult.null_hypothesis +". Interpet: the data has a unit root and is non-stationary"
    else:
        PPisStationary = "Reject H0.  H0 = " +PPresult.null_hypothesis + ". Interpret: accept the H1. H1 = " + PPresult.alternative_hypothesis
    
    marketDiffData = marketData.diff().dropna()
    PPdiff_result  = PhillipsPerron(marketDiffData, trend="n")
    PPdiff_p_value = PPdiff_result.pvalue
    PPdiff_p_lags = PPdiff_result.lags
    if (PPdiff_p_value>=threshold):
        PP_diff_isStationary = "Fail to reject H0. H0 = " +PPdiff_result.null_hypothesis +". Interpet: the data has a unit root and is non-stationary"
    else:
        PP_diff_isStationary = "Reject H0.  H0 = " +PPdiff_result.null_hypothesis + ". Interpret: accept the H1. H1 = " + PPdiff_result.alternative_hypothesis

    KPSSresult = kpss(marketData,"ct")
    KPSSstatistic = KPSSresult[0]
    KPSSp_value = KPSSresult[1]
    KPSS_lags = KPSSresult[2]
    if (KPSSp_value>=threshold):
        KPSSisStationary = "Fail to reject H0. Interpet: the data is stationary around a trend"
    else:
        KPSSisStationary = "Reject H0. Interpret: accept the H1. H1 = Presence of unit root and is non-stationary"
    
    KPSSdiff_result = kpss(marketData.diff().dropna(),"ct")
    KPSSdiff_statistic = KPSSdiff_result[0]
    KPSSdiff_p_value = KPSSdiff_result[1]
    KPSSdiff_lags = KPSSdiff_result[2]
    if (KPSSdiff_p_value>=threshold):
        KPSSdiff_isStationary = "Fail to reject H0. Interpet: the data is stationary around a trend"
    else:
        KPSSdiff_isStationary =  "Reject H0. Interpret: accept the H1. H1 = Presence of unit root and is non-stationary"
    

    results = {"ADFStatistic":ADFStatistic,
                "ADFp_value":ADFp_value,
                "ADFisStationary":ADFisStationary,
                "ADFn_lags":ADFn_lags,
                "PPp_value":PPp_value,
                "PPn_lags":PPp_lags,
                "PPisStationary":PPisStationary,
                "PPdiff_p_value":PPdiff_p_value,
                "PPdiff_p_lags":PPdiff_p_lags,
                "PP_diff_isStationary":PP_diff_isStationary,
                "KPSSstatistic":KPSSstatistic,
                "KPSSp_value":KPSSp_value,
                "KPSSn_lags":KPSS_lags,
                "KPSSisStationary":KPSSisStationary,
                "KPSSdiff_statistic":KPSSdiff_statistic,
                "KPSSdiff_p_value":KPSSdiff_p_value,
                "KPSSdiff_lags":KPSSdiff_lags,
                "KPSSdiff_isStationary":KPSSdiff_isStationary
                }
    return results
#cite https://towardsdatascience.com/vector-autoregressions-vector-error-correction-multivariate-model-a69daf6ab618

def get_rSquared(values,residuals):
    mean = values.mean()
    TSS = ((values-mean)**2).sum()
    RSS = (residuals**2).sum()
    rSquared = 1-(RSS/TSS)
    return rSquared

srcNetworkPairs = pd.read_csv("./dataNetworks/networkMapResults.csv", thousands=',')
srcDataFilePath = "./formattedSrc/formattedSrc-deflated.csv"
maxlag = 6
generateIRFimages = False

if generateIRFimages == True:
    files = glob.glob('./cointResults/irfs/*')
    for f in files:
        os.remove(f)

srcPrices = pd.read_csv(srcDataFilePath, thousands=',',index_col="Date")
networkCointResults = pd.DataFrame()
uniqueProducts = srcNetworkPairs['Product'].unique()

for uniqueProduct in uniqueProducts:
    productNetworkDf= srcNetworkPairs.loc[srcNetworkPairs['Product'] == uniqueProduct]
    productPrices= srcPrices.loc[srcPrices['Product'] == uniqueProduct]
    print("===="+uniqueProduct+"===="+str(len(productNetworkDf)))
    for index, row in tqdm(productNetworkDf.iterrows()):
        originMarket = row['Origin']
        destMarket = row['Destination']
        
        pairData = productPrices[[originMarket,destMarket]]
        pairData = pairData.interpolate(limit_area = "inside", limit=1)
        ##applyLogs
        pairData = pairData.apply(lambda x: np.log(x) if np.issubdtype(x.dtype, np.number) else x)
        ##remove inf
        pairData = pairData.replace([np.inf, -np.inf], np.nan)

        pairData.to_csv("./cointData/presample/"+uniqueProduct +"-"+ originMarket+"-"+destMarket+".csv")

        pairData = pairData.dropna()
        pairLength = len(pairData)
        #Initial Definition of Test Results
        EGtstat = EGpvalue = EGcritValues = EGresult = johanCointegratingVectors = statOrigin_ADFStatistic = statOrigin_ADFp_value = statOrigin_ADFisStationary = statOrigin_ADFn_lags = statOrigin_PPp_value = statOrigin_PPn_lags = statOrigin_PPisStationary = statDest_ADFStatistic = statDest_ADFp_value = statDest_ADFisStationary = statDest_ADFn_lags = statDest_PPp_value = statDest_PPn_lags = statDest_PPisStationary = johan_CointTraceRank = johan_CointMaxEigRank = vecmEligible = vecm_cointegrationConstant = vecm_errorCorrectionTermB2 = vecm_vecmLength = vecm_cointegrationConstant_pvalue = vecm_errorCorrectionTermB2_pvalue = vecm_errorCorrectionTermB1 = vecm_errorCorrectionTermB1_pvalue = vecm_deterministicConfig = vecm_lagOrder = vecm_OriginGrangerCausesDest_testStatistic = vecm_OriginGrangerCausesDest_critValue = vecm_OriginGrangerCausesDest_method = vecm_test_normality_pvalue = vecm_test_whiteness_pvalue = vecm_OriginGrangerCausesDest_pValue = vecm_A_rSquared = vecm_B_rSquared = vecm_alphaOrigin = vecm_alphaOrigin_pvalue = vecm_alphaDest = vecm_alphaDest_pvalue = originLnPriceAvg = destLnPriceAvg = statOrigin_KPSSp_value = statOrigin_KPSSisStationary = statOrigin_KPSSdiff_lags = statOrigin_KPSSdiff_p_value = statOrigin_KPSS_diff_isStationary = statDest_KPSSp_value = statDest_KPSSn_lags = statDest_KPSSisStationary = statDest_KPSSdiff_p_value = statDest_KPSSdiff_lags = statDest_KPSS_diff_isStationary = statOrigin_KPSSstatistic = statOrigin_KPSSdiff_statistic = statDest_KPSSstatistic = statDest_KPSSdiff_statistic = None 

        testErrors = list()
        if(pairLength<=15):
            testErrors.append("Not Enough Obs to continue")
        else:
            #StationarityResults===========================
            statOriginResults = stationaryTest(pairData[originMarket], 0.05)
            statOrigin_ADFStatistic = statOriginResults['ADFStatistic']
            statOrigin_ADFp_value = statOriginResults['ADFp_value']
            statOrigin_ADFisStationary = statOriginResults['ADFisStationary']
            statOrigin_ADFn_lags = statOriginResults['ADFn_lags']
            statOrigin_PPp_value = statOriginResults['PPp_value']
            statOrigin_PPn_lags = statOriginResults['PPn_lags']
            statOrigin_PPisStationary = statOriginResults['PPisStationary']
            statOrigin_PPdiff_p_value = statOriginResults['PPdiff_p_value']
            statOrigin_PPdiff_p_lags = statOriginResults['PPdiff_p_lags']
            statOrigin_PP_diff_isStationary = statOriginResults['PP_diff_isStationary']
            statOrigin_KPSSstatistic = statOriginResults['KPSSstatistic']
            statOrigin_KPSSp_value = statOriginResults['KPSSp_value']
            statOrigin_KPSSn_lags = statOriginResults['KPSSn_lags']
            statOrigin_KPSSisStationary = statOriginResults['KPSSisStationary']
            statOrigin_KPSSdiff_statistic = statOriginResults['KPSSdiff_statistic']
            statOrigin_KPSSdiff_p_value = statOriginResults['KPSSdiff_p_value']
            statOrigin_KPSSdiff_lags = statOriginResults['KPSSdiff_lags']
            statOrigin_KPSS_diff_isStationary = statOriginResults['KPSSdiff_isStationary']
            
            statDestResults = stationaryTest(pairData[destMarket], 0.05)
            statDest_ADFStatistic = statDestResults['ADFStatistic']
            statDest_ADFp_value = statDestResults['ADFp_value']
            statDest_ADFisStationary = statDestResults['ADFisStationary']
            statDest_ADFn_lags = statDestResults['ADFn_lags']
            statDest_PPp_value = statDestResults['PPp_value']
            statDest_PPn_lags = statDestResults['PPn_lags']
            statDest_PPisStationary = statDestResults['PPisStationary']
            statDest_PPdiff_p_value = statDestResults['PPdiff_p_value']
            statDest_PPdiff_p_lags = statDestResults['PPdiff_p_lags']
            statDest_PP_diff_isStationary = statDestResults['PP_diff_isStationary']
            statDest_KPSSstatistic = statDestResults['KPSSstatistic']
            statDest_KPSSp_value = statDestResults['KPSSp_value']
            statDest_KPSSn_lags = statDestResults['KPSSn_lags']
            statDest_KPSSisStationary = statDestResults['KPSSisStationary']
            statDest_KPSSdiff_statistic = statDestResults['KPSSdiff_statistic']
            statDest_KPSSdiff_p_value = statDestResults['KPSSdiff_p_value']
            statDest_KPSSdiff_lags = statDestResults['KPSSdiff_lags']
            statDest_KPSS_diff_isStationary = statDestResults['KPSSdiff_isStationary']
            
            #VAR Model
            selected_lag_order = selectLagOrderDynamic(pairData, 6, criterion='aic',vecm=True)
            
            ##So both variables need to be non-stationary at I(0) and stationary at I(1) to work with them in VECM configs...
            if(statOrigin_PPp_value>0.05 and statDest_PPp_value>0.05):
                vecmEligible = True
            else:
                vecmEligible = False
            
            if(vecmEligible):
                #Engle Granger Test============================
                try:
                    #trend is either "c for constant or nc for noconstant"
                    EGresult=ts.coint(pairData[originMarket], pairData[destMarket],trend="nc", autolag="AIC",maxlag=6)
                    EGtstat = EGresult[0]
                    EGpvalue = EGresult[1]
                    EGcritValues = EGresult[2]
                    if(EGpvalue<0.10):
                        EGresult = "Cointegrated"
                    else:
                        EGresult = "Not Cointegrated"
                except:
                    testErrors.append("EngleGranger"+str(sys.exc_info()[0]))
                #Johansen Rank============================= (with order = constant(0).)
                try:
                    vec_rank1 = select_coint_rank(pairData, det_order = 0, k_ar_diff = selected_lag_order, method = 'trace', signif=0.05)
                    johan_CointTraceRank=vec_rank1.rank
                    vec_rank2 = select_coint_rank(pairData, det_order = 0, k_ar_diff = selected_lag_order, method = 'maxeig', signif=0.05)
                    johan_CointMaxEigRank=vec_rank2.rank
                except:
                    testErrors.append("Johansen"+str(sys.exc_info()[0]))
                
                #VECM model ========================
                try:
                    vecm_deterministicConfig = "(ci) constant in cointegration equation" ##(ci) constant in cointegration equation ##(n) no deterministic terms
                    vecm_lagOrder = selected_lag_order
                    deterministicTerms = "ci"
                    vecmResults = VECM(endog = pairData, k_ar_diff = selected_lag_order, coint_rank = 1, deterministic = deterministicTerms).fit()
                    with open("./cointResults/cointSummaries/"+uniqueProduct +"-"+ originMarket+"-"+destMarket+".txt",'w') as f:
                        f.write(str(vecmResults.summary()))
                    postSampleDf = pd.DataFrame(data=np.transpose(vecmResults.y_all), columns=vecmResults.names)
                    postSampleDf.to_csv("./cointData/postsample/"+uniqueProduct +"-"+ originMarket+"-"+destMarket+"-post.csv")
                    
                    originLnPriceAvg = postSampleDf[originMarket].mean()
                    destLnPriceAvg = postSampleDf[destMarket].mean()

                    vecm_alphaOrigin = vecmResults.alpha[0][0]
                    vecm_alphaDest = vecmResults.alpha[1][0]
                    vecm_alphaOrigin_pvalue =  vecmResults.pvalues_alpha[0][0]
                    vecm_alphaDest_pvalue = vecmResults.pvalues_alpha[1][0]
                    if(deterministicTerms != "n"):
                        vecm_cointegrationConstant = vecmResults.const_coint[0][0]
                        vecm_cointegrationConstant_pvalue = vecmResults.pvalues_det_coef_coint[0][0]
                    vecm_errorCorrectionTermB1 = vecmResults.beta[0][0]
                    vecm_errorCorrectionTermB1_pvalue = vecmResults.pvalues_beta[0][0]
                    vecm_errorCorrectionTermB2 = vecmResults.beta[1][0]
                    vecm_errorCorrectionTermB2_pvalue = vecmResults.pvalues_beta[1][0]
                    vecm_vecmLength = vecmResults.nobs
                    vecm_test_normality_pvalue = vecmResults.test_normality().pvalue
                    vecm_test_whiteness_pvalue = vecmResults.test_whiteness(adjusted=True).pvalue

                    
                    postSampleResid = pd.DataFrame(data=vecmResults.resid, columns=vecmResults.names)
                    vecm_A_rSquared = get_rSquared(postSampleDf[originMarket],postSampleResid[originMarket])
                    vecm_B_rSquared = get_rSquared(postSampleDf[destMarket],postSampleResid[destMarket])

                    #VECM Granger Causality
                    granger_causality_results = vecmResults.test_granger_causality(caused=destMarket, causing=originMarket)
                    vecm_OriginGrangerCausesDest_pValue = granger_causality_results.pvalue
                    vecm_OriginGrangerCausesDest_testStatistic = granger_causality_results.test_statistic
                    vecm_OriginGrangerCausesDest_critValue = granger_causality_results.crit_value
                    vecm_OriginGrangerCausesDest_method = granger_causality_results.method

                    #IRFs
                    irfs = vecmResults.irf(5).irfs
                    if(generateIRFimages==True):
                        vecmResults.irf(20).plot().savefig("./cointResults/irfs/"+uniqueProduct +"-"+ originMarket+"-"+destMarket+".png")
                        plt.close('all')
                except:
                    testErrors.append("VECM"+str(sys.exc_info()[0]))
        results = { "Product":uniqueProduct,
                    "Origin":originMarket,
                    "Destination":destMarket,
                    "Helper":uniqueProduct+originMarket+destMarket,
                    "pairLength":pairLength,
                    "statOrigin_ADFStatistic":statOrigin_ADFStatistic,
                    "statOrigin_ADFp_value":statOrigin_ADFp_value,
                    "statOrigin_ADFisStationary":statOrigin_ADFisStationary,
                    "statOrigin_ADFn_lags":statOrigin_ADFn_lags,
                    "statOrigin_PPp_value":statOrigin_PPp_value,
                    "statOrigin_PPn_lags":statOrigin_PPn_lags,
                    "statOrigin_PPisStationary":statOrigin_PPisStationary,
                    "statOrigin_PPdiff_p_value":statOrigin_PPdiff_p_value,
                    "statOrigin_PPdiff_p_lags":statOrigin_PPdiff_p_lags,
                    "statOrigin_PP_diff_isStationary":statOrigin_PP_diff_isStationary,
                    "statOrigin_KPSSstatistic": statOrigin_KPSSstatistic,
                    "statOrigin_KPSSp_value":statOrigin_KPSSp_value,
                    "statOrigin_KPSSn_lags":statOrigin_KPSSn_lags,
                    "statOrigin_KPSSisStationary":statOrigin_KPSSisStationary,
                    "statOrigin_KPSSdiff_statistic": statOrigin_KPSSdiff_statistic,
                    "statOrigin_KPSSdiff_p_value":statOrigin_KPSSdiff_p_value,
                    "statOrigin_KPSSdiff_lags":statOrigin_KPSSdiff_lags,
                    "statOrigin_KPSS_diff_isStationary":statOrigin_KPSS_diff_isStationary,
                    "statDest_ADFStatistic":statDest_ADFStatistic,
                    "statDest_ADFp_value":statDest_ADFp_value,
                    "statDest_ADFisStationary":statDest_ADFisStationary,
                    "statDest_ADFn_lags":statDest_ADFn_lags,
                    "statDest_PPp_value":statDest_PPp_value,
                    "statDest_PPn_lags":statDest_PPn_lags,
                    "statDest_PPisStationary":statDest_PPisStationary,
                    "statDest_PPdiff_p_value":statDest_PPdiff_p_value,
                    "statDest_PPdiff_p_lags":statDest_PPdiff_p_lags,
                    "statDest_PP_diff_isStationary":statDest_PP_diff_isStationary,
                    "statDest_KPSSstatistic":statDest_KPSSstatistic,
                    "statDest_KPSSp_value":statDest_KPSSp_value,
                    "statDest_KPSSn_lags":statDest_KPSSn_lags,
                    "statDest_KPSSisStationary":statDest_KPSSisStationary,
                    "statDest_KPSSdiff_statistic":statDest_KPSSdiff_statistic,
                    "statDest_KPSSdiff_p_value":statDest_KPSSdiff_p_value,
                    "statDest_KPSSdiff_lags":statDest_KPSSdiff_lags,
                    "statDest_KPSS_diff_isStationary":statDest_KPSS_diff_isStationary,
                    "vecmEligible":vecmEligible,
                    "EngleGranger_tStat": str(EGtstat),
                    "EngleGranger_pValue": str(EGpvalue),
                    "EngleGranger_critValues": str(EGcritValues),
                    "EngleGranger_results": EGresult,
                    "johan_CointTraceRank": johan_CointTraceRank,
                    "johan_CointMaxEigRank": johan_CointMaxEigRank,
                    "vecm_lagOrder":vecm_lagOrder, 
                    "vecm_deterministicConfig":vecm_deterministicConfig,
                    "vecm_alphaOrigin":vecm_alphaOrigin,
                    "vecm_alphaOrigin_pvalue":vecm_alphaOrigin_pvalue,
                    "vecm_alphaDest":vecm_alphaDest,
                    "vecm_alphaDest_pvalue":vecm_alphaDest_pvalue,
                    "vecm_cointegrationConstant": vecm_cointegrationConstant,
                    "vecm_cointegrationConstant_pvalue": vecm_cointegrationConstant_pvalue,
                    "vecm_errorCorrectionTermB1": vecm_errorCorrectionTermB1,
                    "vecm_errorCorrectionTermB1_pvalue": vecm_errorCorrectionTermB1_pvalue,
                    "vecm_errorCorrectionTermB2": vecm_errorCorrectionTermB2,
                    "vecm_errorCorrectionTermB2_pvalue": vecm_errorCorrectionTermB2_pvalue,
                    "vecm_vecmLength": vecm_vecmLength,
                    "vecm_A_rSquared": vecm_A_rSquared ,
                    "vecm_B_rSquared" : vecm_B_rSquared,
                    "vecm_test_whiteness_pvalue" : vecm_test_whiteness_pvalue,
                    "vecm_test_normality_pvalue" : vecm_test_normality_pvalue,
                    "vecm_OriginGrangerCausesDest": vecm_OriginGrangerCausesDest_pValue,
                    "vecm_OriginGrangerCausesDest_testStatistic" : vecm_OriginGrangerCausesDest_testStatistic,
                    "vecm_OriginGrangerCausesDest_critValue" : vecm_OriginGrangerCausesDest_critValue,
                    "vecm_OriginGrangerCausesDest_method" : vecm_OriginGrangerCausesDest_method,
                    "originLnPriceAvg":originLnPriceAvg,
                    "destLnPriceAvg":destLnPriceAvg,
                    "Errors":str(testErrors)
                    }
        results = pd.DataFrame.from_dict([results])
        networkCointResults = pd.concat([networkCointResults, results])

print("---OUTPUT TO /cointResults/networkCointResults.csv---")
networkCointResults.to_csv("./cointResults/networkCointResults.csv")