from statsmodels.tsa.vector_ar.var_model import VAR
from statsmodels.tsa.vector_ar.vecm import coint_johansen, select_coint_rank, VECM
import warnings

def selectLagOrderDynamic(data, max_lag, criterion='aic',vecm=True):
    selected_lag_order = False
    with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            varModel = VAR(data)
            testLag = 1
            
            selectedICS = list()
            selectedOrder = list()
            while testLag <= max_lag:
                try:
                    icsValues = varModel.select_order(maxlags=testLag).ics[criterion]
                    AICorderICS = min(icsValues)
                    AICorder = icsValues.index(min(icsValues))
                    selectedICS.append(AICorderICS)
                    selectedOrder.append(AICorder)
                    '''print(icsValues)'''
                except:
                    selectedICS.append(0)
                    selectedOrder.append(0)
                testLag= testLag+1
            '''
            print("lag ICSs:"+str(selectedICS))
            print("lag orders" + str(selectedOrder))
            print("selected ICS = "+str(min(selectedICS)))
            print("index:"+str(selectedICS.index(min(selectedICS))))
            '''
            selected_lag_order = selectedOrder[selectedICS.index(min(selectedICS))]
            if vecm==True:
                selected_lag_order+1

    '''##IF YOU WANTED TO RUN COMPARISON
    varModel = VAR(data)
    varModelLagOrder = varModel.select_order(maxlags=max_lag).selected_orders["aic"]
    print("VAR Model select:" + str(varModelLagOrder))
    if(selected_lag_order!=varModelLagOrder):
        exit()'''

    return selected_lag_order