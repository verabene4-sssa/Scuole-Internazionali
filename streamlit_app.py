import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
import io
import streamlit.components.v1 as components

# Configurazione della pagina
st.set_page_config(page_title="Business Plan Scuola Internazionale", layout="wide")
st.title("Business Plan Scuola Internazionale")

# --- Variabili di base ---
years = [1, 2, 3, 4, 5]
classes = ["Prima", "Seconda", "Terza", "Quarta", "Quinta"]
default_new_first = [10, 12, 14, 16, 18]

# ================= SIDEBAR ================= #
st.sidebar.header("🎓 Nuove classi prime")
new_first_students = []
for i, anno in enumerate(years):
    val = st.sidebar.number_input(f"Anno {anno} - nuova prima", min_value=0, value=default_new_first[i], step=1)
    new_first_students.append(val)

st.sidebar.markdown("---")
st.sidebar.header("💰 Retta annuale")
retta_unica = st.sidebar.number_input(
    "Retta annuale per studente (€)", 
    min_value=0, value=10000, step=100,
    help="La stessa retta sarà applicata a tutte le classi e a tutti gli anni."
)

st.sidebar.header("💰 Contributi")
altri_contributi = st.sidebar.number_input(
    "Contributi annuali (€)",
    min_value=0, value=0, step=100,
    help="Contributi aggiuntivi annuali."
)

# ================= CALCOLO STUDENTI PER CLASSE ================= #
df_students = pd.DataFrame({"Anno": years})
for c in classes:
    df_students[c] = 0

for i, anno in enumerate(years):
    df_students.at[i, "Prima"] = new_first_students[i]
    if i >= 1:
        df_students.at[i, "Seconda"] = df_students.at[i-1, "Prima"]
    if i >= 2:
        df_students.at[i, "Terza"] = df_students.at[i-1, "Seconda"]
    if i >= 3:
        df_students.at[i, "Quarta"] = df_students.at[i-1, "Terza"]
    if i >= 4:
        df_students.at[i, "Quinta"] = df_students.at[i-1, "Quarta"]

df_students["Studenti totali"] = df_students[classes].sum(axis=1)
 



# ============================= TABS ============================= #
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
    "Ricavi preventivi",
    "Costi preventivi del personale", 
    "Costi preventivi di struttura", 
    "Conto economico",
    "Stato patrimoniale",
    "Rendiconto finanziario",
    "Indici di valutazione",
    "Previsione del fabbisogno finanziario iniziale"
])


# ================= CALCOLO RICAVI (Per Tab 1) ================= #

results_ricavi = []

for i, anno in enumerate(years):
    ricavi_anno = {}
    totale_anno = 0
    
    # Ricavo SOLO dalla retta
    for c in classes:
        studenti = df_students.at[i, c]
        ricavo_classe = studenti * retta_unica
        ricavi_anno[c] = ricavo_classe
        totale_anno += ricavo_classe
    
    # ➕ aggiunta dei contributi unici annuali
    totale_anno += altri_contributi
    
    results_ricavi.append({
        "Anno": anno,
        **ricavi_anno,
        "Contributi (€)": altri_contributi,
        "Totale ricavi (€)": totale_anno
    })

df_ricavi = pd.DataFrame(results_ricavi)


# ================= CALCOLO COSTI STRUTTURA (Per Tab 3) ================= #
# Variabili iniziali per struttura (definizione preliminare)
default_areas = [200, 200, 500, 500, 500]
superfici = default_areas

# Definizione dei parametri per permetterne l'uso nei calcoli globali se necessario
cost_manufab = 2.60
cost_manimpi = 11.96
cost_energia = 11.52
cost_gas = 7.05
cost_acqua = 3.78
cost_pulizie = 38.43
ammort_arredi = 10.0
base_amm_att = 8.5
incremento_amm_att = 8.5
reception_first_two = 230.58
reception_other = 184.46

# --- Calcolo costi struttura ---
results_costs = []
for i, anno in enumerate(years):
    # Usa il default inizialmente, sarà sovrascritto nella tab se l'utente interagisce
    superficie = float(superfici[i])
    amm_att_anno = base_amm_att + i * incremento_amm_att
    reception_m2 = reception_first_two if anno <= 2 else reception_other

    t_manufab = superficie * cost_manufab
    t_manimpi = superficie * cost_manimpi
    t_energia = superficie * cost_energia
    t_gas = superficie * cost_gas
    t_acqua = superficie * cost_acqua
    t_pulizie = superficie * cost_pulizie
    t_amm_arredi = superficie * ammort_arredi
    t_amm_att = superficie * amm_att_anno
    t_reception = superficie * reception_m2
    
    totale_struttura = sum([ 
        t_manufab, t_manimpi, t_energia, t_gas, t_acqua, t_pulizie, 
        t_amm_arredi, t_amm_att, t_reception 
    ])
    
    results_costs.append({
        "Anno": anno,
        "Studenti totali": int(df_students.at[i, "Studenti totali"]),
        "Superficie (m²)": superficie,
        "Manutenzione fabbricati (€/anno)": t_manufab,
        "Manutenzione impianti (€/anno)": t_manimpi,
        "Energia elettrica (€/anno)": t_energia,
        "Fornitura gas (€/anno)": t_gas,
        "Acqua (€/anno)": t_acqua,
        "Pulizie (€/anno)": t_pulizie,
        "Ammortamenti arredi (€/anno)": t_amm_arredi,
        "Ammort. attrezzature (€/anno)": t_amm_att,
        "Reception / servizi (€/anno)": t_reception,
        "Totale Costi Struttura (€/anno)": totale_struttura
    })
df_costs = pd.DataFrame(results_costs)


# ================= CALCOLO COSTI PERSONALE (Per Tab 2) ================= #
# Variabili iniziali per personale (definizione preliminare)
costo_docente_assunto = 40000
costo_docente_contratto = 15000
personale_direttivo = 60000

docenti_assunti = []
docenti_contratto = []

for i, anno in enumerate(years):
    studenti = int(df_students.at[i, "Studenti totali"])

    # 1) DOCENTI ASSUNTI (1 ogni 8 studenti)
    n_assunti = studenti // 8

    # Minimi strutturali anni iniziali (se vuoi mantenerli)
    if anno == 1:
        n_assunti = max(n_assunti, 2)
        min_contratto = 1
    elif anno == 2:
        n_assunti = max(n_assunti, 3)
        min_contratto = 2
    else:
        min_contratto = 1  # minimo base per anni successivi

    # Studenti ancora scoperti
    resto_studenti = studenti - n_assunti * 8

    # 2) DOCENTI A CONTRATTO
    if resto_studenti > 0:
        n_contratto = max(min_contratto, 1)
    else:
        n_contratto = min_contratto

    docenti_assunti.append(n_assunti)
    docenti_contratto.append(n_contratto)


# --- Calcolo costi personale ---
results_personale = []
for i, anno in enumerate(years):
    costo_assunti = docenti_assunti[i] * costo_docente_assunto
    costo_contr = docenti_contratto[i] * costo_docente_contratto
    totale_personale = costo_assunti + costo_contr + personale_direttivo
    
    results_personale.append({
        "Anno": anno,
        "Studenti totali": int(df_students.at[i, "Studenti totali"]),
        "Docenti assunti": docenti_assunti[i],
        "Costo annuo docenti assunti (€)": costo_assunti,
        "Docenti a contratto": docenti_contratto[i],
        "Costo docenti a contratto (€)": costo_contr,
        "Personale direttivo (€)": personale_direttivo,
        "Totale costi personale (€)": totale_personale
    })

df_personale = pd.DataFrame(results_personale)



# ================= CALCOLO RIEPILOGO FINANZIARIO (Per Tab 4) ================= #
df_summary = pd.DataFrame({
    "Anno": years,
    "Costi struttura (€)": df_costs["Totale Costi Struttura (€/anno)"],
    "Costi personale (€)": df_personale["Totale costi personale (€)"],
    "Ricavi (€)": df_ricavi["Totale ricavi (€)"]
})
df_summary["Costi totali (€)"] = (
    df_summary["Costi struttura (€)"] + df_summary["Costi personale (€)"]
)
df_summary["Risultato netto (€)"] = (
    df_summary["Ricavi (€)"] - df_summary["Costi totali (€)"]
)


# ================= FUNZIONE HELPER PER FORMATO EURO (Globale) ================= #
def euro(x):
    """Formatta un numero come stringa Euro, gestendo NaN."""
    if pd.isna(x) or np.isnan(x):
        return "€ 0" if x == 0 else "" # Ritorna stringa vuota per i valori NaN, '€ 0' se zero
    elif x < 0:
        # Aggiusta il formato per i numeri negativi per avere il segno meno all'inizio
        return f"-€ {abs(x):,.0f}".replace(",", ".")
    else:
        return f"€ {x:,.0f}".replace(",", ".")

# ================= TAB 1: RICAVI ================= #
with tab1:
    st.subheader("Ricavi preventivi")
    st.markdown( 
        "### Variabili da definire:\n"
        "1. **Numero di studenti** e studentesse per anno per classe (**sidebar** a sinistra). "
        "L'ipotesi prevede un complessivo mantenimento di studenti e studentesse per anno, "
        "considerando anche un possibile turnover (studenti e studentesse che abbandonano e che entrano).\n"
        "2. **Retta annuale** per studente e studentessa per anno (**sidebar** a sinistra).\n"
        "3. **Contributi:**\n"
        " - contributi privati;\n"
        " - contributi enti pubblici;\n"
        " - contributi da donazioni;\n"
        " - contributi per progetti;\n"
        " - 5x1000."
    )

    # --- Tabella risultati ---
    st.subheader("Totale ricavi annuali")
    st.dataframe(df_ricavi, use_container_width=True)

     # --- Grafico ---
    fig_ricavi = px.bar(
        df_ricavi, 
        x="Anno", 
        y="Totale ricavi (€)",
        text_auto=True  # opzionale: mostra il valore sopra le barre
        )


    fig_ricavi.update_layout(
        title=dict(
            text="Andamento dei ricavi totali negli anni", 
            font=dict(size=20)
        ),
        yaxis=dict(
            title=dict(text="Totale ricavi (€)", font=dict(size=18)),
            tickprefix="€",
            tickformat="..0f",  # separatore migliaia con punto
            rangemode="tozero"
        ),
        xaxis=dict(
            title=dict(text="Anno", font=dict(size=18)),
            tickmode='linear',
            dtick=1
        ),
        font=dict(size=14),
        plot_bgcolor="white",
        hovermode="x unified"
    )

    # --- Mostra grafico ---
    st.plotly_chart(fig_ricavi, use_container_width=True)


# ================= TAB 2: COSTI PERSONALE ================= #
with tab2:
    st.subheader("Costi preventivi del personale")
    
    # Parametri
    costo_docente_assunto = st.number_input("Costo annuo docente assunto (€)", value=40000)
    costo_docente_contratto = st.number_input("Costo annuo docente a contratto (€)", value=15000)
    personale_direttivo = st.number_input("Costo annuo personale direttivo (€)", value=60000)

    st.markdown("---")
    st.subheader("Numero di docenti per anno (automatico in base al numero di studenti)")

    # Checkbox per override manuale
    manual_override = st.checkbox("Modifica manualmente il numero di docenti", value=False)

    docenti_assunti = []
    docenti_contratto = []

    for i, anno in enumerate(years):
        studenti = int(df_students.at[i, "Studenti totali"])

        # Logica automatica
        n_assunti = studenti // 8
        if anno == 1: n_assunti = max(n_assunti, 2)
        if anno == 2: n_assunti = max(n_assunti, 3)

        resto_studenti = studenti - n_assunti * 8

        # Docenti a contratto
        if anno in [1, 2]:
            n_contr = 2 + (1 if resto_studenti > 0 else 0)
        else:
            n_contr = 2 + (1 if resto_studenti > 0 else 0)

        # Keys separate per number_input
        key_assunti = f"assunti_{anno}_manual"
        key_contr = f"contr_{anno}_manual"

        if manual_override:
            val_assunti = st.number_input(
                f"Anno {anno} - Docenti assunti",
                min_value=0,
                value=n_assunti,
                step=1,
                key=key_assunti
            )
            val_contr = st.number_input(
                f"Anno {anno} - Docenti a contratto",
                min_value=0,
                value=n_contr,
                step=1,
                key=key_contr
            )
        else:
            val_assunti = n_assunti
            val_contr = n_contr
            st.write(f"Anno {anno} → Docenti assunti: {val_assunti}, Docenti a contratto: {val_contr}")

        docenti_assunti.append(val_assunti)
        docenti_contratto.append(val_contr)

    # Calcolo costi personale
    results_personale = []
    for i, anno in enumerate(years):
        costo_assunti = docenti_assunti[i] * costo_docente_assunto
        costo_contr = docenti_contratto[i] * costo_docente_contratto
        totale_personale = costo_assunti + costo_contr + personale_direttivo
        
        results_personale.append({
            "Anno": anno,
            "Studenti totali": int(df_students.at[i, "Studenti totali"]),
            "Docenti assunti": docenti_assunti[i],
            "Costo annuo docenti assunti (€)": costo_assunti,
            "Docenti a contratto": docenti_contratto[i],
            "Costo docenti a contratto (€)": costo_contr,
            "Personale direttivo (€)": personale_direttivo,
            "Totale costi personale (€)": totale_personale
        })

    df_personale = pd.DataFrame(results_personale)
    st.dataframe(df_personale, use_container_width=True)



# ================= TAB 3: COSTI STRUTTURA FISICA ================= #
with tab3:
    st.subheader("Costi preventivi di struttura")
    st.markdown( 
        "### Variabili da definire:\n"
        "1. Superficie totale in m² (modificabile nel box sotto).\n"
        "2. Parametri specifici di costo per fattore produttivo (modificabile nel box sotto).\n"
    )

    st.markdown(
        "Si sono assunti a riferimento i costi aggiornati di due sedi della Scuola Superiore Sant’Anna "
        "(palazzo Vernagalli e via Maffi), ritenute rappresentative per lo scopo, mediandone i valori al mq all’anno."
    )


    # --- NOTE SULLA DIMENSIONE DELLA SEDE ---
    st.subheader("Note sulla dimensione ipotizzata della sede")
    st.markdown(
        "**Primi due anni (tot. 200 mq):**\n"
        "- 2 aule x 40 mq = 80 mq\n"
        "- 2 uffici x 12 mq = 24 mq\n"
        "- 1 blocco WC x 20 mq = 20 mq\n"
        "- altre superfici = 76 mq (hall, reception, disimpegni, locali tecnici, ecc.)\n"
        "- **Totale: 200 mq**\n\n"
        "**Dal terzo anno (tot. circa 500 mq):**\n"
        "- 5 aule x 40 mq = 200 mq\n"
        "- 4 uffici x 12 mq = 48 mq\n"
        "- 2 blocchi WC x 20 mq = 40 mq\n"
        "- altre superfici = 200 mq (hall, reception, disimpegni, locali tecnici, ecc.)\n"
        "- **Totale: circa 500 mq**\n\n"
        "_La superficie è modificabile nel box sotto. Tutti i costi sono calcolati in base alla superficie specificata per ciascun anno._"
    )


    # --- Superficie totale per anno ---
    st.subheader("Superficie totale per anno (m², modificabile)")
    
    superfici = []
    for i, anno in enumerate(years):
        superficie = st.number_input(
            f"Anno {anno} - superficie totale (m²)", 
            min_value=50, 
            value=default_areas[i], 
            step=1,
            key=f"superficie_{anno}"
        )
        superfici.append(superficie)

    # --- Parametri costi struttura ---
    with st.expander("⚙️ Parametri costi struttura (€/m²/anno)", expanded=False):
        cost_manufab = st.number_input("Manutenzione fabbricati", value=2.60)
        cost_manimpi = st.number_input("Manutenzione impianti", value=11.96)
        cost_energia = st.number_input("Energia elettrica", value=11.52)
        cost_gas = st.number_input("Fornitura gas", value=7.05)
        cost_acqua = st.number_input("Acqua", value=3.78)
        cost_pulizie = st.number_input("Pulizie", value=38.43)
        ammort_arredi = st.number_input("Ammortamenti arredi", value=10.0)
        base_amm_att = st.number_input("Ammort. attrezzature primo anno", value=8.5)
        incremento_amm_att = st.number_input("Incremento annuo amm. attrezzature", value=8.5)
        reception_first_two = st.number_input("Reception / servizi primi 2 anni", value=230.58)
        reception_other = st.number_input("Reception / servizi anni 3-5", value=184.46)

    # --- Ricalcolo costi struttura con i nuovi parametri ---
    results_costs = []
    for i, anno in enumerate(years):
        superficie = float(superfici[i])
        amm_att_anno = base_amm_att + i * incremento_amm_att
        reception_m2 = reception_first_two if anno <= 2 else reception_other

        t_manufab = superficie * cost_manufab
        t_manimpi = superficie * cost_manimpi
        t_energia = superficie * cost_energia
        t_gas = superficie * cost_gas
        t_acqua = superficie * cost_acqua
        t_pulizie = superficie * cost_pulizie
        t_amm_arredi = superficie * ammort_arredi
        t_amm_att = superficie * amm_att_anno
        t_reception = superficie * reception_m2
        
        totale_struttura = sum([ 
            t_manufab, t_manimpi, t_energia, t_gas, t_acqua, t_pulizie, 
            t_amm_arredi, t_amm_att, t_reception 
        ])
        
        results_costs.append({
            "Anno": anno,
            "Studenti totali": int(df_students.at[i, "Studenti totali"]),
            "Superficie (m²)": superficie,
            "Manutenzione fabbricati (€/anno)": t_manufab,
            "Manutenzione impianti (€/anno)": t_manimpi,
            "Energia elettrica (€/anno)": t_energia,
            "Fornitura gas (€/anno)": t_gas,
            "Acqua (€/anno)": t_acqua,
            "Pulizie (€/anno)": t_pulizie,
            "Ammortamenti arredi (€/anno)": t_amm_arredi,
            "Ammort. attrezzature (€/anno)": t_amm_att,
            "Reception / servizi (€/anno)": t_reception,
            "Totale Costi Struttura (€/anno)": totale_struttura
        })
    df_costs = pd.DataFrame(results_costs)

    st.subheader("🏢 Dettaglio costi struttura per anno")
    st.dataframe(df_costs, use_container_width=True)
    
    
    fig = px.bar(
    df_costs,
    x="Anno",
    y="Totale Costi Struttura (€/anno)",
    text_auto=True  # opzionale: mostra il valore sopra le barre
    )

    fig.update_layout(
        yaxis_title="€",
        yaxis_tickprefix="€",
        yaxis_tickformat="."
    )

    # 👉 Forza asse Y a partire da 0
    fig.update_yaxes(rangemode="tozero")

    # 👉 Asse X solo valori interi
    fig.update_xaxes(tickmode="linear", dtick=1)

    st.plotly_chart(fig, use_container_width=True)




# ================= TAB 4: INDICI DI VALUTAZIONE ================= #
with tab7:
    st.subheader("Indici di valutazione")

    # --- Calcolo break-even (primo anno con ricavi >= costi totali) ---
    #breakeven_year = None
    #for i, row in df_summary.iterrows():
     #   if row["Ricavi (€)"] >= row["Costi totali (€)"]:
      #      breakeven_year = int(row["Anno"])
       #     break
            
    #if breakeven_year:
     #   st.metric("Break-even raggiunto nell'Anno", breakeven_year)
    #else:
     #   st.info("Break-even non raggiunto nei 5 anni considerati.")

    # --- Grafico riepilogativo ---
    fig_summary = px.line(
        df_summary, 
        x="Anno", 
        y=["Ricavi (€)", "Costi totali (€)"], 
        markers=True,
        color_discrete_map={
            "Ricavi (€)": "green",    
            "Costi totali (€)": "red"
        },
        labels={
            "Ricavi (€)": "Ricavi",
            "Costi totali (€)": "Costi"
        }
    )

    fig_summary.update_layout(
        yaxis_title="€", 
        yaxis_tickprefix="€", 
        yaxis_tickformat=".0f", 
        legend_title_text=""
    )

    # Forza asse Y da zero
    fig_summary.update_yaxes(rangemode="tozero")

    # Asse X solo numeri interi
    fig_summary.update_xaxes(tickmode="linear", dtick=1)

    st.plotly_chart(fig_summary, use_container_width=True)


        # --- Ricalcolo riepilogo (assicura dati aggiornati da tutte le tabs) ---
    df_summary = pd.DataFrame({
        "Anno": years,
        "Ricavi (€)": df_ricavi["Totale ricavi (€)"],
        "Costi struttura (€)": df_costs["Totale Costi Struttura (€/anno)"],
        "Costi personale (€)": df_personale["Totale costi personale (€)"]
      
    })
    df_summary["Costi totali (€)"] = (
        df_summary["Costi struttura (€)"] + df_summary["Costi personale (€)"]
    )
    df_summary["Risultato netto (€)"] = (
        df_summary["Ricavi (€)"] - df_summary["Costi totali (€)"]
    )

    st.subheader("Dettaglio costi e ricavi per anno")
    st.dataframe(df_summary, use_container_width=True)
    

    # --- Grafico del risultato netto ---
    # Creiamo una colonna temporanea per il colore
    df_summary["Segno"] = df_summary["Risultato netto (€)"].apply(lambda x: "Positivo" if x >= 0 else "Negativo")

    # --- Grafico del risultato netto ---
    st.subheader("EBIT per anno (ricavi - costi)")
    fig_risultato = px.bar(
        df_summary,
        x="Anno",
        y="Risultato netto (€)",
        color="Segno",
        color_discrete_map={
            "Positivo": "green",
            "Negativo": "red"
        },
        text="Risultato netto (€)"  # opzionale: mostra i valori sulle barre
    )

    fig_risultato.update_layout(
        yaxis_title="€",
        yaxis_tickprefix="€",
        yaxis_tickformat=",",
        showlegend=False
    )

    # Forza asse Y da zero se vuoi vedere anche i negativi rispetto a zero
    fig_risultato.update_yaxes(rangemode="tozero")

    st.plotly_chart(fig_risultato, use_container_width=True)






# ================= TAB 5: CONTO ECONOMICO ================= #

with tab4:
    st.subheader("Conto economico previsionale")

    # --- Selezione anni disponibili ---
    anni_disponibili = sorted(df_summary["Anno"].unique())
    anni_limite = anni_disponibili[:5]  # max anni 5

    st.markdown("### Seleziona gli anni da visualizzare")
    anni_attivi = []

    for a in anni_limite:
        if st.checkbox(f"Mostra Anno {a}", value=True, key=f"show_{a}"):
            anni_attivi.append(a)

    if len(anni_attivi) == 0:
        st.warning("Seleziona almeno un anno per visualizzare il Conto Economico.")
        st.stop()

    # Funzione euro
    def euro(valore):
        return f"-€ {abs(valore):,.0f}".replace(",", ".") if valore < 0 else f"€ {valore:,.0f}".replace(",", ".")

    # Funzione percentuale
    def percentuale(valore, totale):
        if totale == 0:
            return "0%"
        return f"{(valore / totale * 100):.1f}%"

    # ==============================================
    # COSTRUZIONE DINAMICA DEI VALORI PER OGNI ANNO
    # ==============================================
    valori = {}

    for a in anni_attivi:

        df_row = df_summary[df_summary["Anno"] == a].iloc[0]
        df_cost_row = df_costs[df_costs["Anno"] == a].iloc[0]

        ricavi = df_row.get("Ricavi (€)", 0) + altri_contributi
        struttura = df_row.get("Costi struttura (€)", 0)
        personale = df_row.get("Costi personale (€)", 0)

        amm = df_cost_row.get("Ammort. attrezzature (€/anno)", 0) + \
              df_cost_row.get("Ammortamenti arredi (€/anno)", 0)

        per_servizi = struttura - amm
        materie_prime = 0
        godimento_beni = 0

        costi_tot = personale + materie_prime + godimento_beni + per_servizi + amm
        diff = ricavi - costi_tot
        utile_netto = diff

        valori[a] = {
            "ricavi_puri": df_row.get("Ricavi (€)", 0),
            "altri_contributi": altri_contributi,
            "altri_ricavi": 0,
            "ricavi_tot": ricavi,
            "personale": personale,
            "primo_margine": ricavi - personale,
            "materie_prime": materie_prime,
            "godimento_beni": godimento_beni,
            "per_servizi": per_servizi,
            "ammortamenti": amm,
            "costi_tot": costi_tot,
            "risultato_operativo": diff,
            "proventi_partecipazioni": 0,
            "altri_proventi_fin": 0,
            "interessi_oneri": 0,
            "risultato_prima_imposte": diff,
            "imposte": 0,
            "utile_netto": utile_netto,
        }

    # ==========================================================
    #                       TABELLA HTML
    # ==========================================================

    def col_header():
        h = "<tr><th>Conto economico</th>"
        for a in anni_attivi:
            h += f"<th colspan='2' style='text-align:center;'>Anno {a}</th>"
        h += "</tr>"

        h += "<tr><th></th>"
        for a in anni_attivi:
            h += "<th>Valore</th><th>%</th>"
        h += "</tr>"
        return h

    def riga(label, key, bold=False, sub=False, base="ricavi", show_perc=True):
        """
        show_perc=True  → mostra % (solo fino al B)
        show_perc=False → quella riga NON mostra la % (celle vuote)
        """
        style = " class='sub'" if sub else ""
        if bold:
            label = f"<b>{label}</b>"

        totale_ref = "ricavi_tot" if base == "ricavi" else "costi_tot"

        celle = ""
        for a in anni_attivi:
            v = valori[a][key]
            tot = valori[a][totale_ref]
            perc = percentuale(v, tot) if show_perc else ""
            celle += f"<td class='value'>{euro(v)}</td><td class='perc'>{perc}</td>"

        return f"<tr{style}><td class='label'>{label}</td>{celle}</tr>"

    html = f"""
    <style>
    table.conto {{
        width: 100%; border-collapse: collapse; font-size: 14px; margin-top: 20px;
    }}
    table.conto th {{
        background-color: #e1e8f7; text-align: center; padding: 6px 10px; font-weight: bold;
    }}
    table.conto td {{ padding: 6px 10px; border-bottom: 1px solid #ddd; }}
    tr.section td {{
        background-color: #f2f5fc; font-weight: bold; border-top: 2px solid #ccc;
    }}
    tr.sub td {{ padding-left: 20px; }}
    td.label {{ text-align: left; }}
    td.value {{ text-align: right; white-space: nowrap; }}
    td.perc {{ text-align: right; color: #555; font-size: 12px; }}
    </style>

    <table class="conto">

        {col_header()}

        <!-- A) VALORE DELLA PRODUZIONE -->
        <tr class="section"><td colspan="{1 + 2*len(anni_attivi)}">A) Valore della produzione</td></tr>

        {riga("1) Ricavi delle vendite e delle prestazioni", "ricavi_puri", sub=True, base="ricavi")}
        {riga("2) Altri contributi", "altri_contributi", sub=True, base="ricavi")}
        {riga("5) Altri ricavi e proventi", "altri_ricavi", sub=True, base="ricavi")}
        {riga("Totale valore della produzione (A)", "ricavi_tot", bold=True, base="ricavi")}

        <!-- B) COSTI DELLA PRODUZIONE -->
        <tr class="section"><td colspan="{1 + 2*len(anni_attivi)}">B) Costi della produzione</td></tr>

        {riga("6) Totale costi per il personale", "personale", sub=True, base="costi")}

        <!-- PRIMO MARGINE OPERATIVO: NESSUNA % -->
        {riga("Primo margine operativo", "primo_margine", bold=True, base="ricavi", show_perc=False)}

        {riga("7) Materie prime, sussidiarie, merci", "materie_prime", sub=True, base="costi")}
        {riga("8) Per godimento di beni di terzi", "godimento_beni", sub=True, base="costi")}
        {riga("9) Per servizi", "per_servizi", sub=True, base="costi")}
        {riga("10) Ammortamenti e svalutazioni", "ammortamenti", sub=True, base="costi")}

        {riga("Totale costi della produzione (B)", "costi_tot", bold=True, base="costi")}

        <!-- RISULTATO OPERATIVO: NESSUNA % -->
        {riga("Risultato operativo (A - B)", "risultato_operativo", bold=True, base="ricavi", show_perc=False)}

        <!-- C) PROVENTI E ONERI FINANZIARI – SENZA % -->
        <tr class="section"><td colspan="{1 + 2*len(anni_attivi)}">C) Proventi e oneri finanziari</td></tr>

        {riga("15) Proventi da partecipazioni", "proventi_partecipazioni", sub=True, base="ricavi", show_perc=False)}
        {riga("16) Altri proventi finanziari", "altri_proventi_fin", sub=True, base="ricavi", show_perc=False)}
        {riga("17) Interessi e altri oneri finanziari", "interessi_oneri", sub=True, base="ricavi", show_perc=False)}

        {riga("Totale proventi e oneri finanziari", "materie_prime", bold=True, base="ricavi", show_perc=False)}

        {riga("Risultato prima delle imposte", "risultato_prima_imposte", bold=True, base="ricavi", show_perc=False)}
        {riga("20) Imposte", "imposte", base="ricavi", show_perc=False)}
        {riga("Risultato dell'esercizio", "utile_netto", bold=True, base="ricavi", show_perc=False)}

    </table>
    """

    components.html(html, height=900, scrolling=True)

    st.session_state["valori"] = valori



##############################################
#              STATO PATRIMONIALE           #
##############################################


with tab5:


    st.header("Stato patrimoniale iniziale")

    # Help in stile tooltip accanto al titolo
    st.markdown("""
    <div style='display:flex;align-items:center;gap:8px;'>
        <h3 style='margin:0;'>Clicca qui per visionare lo stato patrimoniale di Fondazione Urban Lab Genoa International School (F.U.L.G.I.S.)</h3>
        <span title="Clicca il link per visionare lo stato patrimoniale di Fondazione Urban Lab Genoa International School (F.U.L.G.I.S.).">
            <a href="https://fulgis.it/wp-content/uploads/2025/05/Bilancio-2024-fascicolo.pdf" target="_blank" 
               style="text-decoration:none;font-size:18px;cursor:pointer;">CLICCA QUI</a>
        </span>
    </div>
    """, unsafe_allow_html=True)

    ANNO1_LABEL = "Anno 1"
    ANNO2_LABEL = "Anno 2"

    # ============================================
    # FUNZIONI DI CALCOLO AUTOMATICO
    # ============================================

    def crediti_clienti_auto(anno):
        ricavi = df_ricavi[df_ricavi["Anno"] == anno]["Totale ricavi (€)"].iloc[0]
        return int(0.30 * ricavi)

    def crediti_tributari_auto(anno):
        costi = df_summary[df_summary["Anno"] == anno]["Costi totali (€)"].iloc[0]
        return int(0.01 * costi)

    def debiti_fornitori_auto(anno):
        costi = df_summary[df_summary["Anno"] == anno]["Costi totali (€)"].iloc[0]
        return int(costi / 6)

    def debiti_previdenza_auto(anno):
        personale = df_personale[df_personale["Anno"] == anno]["Totale costi personale (€)"].iloc[0]
        return int(personale * 0.07)

    def debiti_tributari_auto(anno):
        ricavi = df_ricavi[df_ricavi["Anno"] == anno]["Totale ricavi (€)"].iloc[0]
        return int(ricavi * 0.01)

    def tfr_auto(anno):
        personale_fino_anno = df_personale[df_personale["Anno"] <= anno]["Totale costi personale (€)"].sum()
        return int(personale_fino_anno * 0.07)

    def liquidita_auto():
        liquidita_iniziale = 80000
        perdita_tot = df_summary["Risultato netto (€)"].clip(upper=0).abs().sum()
        return max(0, int(liquidita_iniziale - perdita_tot))

    # ============================================
    # IMMOBILIZZAZIONI REALISTICHE
    # ============================================

    immobilizzazioni = {
        1: {
            "CONCESSIONI": 0,
            "AVVIAMENTO": 0,
            "ALTRE_IMM": 0,
            "IMPIANTI": 20000,
            "ATTREZZATURE": 40000,
            "ALTRI_BENI": 35000
        },
        2: {
            "CONCESSIONI": 10000,
            "AVVIAMENTO": 0,
            "ALTRE_IMM": 18000,
            "IMPIANTI": 15000,
            "ATTREZZATURE": 30000,
            "ALTRI_BENI": 25000
        }
    }

    # ============================================
    # GENERA STATO PATRIMONIALE ANNO
    # ============================================

    def genera_sp_anno(anno):
        return {
            # IMMOBILIZZAZIONI
            "CONCESSIONI": immobilizzazioni[anno]["CONCESSIONI"],
            "AVVIAMENTO": immobilizzazioni[anno]["AVVIAMENTO"],
            "ALTRE_IMM": immobilizzazioni[anno]["ALTRE_IMM"],
            "IMPIANTI": immobilizzazioni[anno]["IMPIANTI"],
            "ATTREZZATURE": immobilizzazioni[anno]["ATTREZZATURE"],
            "ALTRI_BENI": immobilizzazioni[anno]["ALTRI_BENI"],
            "TOT_IMM_FIN": 0,

            # ATTIVO CIRCOLANTE
            "RIM_PRIME": 0,
            "CRED_CLIENTI": 0,
            "CRED_TRIBUTARI": 0,
            "IMPOSTE_ANTICIPATE": 0,
            "CRED_ALTRI": 0,
            "TOT_ATT_FIN": 0,

            # LIQUIDITÀ
            "DEPOSITI": liquidita_auto(),
            "CASSA": 0,
            "RATEI_ATTIVI": 0,

            # PATRIMONIO NETTO
            "CAPITALE": 0,
            "RIS_SUPERPREZZO": 0,
            "RIS_RIVALUTAZIONE": 0,
            "RIS_LEGALE": 0,
            "RIS_STATUTARIE": 0,
            "RIS_ALTRE": 0,
            "RIS_COPERTURE": 0,
            "UTILI_PN": 0,
            "UTILE_ESERCIZIO": df_summary[df_summary["Anno"] == anno]["Risultato netto (€)"].iloc[0],
            "RIS_NEG_AZIONI": 0,

            # FONDI & TFR
            "ALTRI_FONDI": 0,
            "TFR": tfr_auto(anno),

            # DEBITI
            "DEB_FORNITORI": 0,
            "DEB_TRIBUTARI": 0,
            "DEB_PREVIDENZA": 0,
            "DEB_ALTRI": 0,
            "RATEI_PASSIVI": 0,
        }

    # ============================================
    # INIZIALIZZA SESSIONE
    # ============================================

    if "sp_anno1" not in st.session_state:
        st.session_state.sp_anno1 = genera_sp_anno(1)

    if "sp_anno2" not in st.session_state:
        st.session_state.sp_anno2 = genera_sp_anno(2)

    anno1_vals = st.session_state.sp_anno1
    anno2_vals = st.session_state.sp_anno2

    # ============================================
    # STRUTTURA RIGHE STATO PATRIMONIALE
    # ============================================

    rows = [

        # ATTIVO
        {"label": "ATTIVO", "code": "A_title", "level": 0, "kind": "title"},

        {"label": "A) IMMOBILIZZAZIONI", "code": "B_IMM", "level": 0, "kind": "title"},
        {"label": "I - Immobilizzazioni materiali", "code": "B_IMM_MAT", "level": 1, "kind": "title"},
        {"label": "Impianti", "code": "IMPIANTI", "level": 2, "kind": "data"},
        {"label": "Attrezzature", "code": "ATTREZZATURE", "level": 2, "kind": "data"},
        {"label": "Altri beni", "code": "ALTRI_BENI", "level": 2, "kind": "data"},
        {"label": "Totale imm. materiali", "code": "TOT_IMM_MAT", "level": 2, "kind": "total"},

        {"label": "II - Immobilizzazioni immateriali", "code": "B_IMM_IMM", "level": 1, "kind": "title"},
        {"label": "Concessioni", "code": "CONCESSIONI", "level": 2, "kind": "data"},
        {"label": "Spese di costituzione", "code": "AVVIAMENTO", "level": 2, "kind": "data"},
        {"label": "Altre immobilizzazioni immateriali", "code": "ALTRE_IMM", "level": 2, "kind": "data"},
        {"label": "Totale imm. immateriali", "code": "TOT_IMM_IMM", "level": 2, "kind": "total"},

        {"label": "III - Immobilizzazioni finanziarie", "code": "B_IMM_FIN", "level": 1, "kind": "title"},
        {"label": "Totale imm. finanziarie", "code": "TOT_IMM_FIN", "level": 2, "kind": "data"},

        {"label": "Totale B) Immobilizzazioni", "code": "TOT_B_IMMOB", "level": 1, "kind": "total"},

        {"label": "B) ATTIVO CIRCOLANTE", "code": "C_ATT_CIRC", "level": 0, "kind": "title"},
        {"label": "I) Rimanenze", "code": "C_RIM", "level": 1, "kind": "title"},
        {"label": "1) Materiali", "code": "RIM_PRIME", "level": 2, "kind": "data"},

        {"label": "II) Crediti", "code": "C_CRED", "level": 1, "kind": "title"},
        {"label": "Verso clienti", "code": "CRED_CLIENTI", "level": 2, "kind": "data"},
        {"label": "Crediti tributari", "code": "CRED_TRIBUTARI", "level": 2, "kind": "data"},
        {"label": "Imposte anticipate", "code": "IMPOSTE_ANTICIPATE", "level": 2, "kind": "data"},
        {"label": "Crediti verso altri", "code": "CRED_ALTRI", "level": 2, "kind": "data"},
        {"label": "Totale crediti", "code": "TOT_CREDITI", "level": 2, "kind": "total"},

        {"label": "III - Attività finanziarie", "code": "C_ATT_FIN", "level": 1, "kind": "title"},
        {"label": "Attività fin. non imm.", "code": "TOT_ATT_FIN", "level": 2, "kind": "data"},

        {"label": "IV - Disponibilità liquide", "code": "C_LIQ", "level": 1, "kind": "title"},
        {"label": "Depositi bancari", "code": "DEPOSITI", "level": 2, "kind": "data"},
        {"label": "Disponibilità liquide", "code": "CASSA", "level": 2, "kind": "data"},
        {"label": "Totale disponibilità liquide", "code": "TOT_LIQ", "level": 2, "kind": "total"},

        {"label": "Totale B) Attivo circolante", "code": "TOT_C", "level": 1, "kind": "total"},

        {"label": "C) Ratei e risconti attivi", "code": "RATEI_ATTIVI", "level": 0, "kind": "data"},

        {"label": "TOTALE ATTIVO", "code": "TOT_ATTIVO", "level": 0, "kind": "total"},

        # PASSIVO
        {"label": "PASSIVO", "code": "PASSIVO_T", "level": 0, "kind": "title"},
        
        {"label": "PASSIVO", "code": "P_title", "level": 0, "kind": "title"},
        {"label": "A) PATRIMONIO NETTO", "code": "PN", "level": 0, "kind": "title"},
        {"label": "Capitale sociale", "code": "CAPITALE", "level": 1, "kind": "data"},
        {"label": "Utile/perdita dell'esercizio", "code": "UTILE_ESERCIZIO", "level": 1, "kind": "data"},
        {"label": "Utili degli anni precedenti", "code": "UTILI_PN", "level": 1, "kind": "data"},
        {"label": "Totale patrimonio netto", "code": "TOT_PN", "level": 1, "kind": "total"},

        {"label": "B) PASSIVO NON CORRENTE", "code": "FONDI", "level": 0, "kind": "title"},
        {"label": "Fondi per benefici ai dipendenti e TFR", "code": "TFR", "level": 1, "kind": "data"},
        {"label": "Debiti finanziari a medio-lungo termine", "code": "DEB_PREVIDENZA", "level": 1, "kind": "data"},
        {"label": "Altri fondi", "code": "ALTRI_FONDI", "level": 1, "kind": "data"},

        {"label": "C) PASSIVO CORRENTE", "code": "DEBITI", "level": 0, "kind": "title"},
        {"label": "Debiti verso fornitori", "code": "DEB_FORNITORI", "level": 1, "kind": "data"},
        {"label": "Debiti verso l'erario", "code": "DEB_TRIBUTARI", "level": 1, "kind": "data"},
        {"label": "Debiti finanziari a breve termine", "code": "DEB_ALTRI", "level": 1, "kind": "data"},
        

        {"label": "TOTALE PASSIVO", "code": "TOT_PASSIVO", "level": 0, "kind": "total"},
    ]

    # ============================================
    # TOTALI
    # ============================================

    total_map = {
        "TOT_A_SOC": ["A_SOC"],
        "TOT_IMM_IMM": ["CONCESSIONI", "AVVIAMENTO", "ALTRE_IMM"],
        "TOT_IMM_MAT": ["IMPIANTI", "ATTREZZATURE", "ALTRI_BENI"],
        "TOT_B_IMMOB": ["CONCESSIONI", "AVVIAMENTO", "ALTRE_IMM", "IMPIANTI", "ATTREZZATURE", "ALTRI_BENI","TOT_IMM_FIN"],

        "TOT_CREDITI": ["CRED_CLIENTI", "CRED_TRIBUTARI", "IMPOSTE_ANTICIPATE", "CRED_ALTRI"],
        "TOT_LIQ": ["DEPOSITI", "CASSA"],

        "TOT_C": [
            "RIM_PRIME", "CRED_CLIENTI", "CRED_TRIBUTARI",
            "IMPOSTE_ANTICIPATE", "CRED_ALTRI",
            "TOT_ATT_FIN", "DEPOSITI", "CASSA"
        ],

        "TOT_ATTIVO": ["TOT_A_SOC", "CONCESSIONI", "AVVIAMENTO", "ALTRE_IMM","IMPIANTI", "ATTREZZATURE", "ALTRI_BENI","TOT_IMM_FIN","RIM_PRIME", "CRED_CLIENTI", "CRED_TRIBUTARI","IMPOSTE_ANTICIPATE", "CRED_ALTRI","TOT_ATT_FIN", "DEPOSITI", "CASSA", "RATEI_ATTIVI"],

        "TOT_PN": [
            "CAPITALE", "UTILI_PN", "UTILE_ESERCIZIO"
        ],

        "TOT_FONDI": ["ALTRI_FONDI"],
        "TOT_DEBITI": ["DEB_FORNITORI", "DEB_TRIBUTARI", "DEB_PREVIDENZA", "DEB_ALTRI"],
        "TOT_PASSIVO": ["CAPITALE", "UTILI_PN", "UTILE_ESERCIZIO", "ALTRI_FONDI", "TFR", "DEB_FORNITORI", "DEB_TRIBUTARI", "DEB_PREVIDENZA", "DEB_ALTRI"],
    }

    # ============================================
    # SUPPORT FUNCTIONS
    # ============================================

    def get_val(year_dict, code):
        return int(year_dict.get(code, 0))

    def compute_total(code, year_dict):
        return sum(get_val(year_dict, c) for c in total_map.get(code, []))

    # ============================================
    # RENDER ATTIVO/PASSIVO AFFIANCATI
    # ============================================

    def render_bilancio(anno_label, vals):

        st.markdown(f"## {anno_label}")
        st.markdown("---")

        attivo_rows = []
        passivo_rows = []
        passivo_mode = False

        for r in rows:
            if r["code"] == "PASSIVO_T":
                passivo_mode = True
                continue
            if not passivo_mode:
                attivo_rows.append(r)
            else:
                passivo_rows.append(r)

        max_len = max(len(attivo_rows), len(passivo_rows))

        for i in range(max_len):

            row_att = attivo_rows[i] if i < len(attivo_rows) else None
            row_pas = passivo_rows[i] if i < len(passivo_rows) else None

            col_l_att, col_v_att, col_l_pas, col_v_pas = st.columns([3, 1.2, 3, 1.2])

            # LATO ATTIVO
            if row_att:
                pad_left = 10 + row_att["level"] * 15
                style = "font-weight:bold;" if row_att["kind"] in ["title", "total"] else ""

                with col_l_att:
                    st.markdown(f"<div style='padding-left:{pad_left}px;{style}'>{row_att['label']}</div>", unsafe_allow_html=True)

                with col_v_att:
                    if row_att["kind"] == "total":
                        val = compute_total(row_att["code"], vals)
                        st.markdown(f"<div style='text-align:right;font-weight:bold;'>{val}</div>", unsafe_allow_html=True)
                    elif row_att["kind"] == "title":
                        st.markdown("&nbsp;", unsafe_allow_html=True)
                    else:
                        num = st.number_input("", value=get_val(vals, row_att["code"]), key=f"{row_att['code']}_{anno_label}_att")
                        vals[row_att["code"]] = int(num)
            else:
                col_l_att.markdown("&nbsp;")
                col_v_att.markdown("&nbsp;")

            # LATO PASSIVO
            if row_pas:
                pad_left = 10 + row_pas["level"] * 15
                style = "font-weight:bold;" if row_pas["kind"] in ["title", "total"] else ""

                with col_l_pas:
                    st.markdown(f"<div style='padding-left:{pad_left}px;{style}'>{row_pas['label']}</div>", unsafe_allow_html=True)

                with col_v_pas:
                    if row_pas["kind"] == "total":
                        val = compute_total(row_pas["code"], vals)
                        st.markdown(f"<div style='text-align:right;font-weight:bold;'>{val}</div>", unsafe_allow_html=True)
                    elif row_pas["kind"] == "title":
                        st.markdown("&nbsp;", unsafe_allow_html=True)
                    else:
                        num = st.number_input("", value=get_val(vals, row_pas["code"]), key=f"{row_pas['code']}_{anno_label}_pas")
                        vals[row_pas["code"]] = int(num)
            else:
                col_l_pas.markdown("&nbsp;")
                col_v_pas.markdown("&nbsp;")

    # ===== RENDER FINALE =====

    render_bilancio("Anno 1", anno1_vals)
    render_bilancio("Anno 2", anno2_vals)

    st.session_state.sp_anno1 = anno1_vals
    st.session_state.sp_anno2 = anno2_vals




# ================= TAB 8: CASH FLOW ================= #


with tab6:
    st.header("Rendiconto Finanziario")

    # Recupero dati
    sp1 = st.session_state.get("sp_anno1", None)
    sp2 = st.session_state.get("sp_anno2", None)
    valori_ce = st.session_state.get("valori", None)

    if sp1 is None or sp2 is None or valori_ce is None:
        st.error("⚠️ Compila prima Stato Patrimoniale (Tab 7) e Conto Economico (Tab 5).")
        st.stop()

    # ------------------------------
    # FUNZIONI LETTURA SP E CE
    # ------------------------------

    def sp_get(code, year):
        return int((sp1 if year == 1 else sp2).get(code, 0))

    def delta(code):
        return sp_get(code, 1) - sp_get(code, 2)

    def ce_get(key):
        return valori_ce.get(2, {}).get(key, 0)

    # ------------------------------
    # LETTURA VALORI CE
    # ------------------------------
    risultato_operativo = ce_get("risultato_operativo")
    ammortamenti = ce_get("ammortamenti")
    gestione_fin = ce_get("totale_proventi_oneri")  # proventi - oneri
    gestione_extra = 0
    gestione_fiscale = -ce_get("imposte")

    # ------------------------------
    # VARIAZIONI CCN
    # ------------------------------
    var_rimanenze    = -delta("RIM_PRIME")
    var_cred_com     = -delta("CRED_CLIENTI")
    var_cred_altri   = -delta("CRED_ALTRI")
    var_imposte_ant  = -delta("IMPOSTE_ANTICIPATE")
    var_att_fin      = -delta("TOT_ATT_FIN")
    var_ratei_att    = -delta("RATEI_ATTIVI")

    var_deb_com      = delta("DEB_FORNITORI")
    var_deb_div      = delta("DEB_ALTRI")
    var_deb_trib     = delta("DEB_TRIBUTARI")
    var_ratei_pass   = delta("RATEI_PASSIVI")

    # ------------------------------
    # VARIAZIONI INVESTIMENTI
    # ------------------------------
    var_imm_imm = -delta("TOT_IMM_IMM")
    var_imm_mat = -delta("TOT_IMM_MAT")
    var_imm_fin = -delta("TOT_IMM_FIN")

    # ------------------------------
    # VARIAZIONI FINANZIAMENTI
    # ------------------------------

    var_deb_fin = 0  # NON HAI DEBITI FINANZIARI IN TAB 7 – resterebbe 0
    var_tfr     = delta("TFR")
    var_fondi   = delta("ALTRI_FONDI")
    var_pn      = delta("TOT_PN")
    var_deb_lp  = 0  # non esistono debiti commerciali LP nel tuo SP

    # ------------------------------
    # CALCOLO TOTALI SECONDO LE TUE FORMULE
    # ------------------------------

    # 1) FLUSSO DI CASSA DELLA GESTIONE CARATTERISTICA
    FCGC = risultato_operativo + ammortamenti

    # 2) FLUSSO POTENZIALE DI CCN
    FPCCN = FCGC + gestione_fin + gestione_extra + gestione_fiscale

    # 3) FLUSSO DI CASSA DELLA GESTIONE REDDITUALE
    FCGR = FPCCN + (
        var_rimanenze +
        var_cred_com +
        var_cred_altri +
        var_att_fin +
        var_ratei_att +
        var_deb_com +
        var_deb_div +
        var_ratei_pass +
        var_deb_trib
    )

    # 4) FLUSSO DI CASSA NETTO AZIENDALE
    FCNA = FCGR + (
        var_imm_imm +
        var_imm_mat +
        var_imm_fin +
        var_deb_fin +
        var_tfr +
        var_deb_lp +
        var_deb_div +
        var_fondi +
        var_pn
    )

    # 5) LIQUIDITÀ
    liquidità_inizio = sp_get("TOT_LIQ", 2)
    liquidità_fine   = liquidità_inizio + FCNA

    # ------------------------------
    # COSTRUZIONE RENDICONTO
    # ------------------------------
    cf_rows = [
        ("RENDICONTO FINANZIARIO", "ANNO 2"),

        ("Risultato operativo", risultato_operativo),
        ("Ammortamenti e accantonamenti (in valore assoluto)", ammortamenti),

        ("FLUSSO DI CASSA DELLA GESTIONE CARATTERISTICA", FCGC),

        ("Risultato della Gestione Finanziaria", gestione_fin),
        ("Risultato della Gestione Straordinaria", gestione_extra),
        ("Risultato della Gestione Fiscale", gestione_fiscale),

        ("FLUSSO POTENZIALE DI CCN", FPCCN),

        ("Variazione delle Rimanenze", var_rimanenze),
        ("Variazione dei Crediti commerciali", var_cred_com),
        ("Variazione dei Altri crediti", var_cred_altri),
        ("Variazione Attività finanziarie", var_att_fin),
        ("Variazione dei Ratei e risconti attivi", var_ratei_att),
        ("Variazione dei Debiti commerciali", var_deb_com),
        ("Variazione dei Debiti diversi", var_deb_div),
        ("Variazione dei Debiti tributari", var_deb_trib),
        ("Variazione dei Ratei e risconti passivi", var_ratei_pass),

        ("FLUSSO DI CASSA DELLA GESTIONE REDDITUALE", FCGR),

        ("Variazione Immobilizzazioni immateriali", var_imm_imm),
        ("Variazione Immobilizzazioni materiali", var_imm_mat),
        ("Variazione Immobilizzazioni finanziarie", var_imm_fin),

        ("Variazione Fondo TFR", var_tfr),
        ("Variazione Fondo Rischi e oneri futuri", var_fondi),
        ("Variazione Patrimonio Netto", var_pn),

        ("FLUSSO DI CASSA NETTO AZIENDALE", FCNA),

        ("Liquidità netta di inizio anno", liquidità_inizio),
        ("LIQUIDITÀ NETTA DI FINE ANNO", liquidità_fine),
    ]

    df_cf = pd.DataFrame(cf_rows, columns=["Voce", "Valore"])

    # ------------------------------
    # STILE
    # ------------------------------
    def style_cf(df):
        blocchi = [
            "RENDICONTO FINANZIARIO",
            "FLUSSO DI CASSA DELLA GESTIONE CARATTERISTICA",
            "FLUSSO POTENZIALE DI CCN",
            "FLUSSO DI CASSA DELLA GESTIONE REDDITUALE",
            "FLUSSO DI CASSA NETTO AZIENDALE"
        ]
        def hl(row):
            if row["Voce"] in blocchi:
                return ['background-color:#FFF4C2; font-weight:bold;'] * 2
            return [''] * 2

        return df.style.apply(hl, axis=1).format(precision=0, na_rep="")

    st.dataframe(style_cf(df_cf), use_container_width=True)






######## TAB 8 Previsione del fabbisogno finanziario iniziale#####

with tab8:
    st.header("Previsione del fabbisogno finanziario iniziale")

    st.markdown("""
    Inserisci qui sotto le principali voci di fabbisogno iniziale per l'avvio della scuola 
    e le relative fonti di finanziamento.  
    Le cifre sono completamente personalizzabili.
    """)

    # ============================
    # FABBRISOGNO FINANZIARIO
    # ============================

    st.subheader("Fabbisogno Finanziario Iniziale")

    fabbisogno_default = {
        "Ristrutturazione e adeguamento locali (€)": 150000,
        "Arredi e attrezzature scolastiche (€)": 80000,
        "Laboratori e tecnologie (€)": 60000,
        "Campagna marketing e comunicazione (€)": 20000,
        "Costi autorizzazioni / accreditamenti (€)": 15000,
        "Capitale circolante iniziale (€)": 50000,
    }

    if "fabbisogno_vals" not in st.session_state:
        st.session_state.fabbisogno_vals = fabbisogno_default.copy()

    fab_vals = st.session_state.fabbisogno_vals

    total_fabbisogno = 0
    for label, default_val in fab_vals.items():
        val = st.number_input(label, value=int(default_val), min_value=0)
        fab_vals[label] = val
        total_fabbisogno += val

    st.markdown(f"### 🔵 Totale fabbisogno finanziario: **€ {total_fabbisogno:,.0f}**")


    # ============================
    # FONTI DI FINANZIAMENTO
    # ============================

    st.subheader("Fonti di Finanziamento Iniziali")

    finanziamenti_default = {
        "Conferimenti iniziali dei fondatori (€)": 1000000,
        "Erogazioni liberali / donazioni (€)": 30000,
        "Finanziamento bancario (€)": 120000,
        "Contributi pubblici (€)": 20000,
        "Altre entrate iniziali (€)": 10000,
    }

    if "fonti_vals" not in st.session_state:
        st.session_state.fonti_vals = finanziamenti_default.copy()

    fonti_vals = st.session_state.fonti_vals

    total_fonti = 0
    for label, default_val in fonti_vals.items():
        val = st.number_input(label, value=int(default_val), min_value=0)
        fonti_vals[label] = val
        total_fonti += val

    st.markdown(f"### 🟢 Totale fonti di finanziamento: **€ {total_fonti:,.0f}**")


    # ============================
    # VERIFICA COPERTURA
    # ============================

    st.markdown("---")
    st.subheader("Verifica copertura finanziaria")

    differenza = total_fonti - total_fabbisogno

    if differenza > 0:
        st.success(f"✔️ Le fonti superano il fabbisogno di **€ {differenza:,.0f}**.")
    elif differenza == 0:
        st.info("ℹ️ Le fonti coprono esattamente il fabbisogno iniziale.")
    else:
        st.error(f"❗ ATTENZIONE: mancano **€ {-differenza:,.0f}** per coprire il fabbisogno.")






