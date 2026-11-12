"""Interface métier locale. Lancer avec streamlit run app.py."""
import hashlib,json
from dataclasses import replace
from pathlib import Path
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from reserving.data import DATASETS,load_dataset
from reserving.triangle import read_csv,to_incremental,observed_mask
from reserving.mack import mack
from reserving.bootstrap import odp_bootstrap
from reserving.backtest import diagonal_backtest,backtest_summary
from reserving.export import triangle_fingerprint,report_json

ROOT=Path(__file__).parent
st.set_page_config(page_title='Clair · Provisionnement',page_icon='◈',layout='wide')
st.markdown('''<style>
[data-testid="stAppViewContainer"]{background:#f6f7f2;color:#243c35}
[data-testid="stSidebar"]{background:#edf1e7}
h1,h2,h3{color:#174f43!important;letter-spacing:-.035em}
[data-testid="stMetric"]{background:white;border:1px solid #e2e7dd;border-radius:12px;padding:17px}
.stButton>button[kind="primary"]{background:#174f43;border-color:#174f43}
[data-testid="stTabs"] button{font-size:14px}.eyebrow{font-size:11px;letter-spacing:3px;color:#7d906c;font-weight:700}
.small-note{font-size:12px;color:#75827c;line-height:1.7}
</style>''',unsafe_allow_html=True)
fmt=lambda v:f'{v:,.2f}'.replace(',',' ').replace('.',',')
st.sidebar.markdown('## clair · réserves')
st.sidebar.caption('DU TRIANGLE À LA DÉCISION')
source=st.sidebar.selectbox('Données à analyser',list(DATASETS)+['upload'],format_func=lambda k:DATASETS.get(k,'Importer mon triangle CSV'),key='dataset')
try:
 if source=='upload':
  st.sidebar.caption('CSV : origin,D1,D2,… ; NA futurs vides ; décimales avec point.')
  upload=st.sidebar.file_uploader('Triangle annuel carré',type=['csv'],key='upload')
  representation=st.sidebar.selectbox('Format des montants',['cumulative','incremental'],format_func=lambda x:'Cumulés' if x=='cumulative' else 'Incrémentaux')
  if upload is None:
   st.title('Votre triangle, une estimation expliquée.');st.info('Importez un CSV pour commencer. Le fichier reste dans la mémoire de cette session.')
   st.caption('Exemple fictif de structure CSV ; ces chiffres ne proviennent pas d’un portefeuille réel.')
   st.code('origin,D1,D2,D3,D4\n2020,100,180,240,270\n2021,120,210,280,\n2022,140,250,,\n2023,160,,,',language='csv')
   st.stop()
  triangle=read_csv(upload.getvalue(),representation=representation)
 else:triangle=load_dataset(source)
except (ValueError,FileNotFoundError,UnicodeError,pd.errors.ParserError) as error:
 st.error(str(error));st.stop()
nature_options=['unspecified','paid','incurred'];nature_names={'unspecified':'Nature à confirmer','paid':'Paiements','incurred':'Charges encourues'}
nature=st.sidebar.selectbox('Nature des montants',nature_options,index=nature_options.index(triangle.nature),format_func=nature_names.get,key='nature_'+source)
unit=st.sidebar.text_input('Unité des montants',value=triangle.unit,key='unit_'+source)
valuation=st.sidebar.text_input('Date d’évaluation / libellé',value=triangle.valuation,key='valuation_'+source)
triangle=replace(triangle,nature=nature,unit=unit or 'unités non précisées',valuation=valuation)
st.sidebar.divider();st.sidebar.markdown('**Hypothèses fixes de la V1**')
st.sidebar.caption('Facteurs pondérés par volume · toutes les années · variance finale selon Mack · facteur de queue = 1 · aucune inflation ni actualisation.')
st.sidebar.caption('Moteur Python indépendant de l’interface. Aucune donnée importée n’est écrite automatiquement sur disque.')
st.sidebar.link_button('Code, méthodes et guide','https://github.com/kelian19/assurance-provisionnement')

try:result=mack(triangle.cumulative)
except ValueError as error:st.error(str(error));st.stop()
fingerprint=triangle_fingerprint(triangle)
boot_state=st.session_state.get('bootstrap_result')
bootstrap=boot_state['result'] if boot_state and boot_state['fingerprint']==fingerprint else None
st.markdown('<div class="eyebrow">ATELIER DE PROVISIONNEMENT</div>',unsafe_allow_html=True)
st.title('Combien reste-t-il à développer ?')
st.caption(f'{triangle.name} · {triangle.n} années · {triangle.unit} · évaluation : {triangle.valuation}')
if nature=='paid':interpretation='Provision estimée restant à payer, dans le périmètre du triangle.'
elif nature=='incurred':interpretation='Développement futur estimé de charge. Ce montant n’est pas la totalité du reste à payer.'
else:interpretation='Développement futur estimé. Confirmez la nature des montants pour interpréter ce résultat comme une provision restant à payer.'
st.info(interpretation)
cols=st.columns(4)
cols[0].metric('Développement futur estimé',fmt(result.total_reserve))
cols[1].metric('Montant ultime estimé',fmt(result.ultimate.sum()))
cols[2].metric('Erreur de prédiction Mack',fmt(result.total_rmsep))
cols[3].metric('Erreur / estimation',f'{100*result.total_rmsep/abs(result.total_reserve):.1f} %' if result.total_reserve else 'Non défini')
st.caption('Montants dans l’unité indiquée ; aucune conversion automatique en euros. L’erreur Mack est une RMSEP, pas une marge à ajouter ni un intervalle de confiance.')
if result.diagnostics['negative_observed_increments']:
 st.warning(f"{result.diagnostics['negative_observed_increments']} incrément(s) négatif(s) : les reprises restent dans Mack. Le bootstrap ODP de cette V1 sera indisponible.")

t_data,t_est,t_unc,t_val,t_math=st.tabs(['Données & triangle','Estimation','Incertitude','Validation','Méthode & maths'])
with t_data:
 st.subheader('Des observations aux projections')
 mode=st.radio('Triangle à afficher',['Observé','Projeté','Incréments observés'],horizontal=True,key='triangle_view')
 matrix=triangle.cumulative if mode=='Observé' else result.projected if mode=='Projeté' else to_incremental(triangle.cumulative)
 fig=go.Figure(go.Heatmap(z=matrix,x=[f'D{j+1}' for j in range(triangle.n)],y=triangle.origins,colorscale=[[0,'#f0f4e7'],[1,'#174f43']],hovertemplate='Origine %{y}<br>Développement %{x}<br>Montant %{z:,.2f}<extra></extra>',colorbar={'title':'Montant'}))
 fig.update_layout(height=440,margin=dict(l=0,r=0,t=10,b=0),yaxis={'autorange':'reversed'},paper_bgcolor='rgba(0,0,0,0)')
 st.plotly_chart(fig,width='stretch');st.dataframe(pd.DataFrame(matrix,index=triangle.origins,columns=[f'D{j+1}' for j in range(triangle.n)]),width='stretch')
 st.caption('La partie inférieure droite vide correspond au futur. Les observations ne sont jamais écrasées par les projections.')
 with st.expander('Source et traçabilité'):
  st.write(triangle.source);st.code(fingerprint,language=None)
  st.caption('L’empreinte intègre les montants, les origines, la nature, l’unité et le libellé d’évaluation. Les dates techniques utilisées pour comparer la bibliothèque ne remplacent pas les dates de la source.')
 frame=triangle.frame().reset_index(names='origin')
 st.download_button('Télécharger le triangle au format CSV',frame.to_csv(index=False),file_name='triangle_cumule.csv',mime='text/csv')
with t_est:
 st.subheader('Une lecture par année de survenance')
 summary=result.summary(triangle)
 fig=px.bar(summary,x='origin',y='reserve',error_y='mack_rmsep',labels={'origin':'Année de survenance','reserve':'Développement futur estimé'},color_discrete_sequence=['#42745d'])
 fig.update_layout(paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)',showlegend=False)
 st.plotly_chart(fig,width='stretch');st.caption('Les barres d’erreur représentent une RMSEP par année. Elles ne sont pas des intervalles de confiance.')
 st.dataframe(summary,width='stretch',hide_index=True)
 st.subheader('Cadence de développement')
 st.dataframe(pd.DataFrame({'transition':[f'D{j+1} → D{j+2}' for j in range(triangle.n-1)],'facteur':result.factors,'sigma2_Mack':result.sigma2,'observations':result.diagnostics['sample_size_by_factor']}),hide_index=True,width='stretch')
 p1,p2=st.columns(2);p1.metric('Risque de processus · écart-type',fmt(np.sqrt(result.process_msep.sum())));p2.metric('Risque d’estimation · écart-type',fmt(np.sqrt(result.parameter_covariance.sum())))
 st.caption('Les variances de processus et d’estimation s’additionnent. Le total tient compte de la covariance entre années ; les écarts-types ne s’additionnent pas.')
 st.download_button('Exporter les résultats par année',summary.to_csv(index=False),file_name='provisions_par_annee.csv',mime='text/csv')
with t_unc:
 st.subheader('Explorer une distribution de scénarios')
 st.write('Bootstrap ODP de bibliothèque, avec rééchantillonnage des résidus de Pearson et risque de processus Gamma signé. Ce modèle est distinct du modèle de Mack.')
 with st.form('bootstrap_controls'):
  c1,c2=st.columns(2);simulations=c1.selectbox('Nombre de simulations',[500,1000,5000,10000],index=2,key='simulations');seed=c2.number_input('Graine de simulation',min_value=1,max_value=2**32-2,value=42,step=1,key='seed')
  run=st.form_submit_button('Simuler l’incertitude',type='primary',key='run_bootstrap')
 if run:
  try:
   with st.spinner('Rééchantillonnage et simulation du développement futur…'):bootstrap=odp_bootstrap(triangle.cumulative,simulations=int(simulations),seed=int(seed))
   st.session_state['bootstrap_result']={'fingerprint':fingerprint,'result':bootstrap}
  except (ValueError,ArithmeticError,np.linalg.LinAlgError) as error:st.error(str(error));bootstrap=None
 if bootstrap is None:st.info('Lancez une simulation pour afficher les quantiles. Aucun résultat aléatoire n’est prérempli.')
 else:
  b=bootstrap.summary();bc=st.columns(4)
  for col,label,key in zip(bc,['Moyenne des scénarios','Médiane','Quantile 95 %','Quantile 99 %'],['mean','median','q95','q99']):col.metric(label,fmt(b[key]))
  fig=go.Figure(go.Histogram(x=bootstrap.predictive_reserves,nbinsx=60,marker_color='#66875c',opacity=.85))
  fig.add_vline(x=result.total_reserve,line_dash='dash',line_color='#174f43',annotation_text='Chain-Ladder')
  fig.add_vline(x=b['q95'],line_dash='dot',line_color='#b38b4f',annotation_text='Q95 bootstrap')
  fig.update_layout(xaxis_title='Développement futur simulé',yaxis_title='Nombre de scénarios',paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)')
  st.plotly_chart(fig,width='stretch')
  st.caption(f"Écart-type : {fmt(b['std'])} · erreur Monte-Carlo de la moyenne : {fmt(b['mean_monte_carlo_se'])} · graine : {bootstrap.diagnostics['seed']} · simulations : {bootstrap.diagnostics['simulations']}.")
  if bootstrap.diagnostics['negative_future_mean_cells']:
   st.warning(f"La réestimation produit des incréments futurs moyens négatifs dans {bootstrap.diagnostics['negative_mean_simulations']} scénario(s). La bibliothèque utilise une Gamma signée ; ces scénarios sont conservés et rendent explicite cette extension du modèle ODP positif.")
  st.caption('Les quantiles portent sur le développement jusqu’au terme retenu. Ils ne constituent pas un SCR à un an, ni une provision réglementaire approuvée.')
  with st.expander('Diagnostics et stabilité Monte-Carlo'):
   st.json(bootstrap.diagnostics);st.write('Les quatre quantiles Q95 par lots sont un diagnostic de stabilité, pas un intervalle de confiance.')
  st.download_button('Exporter les scénarios',pd.DataFrame({'scenario':np.arange(1,len(bootstrap.predictive_reserves)+1),'reserve':bootstrap.predictive_reserves}).to_csv(index=False),file_name='scenarios_bootstrap.csv',mime='text/csv')
with t_val:
 st.subheader('Validation sur diagonales masquées')
 backtest=diagonal_backtest(triangle.cumulative);bt=backtest_summary(backtest)
 if bt.empty:st.info('Au moins cinq années sont nécessaires pour cette validation rétrospective.')
 else:
  st.dataframe(bt,hide_index=True,width='stretch')
  st.caption('Chaque ligne est un arrêt de données antérieur : une diagonale suivante connue est prédite avec les seules données disponibles à cet arrêt. Les nouvelles origines et la plus ancienne au-delà de la maturité ajustée sont exclues. Le ratio porte sur les incréments, pas sur les cumuls.')
  with st.expander('Voir les cellules prédites'):st.dataframe(backtest,hide_index=True,width='stretch')
  st.download_button('Exporter la validation',backtest.to_csv(index=False),file_name='validation_diagonales.csv',mime='text/csv')
 report_path=ROOT/'reports/validation.json'
 if report_path.exists():
  v=json.loads(report_path.read_text(encoding='utf-8'));st.subheader('Réconciliation des références livrées')
  st.dataframe(pd.DataFrame(v['deterministic_comparisons']),hide_index=True,width='stretch')
  st.caption('La comparaison utilise exactement les mêmes données et l’approximation finale de variance « Mack ». Le triangle du cours diffère de GenIns en une cellule : 2 864 494 contre 2 864 498. Les deux jeux sont conservés séparément.')
 st.warning('La reproduction des références vérifie les calculs. Elle ne valide pas les hypothèses sur votre portefeuille : indépendance des années, stabilité des cadences, changements de gestion, inflation et facteur de queue restent à examiner.')
with t_math:
 st.subheader('Les hypothèses et les calculs')
 st.latex(r'\mathbb{E}[C_{i,j+1}\mid\mathcal{F}_{i,j}]=f_j C_{i,j},\qquad \mathrm{Var}(C_{i,j+1}\mid\mathcal{F}_{i,j})=\sigma_j^2 C_{i,j}')
 st.write('Mack suppose des années de survenance indépendantes, des facteurs de développement communs et une variance proportionnelle au cumul. Il ne spécifie pas une loi complète des provisions.')
 st.latex(r'\widehat f_j=\frac{\sum_i C_{i,j+1}}{\sum_i C_{i,j}},\qquad \widehat C_{i,n}=C_{i,k_i}\prod_{j=k_i}^{n-1}\widehat f_j')
 st.latex(r'\widehat R_i=\widehat C_{i,n}-C_{i,k_i},\qquad \widehat R=\sum_i\widehat R_i')
 st.latex(r'\widehat\sigma_j^2=\frac{1}{m_j-1}\sum_{i=1}^{m_j}\frac{(C_{i,j+1}-\widehat f_j C_{i,j})^2}{C_{i,j}}')
 st.write('La dernière transition n’a qu’une observation : sa variance est approchée par le minimum de Mack, documenté dans le code. Facteur de queue fixé à 1 : aucune charge supplémentaire au-delà du dernier âge modélisé.')
 st.latex(r'\widehat{\mathrm{MSEP}}(\widehat R_i)=\widehat C_{i,n}^{\,2}\sum_{j=k_i}^{n-1}\frac{\widehat\sigma_j^2}{\widehat f_j^2}\left(\frac{1}{\widehat C_{i,j}}+\frac{1}{\sum_l C_{l,j}}\right)')
 st.latex(r'\mathrm{MSEP}_{total}=\sum_i\mathrm{MSEP}_i+2\sum_{i<k}\widehat{\mathrm{Cov}}(R_i,R_k)')
 st.write('Bootstrap ODP : les montants incrémentaux sont représentés par une moyenne ligne × colonne, avec variance proportionnelle à cette moyenne. Les résidus ajustés sont rééchantillonnés ; les paramètres sont réestimés et le risque de processus est ajouté. La bibliothèque conserve les scénarios signés plutôt que de les tronquer silencieusement.')
 st.markdown('Schnieper et inflation restent des extensions. [Méthodologie complète et sources](https://github.com/kelian19/assurance-provisionnement/blob/main/docs/METHODOLOGIE.md).')

st.divider()
# Refresh bootstrap from session after a submitted form, keeping exports tied to the current triangle.
boot_state=st.session_state.get('bootstrap_result');bootstrap=boot_state['result'] if boot_state and boot_state['fingerprint']==fingerprint else None
st.download_button('Télécharger le dossier de calcul JSON',report_json(triangle,result,bootstrap),file_name='dossier_provisionnement.json',mime='application/json',key='report_download')
st.caption('Clair · Réserves — démonstrateur actuariel vérifié sur références. Aucun déploiement public, aucune donnée client publiée. Les fichiers téléchargés sont créés uniquement à votre demande.')
