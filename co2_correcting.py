# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""
####################################################################################
### Routine de correction des données CO2 à partir du fichier journalier nettoyé ###
# Attention la première ligne et dernière ligne du fichier doivent être non nulles #
##################################### WEBOBS #######################################
####################################################################################

##################################
### Importation des librairies ###
##################################

import csv
import os
import datetime as dt
import numpy as np
import pandas as pd
from scipy.fftpack import fft, rfft, irfft, fftfreq
import statsmodels.api as sm
import copy
from collections import OrderedDict
from co2_filtering.data.DataAccessor import DataAccessor
from co2_filtering.configuration.Configuration import Configuration


# Loading configuration
conf_start = Configuration("./resources")
# conf_start.show_configuration()

# DataAccessor instanciation
data_accessor = DataAccessor(conf_start.get_host(),
                             conf_start.get_user(),
                             conf_start.get_password(),
                             conf_start.get_database())

# Common output attributes for all stations
attributes = OrderedDict()
attributes['Date'] = 'DATETIME NOT NULL'
attributes['CO2_raw'] = 'DOUBLE'
attributes['CO2_corr'] = 'DOUBLE'
attributes['CO2_filter7'] = 'DOUBLE'
attributes['CO2_filter15'] = 'DOUBLE'
attributes['CO2_filter31'] = 'DOUBLE'
attributes['CO2_filterSG_1'] = 'DOUBLE'
attributes['CO2_filterSG_2'] = 'DOUBLE'

#############################
### Répertoire du fichier ###
#############################

path = "./PCRN.csv" # Fichier PCRN 22 août 2013
pathb = "./PNRN.csv" # Fichier PNRN 9 octobre 2014
pathc = "./PNRNfirst.csv"# Fichier PNRN 21 mars 2014
pathd = "./BLEN.csv"# Fichier BLEN 4 novembre 2016

###########################################################
### Définitions des paramètres propres à chaque station ###
###########################################################

### Paramètres de régression linéaire ###
# PCRN
Ta=-0.0679 # Slope of the equation for linear regression
Tc=1.6226 # Constant of the equation for linear regression
# PNRN
Tab=0.0009 # Slope of the equation for linear regression
Tcb=0.0457 # Constant of the equation for linear regression
Vab=-0.1253 # Slope of the equation for linear regression
Vcb=1.7253 # Constant of the equation for linear regression
# BLEN
Vad=0.0623 # Slope of the equation for linear regression
Vcd=0.4742 # Constant of the equation for linear regression
Tad=-0.0326 # Slope of the equation for linear regression
Tcd=1.2252 # Constant of the equation for linear regression

### Paramètres de filtrage GB ###
dayslon=31 # Nombre de jours pour la moyenne glissante (doit être impair)
daysmed=15 # Nombre de jours pour la moyenne glissante (doit être impair)
dayssho=7 # Nombre de jours pour la moyenne glissante (doit être impair)
dmax=420 # Filtrage saisonnier (fréquence de jour max)
dmin=280 # Filtrage saisonnier (fréquence de jour min)

### Paramètres de filtrage SG ###
# PCRN
sho=31 #Not modify
med=180
lon=361
# PNRN
shob=31 #Not modify
medb=175
lonb=351
# BLEN
shod=31 #Not modify
medd=45
lond=316

############################################
### Définition des principales fonctions ###
############################################

def movingaverage(values,window): ### Valeurs moyennées avec fenêtre souhaitée
    weigths = np.repeat(1.0, window)/window
    smas = np.convolve(values, weigths, 'valid')
    return smas # Donne une liste

def reg_m(endogene, exogene): ### Affiche les valeurs de la régression linéaire
    ones = np.ones(len(exogene[0]))
    X = sm.add_constant(np.column_stack((exogene[0], ones)))
    for ele in exogene[1:]:
        X = sm.add_constant(np.column_stack((ele, X)))
    results = sm.OLS(endogene, X).fit()
    return results

def dateliste (acces): ### Liste de dates complètes
    f = open(acces)
    next(f)    
    date=[]
    for line in f: 
        line = line.rstrip()
        lis = line.split(";") # Séparateur dans le fichier d'entrée
        date.append(lis[0]) 
    return [dt.datetime.strptime(i,'%d/%m/%y').date() for i in date]
    f.close()
    
def interpolate (acces,column): ### Liste des listes de valeurs interpolées et indices
    f = open(acces)
    next(f)
    L = [] # Liste des valeurs de la colonne
    indice = [] # Liste des indices des données manquantes interpolées
    nb = 0
    for line in f: 
        line = line.rstrip()
        lis = line.split(";") # Séparateur dans le fichier d'entrée
        if lis[column] == "":
            L.append(np.nan)
            indice.append(nb)
        else:
            L.append(float(lis[column]))
        nb = nb+1
    table = np.asarray(L) # Convertit la liste en table
    array = pd.Series(table).interpolate().values # Interpolation linéaire des trous
    liste = array.tolist() # Convertit la table en liste
    return liste, indice
    f.close()

def gap(*args): # Identifie l'indice des données manquantes
    resulting_list = list(args[0])
    for i in args:
        resulting_list.extend(x for x in i if x not in resulting_list)
    return sorted(resulting_list)

def fftcp (C,fmin,fmax):# Applique un filtre coupe bande sur une liste entre fmin and fmax
    timef = np.linspace(0,1,len(C)) # Abcisse temporelle
    signal = np.asarray(C) # Conversion de la liste de données en table
    W = fftfreq(signal.size, d=(timef[1]-timef[0])) # Conversion en fréquence sur la plage temporelle at analyse fréquentielle
    f_signal = rfft(signal) # Analyse spectrale
    cut_f_signal1 = f_signal.copy() # Coupe bande sur les valeurs souhaitée
    cut_f_signal2 = f_signal.copy()
    cut_f_signal = f_signal.copy()
    cut_f_signal1[(W>float((2*signal.size)/fmax))] = 0
    cut_f_signal2[(W<float((2*signal.size)/fmin))] = 0
    for i in range(0,signal.size-1):
        if cut_f_signal[i]!=cut_f_signal1[i] and cut_f_signal[i]!=cut_f_signal2[i] :
            cut_f_signal[i]=cut_f_signal1[i]
        else:
            cut_f_signal[i]=cut_f_signal[i]
    cut_signal = irfft(cut_f_signal) # FFT inverse
    return np.array(cut_signal).tolist() # Liste des données 

def RunningAverages(v,w): # Moyenne glissante SG créant directement les vides
    m=int(w/2); n=len(v); rave=np.zeros(n);
    for i in range(0,n):
        med=0; nn=0;
        for j in range(i-m,i+m):
            if (j>0 and j<n and np.isnan(v[i])==0): med=med+v[j]; nn=nn+1;
        if (nn>0): rave[i]=med/(nn);
        else: rave[i]=np.NaN;
    return rave;
    
def Normalize(x): # Normalisation entre 0 et 1
    n=len(x); mi=np.nanmin(x); ma=np.nanmax(x);
    r=ma-mi;
    for i in range(0,n):
        if (np.isnan(x[i])==False): x[i]=(x[i]-mi)/r;
        else: x[i]=0;
    return x;

def RunningDerivates(x): # Création d'une dérivée pour trouver les pics
    n=len(x); de=np.zeros(n); k=0; d0=np.NaN; 
    for i in range(0,n-1):
        if (np.isnan(x[i])==0): d0=x[i]; k=i; break;
    for i in range(0,n):
        de[i]=np.NaN;   
        if (np.isnan(x[i])==0 and i>k): de[i]=x[i]-d0; d0=x[i]; k=i;
    return de;

def FindPeaks(x,y): # Renvoie le pic principal sur une courbe en se basant sur la dérivée
    d=RunningDerivates(y); t=[]; b=[];
    n=len(d); a=0; i0=0; i1=0;
    if (d[1]>0): t.append(-1); b.append(0);
    for i in range(1,n):
        if (d[i]>0):
            if (a<0): t.append(int(i1)); b.append(int(i0));
            i1=i; a=1;
        if (d[i]<0): i0=i; a=-1;
    if (d[n-1]>0): t.append(int(n-1)); b.append(-1);
    return t,b;

def Spectrum(x,leg,N): # Analyse spectrale du signal et renvoie les trois fréquences de plus forte amplitude, possibilité de tracer en retirant #
    n=len(x);
    yf=fft(x); yf=2.0/N*np.abs(yf[0:N/2]);
    xf=np.fft.fftfreq(n,d=1);
    #plt.plot(xf[0:N/2],yf[0:N/2]);
    [x,y]=FindPeaks(xf[0:N/2],yf[0:N/2]);
    #plt.legend([leg]);
    n=len(x);
    for j in range(0,4):
        p=0; k=-1;
        for i in range(0,n):
            if (x[i]>-1):
                if (p<yf[x[i]]): p=yf[x[i]]; k=i;
        if (k>-1):
            if (xf[x[k]]==0): period='inf';
            else: period=str(int(1/xf[x[k]])); print period;
            #plt.text(xf[x[k]],yf[x[k]],period); 
            x[k]=-1;
            
def filter_season_SG (X, t1, t2, t3): # Filtre de SG sur raw avec trois temps (moyenne 31, intermediate et long frequency)
    SPfilt=RunningAverages(X,t1); # Short period filter
    LPfilt=RunningAverages(SPfilt,t3); # Long period
    MPsx=SPfilt-LPfilt; # Short period filter-Long period filter
    Season=RunningAverages(MPsx,t2); # Seasonal component
    NoSeaNoLP=X-Season-LPfilt; # Remove seasonality and LP from signal
    return sum([[np.nan]*(t1/2), movingaverage(LPfilt,t1).tolist(), [np.nan]*(t1/2)], []),sum([[np.nan]*(t1/2), movingaverage(NoSeaNoLP,t1).tolist(), [np.nan]*(t1/2)], []) # Moving average

def clean_dataset (interpoind, *args): # Nettoie le fichier des points interpolés
    for L in args:    
        for i in sorted(interpoind, reverse=True):
            del L[i]
    return args

def two_stations (Cmov1,Cmov2,jour1,jour2): # Créer une liste unique de date et de CO2 normalisé représentative de tout le réseau
    # Normaliser chaque série du réseau
    normCmov1 = [(q-np.nanmin(Cmov1))/(np.nanmax(Cmov1)-np.nanmin(Cmov1)) for q in Cmov1]
    normCmov2 = [(q-np.nanmin(Cmov2))/(np.nanmax(Cmov2)-np.nanmin(Cmov2)) for q in Cmov2]
    L = [normCmov1,normCmov2]
    # Convertir les dates en strings
    JOUR = [[i.strftime('%Y-%m-%d') for i in jour1],[i.strftime('%Y-%m-%d') for i in jour2]]
    # Sélectionner la série la plus courte (station récente)
    LST = [len(normCmov1), len(normCmov2)]
    indicemin = LST.index(min(len(normCmov1), len(normCmov2)))
    # Créer les listes si une valeur existe pour cette date sur chaque station sinon vide
    Norm = []
    Jour = []
    for i in range (0,len(L[indicemin])):
        if (JOUR[indicemin][i] in JOUR[0]) and (JOUR[indicemin][i] in JOUR[1]):
            Norm.append((L[0][JOUR[0].index(JOUR[indicemin][i])]+L[1][JOUR[1].index(JOUR[indicemin][i])])/2)
            Jour.append(JOUR[indicemin][i])
        else:
            None
    return [Normalize(Norm),Jour]

def three_stations (Cmov1,Cmov2,Cmov3,jour1,jour2,jour3): # Créer une liste unique de date et de CO2 normalisé représentative de tout le réseau
    # Normaliser chaque série du réseau
    normCmov1 = [(q-np.nanmin(Cmov1))/(np.nanmax(Cmov1)-np.nanmin(Cmov1)) for q in Cmov1]
    normCmov2 = [(q-np.nanmin(Cmov2))/(np.nanmax(Cmov2)-np.nanmin(Cmov2)) for q in Cmov2]
    normCmov3 = [(q-np.nanmin(Cmov3))/(np.nanmax(Cmov3)-np.nanmin(Cmov3)) for q in Cmov3]
    L = [normCmov1,normCmov2,normCmov3]
    # Convertir les dates en strings
    JOUR = [[i.strftime('%Y-%m-%d') for i in jour1],[i.strftime('%Y-%m-%d') for i in jour2],[i.strftime('%Y-%m-%d') for i in jour3]]
    # Sélectionner la série la plus courte (station récente)
    LST = [len(normCmov1), len(normCmov2), len(normCmov3)]
    indicemin = LST.index(min(len(normCmov1), len(normCmov2), len(normCmov3)))
    # Créer les listes si une valeur existe pour cette date sur chaque station sinon vide
    Norm = []
    Jour = []
    for i in range (0,len(L[indicemin])):
        if (JOUR[indicemin][i] in JOUR[0]) and (JOUR[indicemin][i] in JOUR[1]) and (JOUR[indicemin][i] in JOUR[2]):
            Norm.append((L[0][JOUR[0].index(JOUR[indicemin][i])]+L[1][JOUR[1].index(JOUR[indicemin][i])]+L[2][JOUR[2].index(JOUR[indicemin][i])])/3)
            Jour.append(JOUR[indicemin][i])
        else:
            None
    return [Normalize(Norm),Jour]

def fichier_intermediate (finalfile,jour1,jour2,raw1,raw2): # Créer les fichiers de sortie à exporter pour WebObs
    with open(finalfile, "w") as ff:
        L = ["Date","CO2_raw"]
        w = csv.writer(ff, delimiter=";", lineterminator="\n")
        w.writerow(L)
        w.writerows(zip(jour1+jour2, raw1+raw2))
        
def fichier_sortie (finalfile, jour, raw, corr, filter7, filter15, filter31, SG1, SG2): # Créer les fichiers de sortie à exporter pour WebObs
    with open(finalfile, "w") as ff:
        L = ["Date","CO2_raw","CO2_corr","CO2_filter7","CO2_filter15","CO2_filter31","CO2_filterSG_1","CO2_filterSG_2"]
        w = csv.writer(ff, delimiter=";", lineterminator="\n")
        w.writerow(L)
        w.writerows(zip(jour, raw, corr, filter7, filter15, filter31, SG1, SG2))

############################################################
### MAIN FOR PCRN (TO MODIFY ACCORDING THE COLUMN PLACE) ###
############################################################

# Extraire les données en liste et regarder les données manquantes
jour = dateliste(path) # Liste des dates complètes
Craw = interpolate(path,1)[0] # List des valeurs de CO2 interpolées
temp = interpolate(path,2)[0] # List des valeurs de température interpolées
pluv = interpolate(path,3)[0] # List des données pluvios interpolées
missingind = gap(interpolate(path,1)[1],interpolate(path,2)[1]) # Liste des indices de manque de données dans Craw et paramètres de corrections
# Modèle de correction PITON DE LA FOURNAISE (G. BOUDOIRE)
print "PCRN temp", reg_m(Craw, [temp]).summary() # Affiche coeff à actualiser
Ccorr = [Craw[i]-(Ta*temp[i]+Tc)+(Ta*np.mean(temp)+Tc) for i in range (0,len(Craw))] # Correction par régression linéaire du CO2
Cfilt = fftcp(Ccorr,dmin,dmax) # Filtrage des données
Cmov31 = sum([[np.nan]*(dayslon/2), movingaverage(Cfilt,dayslon).tolist(), [np.nan]*(dayslon/2)], []) # Moving average
Cmov15 = sum([[np.nan]*(daysmed/2), movingaverage(Cfilt,daysmed).tolist(), [np.nan]*(daysmed/2)], []) # Moving average
Cmov7 = sum([[np.nan]*(dayssho/2), movingaverage(Cfilt,dayssho).tolist(), [np.nan]*(dayssho/2)], []) # Moving average
# Modèle de correction ETNA (S. GURRIERI)
print "Main Spectral Components", Spectrum(Craw,"Days",400)
Cmovsho1,Cmovsho2 = filter_season_SG(Craw,sho,med,lon)
# Nettoyer la base des données interpolées et fichier de sortie
jour2=copy.copy(jour) # Crée une copie de jour sinon écrase les listes avec ligne suivante
Crawf, Ccorrf, Cmov31f, Cmov15f, Cmov7f, Cmovsho1f, Cmovsho2f, jourf, pluvf = clean_dataset(missingind,Craw,Cfilt,Cmov31,Cmov15,Cmov7,Cmovsho1,Cmovsho2,jour2,pluv) # Supprimer les données interpolées de CO2 raw, CO2 final, Temp et Pluvio
fichier_sortie("PCRN_WebObs.csv", jourf, Crawf, Ccorrf, Cmov7f, Cmov15f, Cmov31f, Cmovsho1f, Cmovsho2f)
data_accessor.create_table('pcrn_elaborated', attributes)
data_accessor.insert_data('pcrn_elaborated', attributes, (jourf, Crawf, Ccorrf,
                                                          Cmov7f, Cmov15f,
                                                          Cmov31f, Cmovsho1f,
                                                          Cmovsho2f))


############################################################
### MAIN FOR PNRN (TO MODIFY ACCORDING THE COLUMN PLACE) ###
############################################################

### Première partie du fichier lorsque les paramètres météo n'étaient pas bons ###
# Extraire les données en liste et regarder les données manquantes
jourc = dateliste(pathc) # Liste des dates complètes pour la première partie des données
Crawc = interpolate(pathc,1)[0] # List des valeurs de CO2 interpolées
missingindc = interpolate(pathc,1)[1]
Cmov31c = sum([[np.nan]*(dayslon/2), movingaverage(Crawc,dayslon).tolist(), [np.nan]*(dayslon/2)], []) # Moving average
Cmov15c = sum([[np.nan]*(daysmed/2), movingaverage(Crawc,daysmed).tolist(), [np.nan]*(daysmed/2)], []) # Moving average
Cmov7c = sum([[np.nan]*(dayssho/2), movingaverage(Crawc,dayssho).tolist(), [np.nan]*(dayssho/2)], []) # Moving average
# Nettoyer la base des données interpolées et fichier de sortie
jour2c=copy.copy(jourc) # Crée une copie de jour sinon écrase les listes avec ligne suivante
Crawfc,Cmov31cf,Cmov15cf,Cmov7cf,jourfc = clean_dataset(missingindc,Crawc,Cmov31c,Cmov15c,Cmov7c,jour2c) # Supprimer les données interpolées de CO2 raw, CO2 final, Temp et Pluvio

### Deuxième partie du fichier lorsque les paramètres météo étaient bons ###
# Extraire les données en liste et regarder les données manquantes
jourb = dateliste(pathb) # Liste des dates complètes
Crawb = interpolate(pathb,1)[0] # List des valeurs de CO2 interpolées
tempb = interpolate(pathb,2)[0] # List des valeurs de température interpolées
pluvb = interpolate(pathb,3)[0] # List des données pluvios interpolées
ventb = interpolate(pathb,4)[0]
missingindb = gap(interpolate(pathb,1)[1],interpolate(pathb,2)[1],interpolate(pathb,4)[1]) # Liste des indices de manque de données dans Craw et paramètres de corrections
# Modèle de correction PITON DE LA FOURNAISE (G. BOUDOIRE)
print "PNRN temp", reg_m(Crawb, [tempb]).summary()
Ccorrb = [Crawb[i]-(Tab*tempb[i]+Tcb)+(Tab*np.mean(tempb)+Tcb) for i in range (0,len(Crawb))] # Correction par régression linéaire du CO2
Cregvent=[]
Vreg=[]
for i in range (0,len(Crawb)):
    if ventb[i]>0.1:
        Cregvent.append(Ccorrb[i])
        Vreg.append(ventb[i])
    else:
        None
print "PNRN wind", reg_m(Cregvent, [Vreg]).summary()
Ccorrbb = [] # Deuxième correction en vent pour PNRN
for i in range (0,len(Crawb)):
    if ventb[i]>0.1:
        Ccorrbb.append(Ccorrb[i]-(Vab*ventb[i]+Vcb)+(Vab*np.mean(ventb)+Vcb))
    else:
        Ccorrbb.append(Ccorrb[i])
Cfiltb = fftcp(Ccorrbb,dmin,dmax) # Filtrage des données
Cmov31b = sum([[np.nan]*(dayslon/2), movingaverage(Cfiltb,dayslon).tolist(), [np.nan]*(dayslon/2)], []) # Moving average
Cmov15b = sum([[np.nan]*(daysmed/2), movingaverage(Cfiltb,daysmed).tolist(), [np.nan]*(daysmed/2)], []) # Moving average
Cmov7b = sum([[np.nan]*(dayssho/2), movingaverage(Cfiltb,dayssho).tolist(), [np.nan]*(dayssho/2)], []) # Moving average
# Nettoyer la base des données interpolées
jour2b=copy.copy(jourb) # Crée une copie de jour sinon écrase les listes avec ligne suivante
Crawfb, Ccorrfbb, Cmov31bf, Cmov15bf, Cmov7bf, jourfb, pluvfb, ventfb = clean_dataset(missingindb,Crawb,Cfiltb,Cmov31b,Cmov15b,Cmov7b,jour2b,pluvb,ventb) # Supprimer les données interpolées de CO2 raw, CO2 final, Temp et Pluvio

### Concatener les deux fichiers ###
# Modèle de correction ETNA (S. GURRIERI)
fichier_intermediate("PNRN_Intermediate.csv",jourc,jourb,Crawc,Crawb)
pathint = "./PNRN_Intermediate.csv"
jouruni = jour2c+jour2b # Liste des dates complètes
Crawuni = interpolate(pathint,1)[0] # List des valeurs de CO2 interpolées
missinginduni = gap(interpolate(pathint,1)[1])
print "Main Spectral Components", Spectrum(Crawuni,"Days",400)
Cmovshouni1,Cmovshouni2 = filter_season_SG(Crawuni,shob,medb,lonb)
# Nettoyer la base des données interpolées
jour2uni=copy.copy(jouruni) # Crée une copie de jour sinon écrase les listes avec ligne suivante
Cmovshofuni1,Cmovshofuni2, jourfuni = clean_dataset(missinginduni,Cmovshouni1,Cmovshouni2,jour2uni)
fichier_sortie("PNRN_WebObs.csv", jourfuni, Crawfc+Crawfb, Crawfc+Ccorrfbb, Cmov7cf+Cmov7bf, Cmov15cf+Cmov15bf, Cmov31cf+Cmov31bf,Cmovshofuni1, Cmovshofuni2)
os.remove("./PNRN_Intermediate.csv")
data_accessor.create_table('pnrn_elaborated', attributes)
data_accessor.insert_data('pnrn_elaborated', attributes, (jourfuni,
                                                          Crawfc+Crawfb,
                                                          Crawfc+Ccorrfbb,
                                                          Cmov7cf+Cmov7bf,
                                                          Cmov15cf+Cmov15bf,
                                                          Cmov31cf+Cmov31bf,
                                                          Cmovshofuni1,
                                                          Cmovshofuni2))


############################################################
### MAIN FOR BLEN (TO MODIFY ACCORDING THE COLUMN PLACE) ###
############################################################

# Extraire les données en liste et regarder les données manquantes
jourd = dateliste(pathd) # Liste des dates complètes
Crawd = interpolate(pathd,1)[0] # List des valeurs de CO2 interpolées
tempd = interpolate(pathd,2)[0] # List des valeurs de température interpolées
ventd = interpolate(pathd,3)[0]
missingindd = gap(interpolate(pathd,1)[1],interpolate(pathd,2)[1],interpolate(pathd,3)[1]) # Liste des indices de manque de données dans Craw et paramètres de corrections
# Modèle de correction PITON DE LA FOURNAISE (G. BOUDOIRE)
print "BLEN wind", reg_m(Crawd, [ventd]).summary()
Ccorrd = [Crawd[i]-(Vad*ventd[i]+Vcd)+(Vad*np.mean(ventd)+Vcd) for i in range (0,len(Crawd))] # Correction par régression linéaire du CO2
print "BLEN temp", reg_m(Ccorrd, [tempd]).summary()
Ccorrdb = [Ccorrd[i]-(Tad*tempd[i]+Tcd)+(Tad*np.mean(tempd)+Tcd)for i in range (0,len(Crawd))]
Cfiltd = fftcp(Ccorrdb,dmin,dmax) # Filtrage des données
Cmov31d = sum([[np.nan]*(dayslon/2), movingaverage(Cfiltd,dayslon).tolist(), [np.nan]*(dayslon/2)], []) # Moving average
Cmov15d = sum([[np.nan]*(daysmed/2), movingaverage(Cfiltd,daysmed).tolist(), [np.nan]*(daysmed/2)], []) # Moving average
Cmov7d = sum([[np.nan]*(dayssho/2), movingaverage(Cfiltd,dayssho).tolist(), [np.nan]*(dayssho/2)], []) # Moving average
# Modèle de correction ETNA (S. GURRIERI)
print "Main Spectral Components",Spectrum(Crawd,"Days",400)
Cmovshod1,Cmovshod2 = filter_season_SG(Crawd,shod,medd,lond)
# Nettoyer la base des données interpolées et fichier de sortie
jour2d=copy.copy(jourd) # Crée une copie de jour sinon écrase les listes avec ligne suivante
Crawfd, Ccorrfdb, Cmov31df, Cmov15df, Cmov7df, Cmovshodf1,Cmovshodf2, jourfd, ventfd = clean_dataset(missingindd,Crawd,Cfiltd,Cmov31d,Cmov15d,Cmov7d,Cmovshod1,Cmovshod2,jour2d,ventd) # Supprimer les données interpolées de CO2 raw, CO2 final, Temp et Pluvio
fichier_sortie("BLEN_WebObs.csv", jourfd, Crawfd, Ccorrfdb, Cmov7df, Cmov15df, Cmov31df, Cmovshodf1, Cmovshodf2)
data_accessor.create_table('blen_elaborated', attributes)
data_accessor.insert_data('blen_elaborated', attributes, (jourfd, Crawfd,
                                                          Ccorrfdb, Cmov7df,
                                                          Cmov15df, Cmov31df,
                                                          Cmovshodf1,
                                                          Cmovshodf2))


####################################################################
### MAIN FOR ALL STATIONS (TO MODIFY ACCORDING THE COLUMN PLACE) ###
####################################################################

# Deux stations (PCRN,PNRN)
CRAW_2 = two_stations(Crawf,Crawfc+Crawfb,jourf,jourfuni)
CCORR_2 = two_stations(Ccorrf,Crawfc+Ccorrfbb,jourf,jourfuni)
CMOV7_2 = two_stations(Cmov7f,Cmov7cf+Cmov7bf,jourf,jourfuni)
CMOV15_2 = two_stations(Cmov15f,Cmov15cf+Cmov15bf,jourf,jourfuni)
CMOV31_2 = two_stations(Cmov31f,Cmov31cf+Cmov31bf,jourf,jourfuni)
CSG1_2 = two_stations(Cmovsho1f,Cmovshofuni1,jourf,jourfuni)
CSG2_2 = two_stations(Cmovsho2f,Cmovshofuni2,jourf,jourfuni)
fichier_sortie("TWO_WebObs.csv", CRAW_2[1], CRAW_2[0], CCORR_2[0], CMOV7_2[0], CMOV15_2[0], CMOV31_2[0], CSG1_2[0],CSG2_2[0])

# Trois stations (PCRN,PNRN,BLEN) 
CRAW_3 = three_stations(Crawf,Crawfc+Crawfb,Crawfd,jourf,jourfuni,jourfd)
CCORR_3 = three_stations(Ccorrf,Crawfc+Ccorrfbb,Ccorrfdb,jourf,jourfuni,jourfd)
CMOV7_3 = three_stations(Cmov7f,Cmov7cf+Cmov7bf,Cmov7df,jourf,jourfuni,jourfd)
CMOV15_3 = three_stations(Cmov15f,Cmov15cf+Cmov15bf,Cmov15df,jourf,jourfuni,jourfd)
CMOV31_3 = three_stations(Cmov31f,Cmov31cf+Cmov31bf,Cmov31df,jourf,jourfuni,jourfd)
CSG1_3 = three_stations(Cmovsho1f,Cmovshofuni1,Cmovshodf1,jourf,jourfuni,jourfd)
CSG2_3 = three_stations(Cmovsho2f,Cmovshofuni2,Cmovshodf2,jourf,jourfuni,jourfd)
fichier_sortie("THREE_WebObs.csv", CRAW_3[1], CRAW_3[0], CCORR_3[0], CMOV7_3[0], CMOV15_3[0], CMOV31_3[0], CSG1_3[0],CSG2_3[0])
data_accessor.create_table('all_distal_elaborated', attributes)
data_accessor.insert_data('all_distal_elaborated', attributes, (CRAW_3[1],
                                                                CRAW_3[0],
                                                                CCORR_3[0],
                                                                CMOV7_3[0],
                                                                CMOV15_3[0],
                                                                CMOV31_3[0],
                                                                CSG1_3[0],
                                                                CSG2_3[0]))

data_accessor.close()
