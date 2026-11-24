"""Interface métier locale. Lancer avec streamlit run app.py."""
import hashlib,json
from dataclasses import replace
from pathlib import Path
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from reserving.data import DATASETS,load_dataset,load_schnieper
from reserving.triangle import read_csv,to_incremental,observed_mask
from reserving.mack import mack
from reserving.bootstrap import odp_bootstrap
from reserving.schnieper import schnieper,schnieper_bootstrap
from reserving.merz_wuthrich import merz_wuthrich
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

t_data,t_est,t_unc,t_mw,t_sch,t_val,t_math=st.tabs(['Données & triangle','Estimation','Incertitude','Vue à un an','Schnieper','Validation','Méthode & maths'])
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
with t_mw:
 st.subheader('Ce qui se révélera en un an')
 st.write('Mack mesure l’incertitude sur la charge **ultime**, tout le run-off. Solvabilité II raisonne à **un an** : de combien l’estimation de l’ultime peut-elle bouger quand la prochaine diagonale sera observée ? C’est le **résultat de développement (CDR)** de Merz et Wüthrich (2008), d’espérance nulle, dont on estime l’erreur quadratique.')
 try:mw=merz_wuthrich(triangle.cumulative)
 except ValueError as error:st.error(str(error));mw=None
 if mw is not None:
  m1,m2,m3=st.columns(3)
  m1.metric('Erreur Mack (ultime)',fmt(mw.total_rmsep_mack));m2.metric('Erreur du CDR à un an',fmt(mw.total_rmsep_cdr));m3.metric('Part révélée en un an',f'{100*mw.one_year_share:.0f} %')
  frame=mw.summary(triangle)
  fig=go.Figure([go.Bar(name='Mack (ultime)',x=frame.origin,y=frame.mack_rmsep,marker_color='#b9c9a8'),go.Bar(name='CDR à un an',x=frame.origin,y=frame.cdr_rmsep,marker_color='#174f43')])
  fig.update_layout(barmode='group',xaxis_title='Année de survenance',yaxis_title='Racine de la msep',paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)',legend=dict(orientation='h'))
  st.plotly_chart(fig,width='stretch')
  st.dataframe(frame.assign(part_un_an=frame.cdr_rmsep/frame.mack_rmsep.where(frame.mack_rmsep>0)),width='stretch',hide_index=True)
  st.caption('Contrôles : sur le triangle de l’article (MW2008) le moteur redonne les valeurs publiées (81 080 et 108 401) ; pour l’origine à qui il ne reste qu’une période, l’erreur à un an égale celle de Mack. Ce n’est pas un SCR : il manque la marge de risque et une mesure de risque à 99,5 %, qui demande une hypothèse de loi.')
  st.download_button('Exporter la vue à un an',frame.to_csv(index=False),file_name='cdr_un_an.csv',mime='text/csv')
with t_sch:
 st.subheader('Séparer les vrais IBNR des révisions de sinistres connus')
 st.write('Le modèle de Schnieper décompose le développement en deux flux : les **nouveaux sinistres** N, proportionnels à une exposition (vrais IBNR), et les **révisions** D des sinistres déjà connus, proportionnelles à la charge actuelle (IBNER). Il exige donc trois entrées — N, D et l’exposition E — qu’un triangle cumulé seul ne permet pas de reconstituer. Cet onglet utilise l’exemple 5.4 du cours (indépendant du triangle choisi à gauche).')
 try:sch_data=load_schnieper();sch=schnieper(sch_data);mack_same=mack(sch_data.cumulative)
 except (ValueError,FileNotFoundError) as error:
  st.info(f'Données Schnieper indisponibles : {error}');sch=None
 if sch is not None:
  sm=st.columns(4)
  sm[0].metric('Provision Schnieper',fmt(sch.total_reserve));sm[1].metric('Mack, même triangle cumulé',fmt(mack_same.total_reserve))
  sm[2].metric('dont vrais IBNR (nouveaux sinistres)',fmt(sch.ibnr.sum()));sm[3].metric('dont IBNER (révisions)',fmt(sch.ibner.sum()))
  st.caption('Un IBNER négatif signifie que les révisions observées sont en moyenne des baisses de charge. Schnieper et Mack reposent sur des hypothèses différentes (exposition connue contre proportionnalité pure) : l’écart entre les deux est une mesure du risque de modèle, pas une erreur de calcul.')
  sch_summary=sch.summary(sch_data)
  fig=go.Figure([go.Bar(x=sch_summary.origin,y=sch_summary.true_ibnr,name='Vrais IBNR',marker_color='#42745d'),go.Bar(x=sch_summary.origin,y=sch_summary.ibner,name='IBNER (révisions)',marker_color='#b38b4f')])
  fig.update_layout(barmode='relative',paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)',xaxis_title='Année de survenance',yaxis_title='Développement futur estimé',legend={'orientation':'h'})
  st.plotly_chart(fig,width='stretch');st.dataframe(sch_summary,width='stretch',hide_index=True)
  st.subheader('Paramètres estimés')
  st.dataframe(sch.parameters(),width='stretch',hide_index=True)
  st.caption('λ_j : nouveaux sinistres par unité d’exposition ; δ_j : taux de révision de la charge connue (négatif = hausse) ; σ²_j, τ²_j : variances associées. Par convention du cours, σ²_n = τ²_{n−1} = 0 faute d’observations : les années dont le seul développement restant est la dernière colonne ont donc une variance de processus nulle, ce qui sous-estime leur risque.')
  sp=st.columns(2);sp[0].metric('Écart-type de processus (paramètres supposés connus)',fmt(sch.total_process_std));sp[1].metric('Écart-type / estimation',f'{100*sch.total_process_std/sch.total_reserve:.1f} %')
  st.caption('Variance analytique du lemme 5.13 du cours : risque de processus seul. L’erreur d’estimation des paramètres n’est pas incluse ; elle l’est dans le bootstrap ci-dessous.')
  with st.expander('Triangles N, D et cumul C, exposition E'):
   cols_names=[f'D{j+1}' for j in range(sch_data.n)]
   for label,matrix in (('Nouveaux sinistres N',sch_data.new_claims),('Révisions D',sch_data.revisions),('Cumul C = ΣN − ΣD',sch.cumulative)):
    st.markdown(f'**{label}**');st.dataframe(pd.DataFrame(matrix,index=sch_data.origins,columns=cols_names),width='stretch')
   st.markdown('**Exposition E**');st.dataframe(pd.DataFrame({'exposition':sch_data.exposure},index=sch_data.origins),width='stretch')
   st.caption(f'Source : {sch_data.source}. Données du cours, unités non précisées.')
  st.subheader('Distribution par bootstrap de résidus')
  st.write('Bootstrap non paramétrique du cours (§6.4.1) : résidus de Pearson ajustés et centrés des deux flux, reconstruction du passé pour réestimer les paramètres, puis projection stochastique du futur avec plancher à zéro. Contrairement à l’ODP de l’onglet Incertitude, il s’agit bien du bootstrap du modèle de Schnieper.')
  with st.form('schnieper_bootstrap_controls'):
   c1,c2=st.columns(2);sch_sims=c1.selectbox('Nombre de simulations',[1000,5000,10000,20000],index=1,key='schnieper_simulations');sch_seed=c2.number_input('Graine de simulation',min_value=1,max_value=2**32-2,value=42,step=1,key='schnieper_seed')
   sch_run=st.form_submit_button('Simuler (Schnieper)',type='primary',key='run_schnieper_bootstrap')
  if sch_run:
   try:
    with st.spinner('Reconstruction du passé et projection du futur…'):st.session_state['schnieper_bootstrap_result']=schnieper_bootstrap(sch_data,simulations=int(sch_sims),seed=int(sch_seed))
   except (ValueError,ArithmeticError) as error:st.error(str(error));st.session_state.pop('schnieper_bootstrap_result',None)
  sb=st.session_state.get('schnieper_bootstrap_result')
  if sb is None:st.info('Lancez une simulation pour afficher la distribution. Aucun résultat aléatoire n’est prérempli.')
  else:
   q=sb.summary();qc=st.columns(4)
   for col,label,key in zip(qc,['Moyenne (Schnieper)','Médiane (Schnieper)','Q95 (Schnieper)','Q99 (Schnieper)'],['mean','median','q95','q99']):col.metric(label,fmt(q[key]))
   fig=go.Figure(go.Histogram(x=sb.predictive_reserves,nbinsx=60,marker_color='#66875c',opacity=.85))
   fig.add_vline(x=sch.total_reserve,line_dash='dash',line_color='#174f43',annotation_text='Estimation Schnieper')
   fig.update_layout(xaxis_title='Développement futur simulé',yaxis_title='Nombre de scénarios',paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)')
   st.plotly_chart(fig,width='stretch')
   d=sb.diagnostics
   st.caption(f"Écart-type : {fmt(q['std'])} (paramètres seuls : {fmt(q['parameter_only_std'])}) · erreur Monte-Carlo de la moyenne : {fmt(q['mean_monte_carlo_se'])} · graine {d['seed']} · {d['simulations']} simulations.")
   st.caption(f"{100*d['floored_rate']:.2f} % des simulations contiennent au moins un cumul négatif ramené à zéro (plancher du cours) ; ces scénarios sont conservés et biaisent légèrement la moyenne à la hausse. Quantiles non interprétables comme un SCR à un an.")
   with st.expander('Diagnostics'):st.json(d)
   st.download_button('Exporter les scénarios Schnieper',pd.DataFrame({'scenario':np.arange(1,len(sb.predictive_reserves)+1),'reserve':sb.predictive_reserves}).to_csv(index=False),file_name='scenarios_schnieper.csv',mime='text/csv')
  st.download_button('Exporter les résultats Schnieper par année',sch_summary.to_csv(index=False),file_name='schnieper_par_annee.csv',mime='text/csv')
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
 st.markdown('**Schnieper** (onglet dédié) :')
 st.latex(r'C_{i,j+1}=C_{i,j}+N_{i,j+1}-D_{i,j+1},\quad \mathbb{E}[N_{i,j}\mid\mathcal{F}]=\lambda_jE_i,\quad \mathbb{E}[D_{i,j+1}\mid\mathcal{F}]=\delta_jC_{i,j}')
 st.latex(r'\widehat\lambda_j=\frac{\sum_i N_{i,j}}{\sum_i E_i},\quad \widehat\delta_j=\frac{\sum_i D_{i,j+1}}{\sum_i C_{i,j}},\quad \widehat C_{i,j}=\widehat\lambda_jE_i+(1-\widehat\delta_{j-1})\widehat C_{i,j-1}')
 st.write('Les vrais IBNR sont la somme des λ̂_j·E_i futurs ; l’IBNER est la somme des −δ̂_{j−1}·Ĉ_{i,j−1} futurs. L’inflation reste une extension. [Méthodologie complète et sources](https://github.com/kelian19/assurance-provisionnement/blob/main/docs/METHODOLOGIE.md).')

st.divider()
# Refresh bootstrap from session after a submitted form, keeping exports tied to the current triangle.
boot_state=st.session_state.get('bootstrap_result');bootstrap=boot_state['result'] if boot_state and boot_state['fingerprint']==fingerprint else None
st.download_button('Télécharger le dossier de calcul JSON',report_json(triangle,result,bootstrap),file_name='dossier_provisionnement.json',mime='application/json',key='report_download')
st.caption('Clair · Réserves — démonstrateur actuariel vérifié sur références. Aucun déploiement public, aucune donnée client publiée. Les fichiers téléchargés sont créés uniquement à votre demande.')
