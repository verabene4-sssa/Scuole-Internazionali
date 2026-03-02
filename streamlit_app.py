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
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "Ricavi preventivi",
    "Costi preventivi del personale", 
    "Costi preventivi di struttura", 
    "Conto economico",
    "Stato patrimoniale",
    "Rendiconto finanziario",
    "Indici di valutazione"
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




# ================= TAB 7: INDICI DI VALUTAZIONE ================= #
with tab7:
    st.subheader("Indici di valutazione")

    # ================= RIEPILOGO DATI ================= #
    df_summary = pd.DataFrame({
        "Anno": years,
        "Ricavi (€)": df_ricavi["Totale ricavi (€)"],
        "Costi struttura (€)": df_costs["Totale Costi Struttura (€/anno)"],
        "Costi personale (€)": df_personale["Totale costi personale (€)"]
    })

    # Calcolo costi totali
    df_summary["Costi totali (€)"] = (
        df_summary["Costi struttura (€)"] +
        df_summary["Costi personale (€)"]
    )

    # Calcolo risultato netto (EBIT)
    df_summary["Risultato netto (€)"] = (
        df_summary["Ricavi (€)"] -
        df_summary["Costi totali (€)"]
    )

    # ================= BREAK EVEN ================= #
    breakeven_year = None
    for _, row in df_summary.iterrows():
        if row["Ricavi (€)"] >= row["Costi totali (€)"]:
            breakeven_year = int(row["Anno"])
            break

    if breakeven_year:
        st.metric("Break-even raggiunto nell'anno", breakeven_year)
    else:
        st.info("Break-even non raggiunto nei 5 anni considerati.")

    # ================= GRAFICO RICAVI VS COSTI ================= #
    st.subheader("Andamento Ricavi vs Costi")

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
            "value": "€",
            "variable": ""
        }
    )

    fig_summary.update_layout(
        yaxis_title="€",
        yaxis_tickprefix="€",
        yaxis_tickformat=",",
        legend_title_text=""
    )

    fig_summary.update_yaxes(rangemode="tozero")
    fig_summary.update_xaxes(tickmode="linear", dtick=1)

    st.plotly_chart(fig_summary, use_container_width=True)

    # ================= TABELLA DETTAGLIO ================= #
    st.subheader("Dettaglio costi e ricavi per anno")
    st.dataframe(df_summary, use_container_width=True)

    # ================= GRAFICO EBIT ================= #
    st.subheader("EBIT per anno (Ricavi - Costi)")

    df_summary["Segno"] = df_summary["Risultato netto (€)"].apply(
        lambda x: "Positivo" if x >= 0 else "Negativo"
    )

    fig_risultato = px.bar(
        df_summary,
        x="Anno",
        y="Risultato netto (€)",
        color="Segno",
        color_discrete_map={
            "Positivo": "green",
            "Negativo": "red"
        },
        text="Risultato netto (€)"
    )

    fig_risultato.update_layout(
        yaxis_title="€",
        yaxis_tickprefix="€",
        yaxis_tickformat=",",
        showlegend=False
    )

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

    st.subheader("Stato Patrimoniale previsionale")

    anni = years

    # -------------------------------
    # FONDO DI DOTAZIONE PROGRESSIVO
    # -------------------------------
    fondo_progressivo = [200000, 120000, 90000, 60000, 30000]
    fondo_cumulato = np.cumsum(fondo_progressivo)

    risultati = df_summary["Risultato netto (€)"].values

    # Perdite / utili cumulati
    cumulato = []
    somma = 0
    for r in risultati:
        somma += r
        cumulato.append(somma)

    # -------------------------------
    # COSTRUZIONE VALORI PER ANNO
    # -------------------------------

    sp = {}

    for i, anno in enumerate(anni):

        # ATTIVO
        imm_immateriali = max(30000 - i*5000, 10000)
        imm_materiali = df_costs.at[i, "Ammortamenti arredi (€/anno)"] * 5
        imm_fin = 10000

        tot_imm = imm_immateriali + imm_materiali + imm_fin

        rimanenze = 2000 + i*1000
        crediti = df_summary.at[i, "Ricavi (€)"] * 0.2
        att_fin_non_imm = 0

        liquidita = fondo_cumulato[i] + cumulato[i] - tot_imm - rimanenze - crediti

        tot_circ = rimanenze + crediti + att_fin_non_imm + liquidita
        totale_attivo = tot_imm + tot_circ

        # PASSIVO
        fondo = fondo_cumulato[i]
        risultato_es = risultati[i]
        utili_portati = cumulato[i] - risultato_es

        patrimonio_netto = fondo + utili_portati + risultato_es

        fondi_rischi = 5000 + i*1000
        tfr = df_personale.at[i, "Totale costi personale (€)"] * 0.07

        debiti = totale_attivo - patrimonio_netto - fondi_rischi - tfr

        sp[anno] = {
            # ATTIVO
            "imm_immateriali": imm_immateriali,
            "imm_materiali": imm_materiali,
            "imm_fin": imm_fin,
            "tot_imm": tot_imm,
            "rimanenze": rimanenze,
            "crediti": crediti,
            "att_fin_non_imm": att_fin_non_imm,
            "liquidita": liquidita,
            "tot_circ": tot_circ,
            "tot_attivo": totale_attivo,
            # PASSIVO
            "fondo": fondo,
            "fin_invest": 0,
            "riserve_vinc": 0,
            "altre_riserve": 0,
            "contrib_rip": 0,
            "utili_portati": utili_portati,
            "risultato_es": risultato_es,
            "tot_pn": patrimonio_netto,
            "fondi_rischi": fondi_rischi,
            "tfr": tfr,
            "debiti": debiti
        }

    # -------------------------------
    # FUNZIONE FORMATTA EURO
    # -------------------------------
    def euro(x):
        if x < 0:
            return f"-€ {abs(x):,.0f}".replace(",", ".")
        return f"€ {x:,.0f}".replace(",", ".")

    # -------------------------------
    # COSTRUZIONE HTML
    # -------------------------------

    def header():
        h = "<tr><th>VOCI</th>"
        for a in anni:
            h += f"<th>ANNO {a}</th>"
        h += "</tr>"
        return h

    def riga(label, key, bold=False):
        if bold:
            label = f"<b>{label}</b>"
        row = f"<tr><td>{label}</td>"
        for a in anni:
            row += f"<td style='text-align:right'>{euro(sp[a][key])}</td>"
        row += "</tr>"
        return row

    html = f"""
    <style>
    table.sp {{
        width: 100%;
        border-collapse: collapse;
        font-size: 14px;
        margin-bottom: 40px;
    }}
    table.sp th {{
        background-color: #e1e8f7;
        padding: 6px;
        text-align: center;
    }}
    table.sp td {{
        padding: 6px;
        border-bottom: 1px solid #ddd;
    }}
    .section {{
        background-color: #f2f5fc;
        font-weight: bold;
    }}
    </style>

    <h3>STATO PATRIMONIALE ATTIVO</h3>
    <table class="sp">
    {header()}
    <tr class="section"><td colspan="{1+len(anni)}">A) IMMOBILIZZAZIONI</td></tr>
    {riga("I Immobilizzazioni immateriali", "imm_immateriali")}
    {riga("II Immobilizzazioni materiali", "imm_materiali")}
    {riga("III Immobilizzazioni finanziarie", "imm_fin")}
    {riga("Totale A) Immobilizzazioni", "tot_imm", True)}

    <tr class="section"><td colspan="{1+len(anni)}">B) ATTIVO CIRCOLANTE</td></tr>
    {riga("I Rimanenze", "rimanenze")}
    {riga("II Crediti", "crediti")}
    {riga("III Attività finanziarie non immobilizzate", "att_fin_non_imm")}
    {riga("IV Disponibilità liquide", "liquidita")}
    {riga("Totale B) Attivo circolante", "tot_circ", True)}

    {riga("TOTALE ATTIVO (A+B)", "tot_attivo", True)}
    </table>

    <h3>STATO PATRIMONIALE PASSIVO</h3>
    <table class="sp">
    {header()}
    <tr class="section"><td colspan="{1+len(anni)}">A) PATRIMONIO NETTO</td></tr>
    {riga("I Fondo di dotazione", "fondo")}
    {riga("II Finanziamenti per investimenti", "fin_invest")}
    {riga("III Riserve vincolate", "riserve_vinc")}
    {riga("IV Altre riserve", "altre_riserve")}
    {riga("V Contributi ripiano perdite", "contrib_rip")}
    {riga("VI Utili (perdite) portati a nuovo", "utili_portati")}
    {riga("VII Risultato esercizio", "risultato_es")}
    {riga("Totale A) Patrimonio netto", "tot_pn", True)}

    {riga("B) FONDI PER RISCHI E ONERI", "fondi_rischi")}
    {riga("C) TRATTAMENTO FINE RAPPORTO", "tfr")}
    {riga("D) DEBITI", "debiti")}

    {riga("TOTALE PASSIVO", "tot_attivo", True)}
    </table>
    """

    components.html(html, height=1200, scrolling=True)




#------------------------------------------#
####------RENDICONTO FINANZIARIO
#------------------------------------------#


with tab6:

    st.subheader("Rendiconto Finanziario")

    anni = years
    fondo_progressivo = [200000, 120000, 90000, 60000, 30000]

    risultati = df_summary["Risultato netto (€)"].values

    rf = {}
    liquidita_precedente = 0

    for i, anno in enumerate(anni):

        # ===============================
        # 1) GESTIONE CARATTERISTICA
        # ===============================

        risultato_operativo = risultati[i]

        ammortamenti = (
            df_costs.at[i, "Ammortamenti arredi (€/anno)"] +
            df_costs.at[i, "Ammort. attrezzature (€/anno)"]
        )

        flusso_gestione_caratt = risultato_operativo + ammortamenti

        # ===============================
        # 2) GESTIONI NON OPERATIVE
        # ===============================

        gestione_finanziaria = 0
        gestione_straordinaria = 0
        gestione_fiscale = 0

        flusso_potenziale_ccn = (
            flusso_gestione_caratt +
            gestione_finanziaria +
            gestione_straordinaria +
            gestione_fiscale
        )

        # ===============================
        # 3) VARIAZIONI CCN
        # ===============================

        rimanenze = 2000 + i * 1000
        crediti = df_summary.at[i, "Ricavi (€)"] * 0.2

        if i == 0:
            var_rimanenze = -rimanenze
            var_crediti = -crediti
        else:
            rimanenze_prev = 2000 + (i - 1) * 1000
            crediti_prev = df_summary.at[i - 1, "Ricavi (€)"] * 0.2

            var_rimanenze = -(rimanenze - rimanenze_prev)
            var_crediti = -(crediti - crediti_prev)

        var_altri_crediti = 0
        var_att_fin = 0
        var_ratei_att = 0

        var_debiti_commerciali = 0
        var_debiti_diversi = 0
        var_ratei_passivi = 0

        flusso_gestione_reddituale = (
            flusso_potenziale_ccn +
            var_rimanenze +
            var_crediti +
            var_altri_crediti +
            var_att_fin +
            var_ratei_att +
            var_debiti_commerciali +
            var_debiti_diversi +
            var_ratei_passivi
        )

        # ===============================
        # 4) INVESTIMENTI
        # ===============================

        var_imm_immateriali = -5000 if i > 0 else -30000
        var_imm_materiali = -df_costs.at[i, "Ammortamenti arredi (€/anno)"] * 5
        var_imm_finanziarie = 0

        flusso_investimenti = (
            var_imm_immateriali +
            var_imm_materiali +
            var_imm_finanziarie
        )

        # ===============================
        # 5) FINANZIAMENTI
        # ===============================

        var_debiti_fin = 0

        tfr = df_personale.at[i, "Totale costi personale (€)"] * 0.07
        if i == 0:
            var_tfr = tfr
        else:
            tfr_prev = df_personale.at[i - 1, "Totale costi personale (€)"] * 0.07
            var_tfr = tfr - tfr_prev

        var_debiti_lp = 0
        var_debiti_div = 0
        var_fondo_rischi = 1000
        var_patrimonio_netto = fondo_progressivo[i]

        flusso_finanziamenti = (
            var_debiti_fin +
            var_tfr +
            var_debiti_lp +
            var_debiti_div +
            var_fondo_rischi +
            var_patrimonio_netto
        )

        # ===============================
        # 6) FLUSSO NETTO
        # ===============================

        flusso_netto = (
            flusso_gestione_reddituale +
            flusso_investimenti +
            flusso_finanziamenti
        )

        liquidita_finale = liquidita_precedente + flusso_netto

        rf[anno] = {
            "risultato_operativo": risultato_operativo,
            "ammortamenti": ammortamenti,
            "flusso_gestione_caratt": flusso_gestione_caratt,
            "gestione_fin": gestione_finanziaria,
            "gestione_str": gestione_straordinaria,
            "gestione_fisc": gestione_fiscale,
            "flusso_pot_ccn": flusso_potenziale_ccn,
            "var_rimanenze": var_rimanenze,
            "var_crediti": var_crediti,
            "flusso_gestione_redd": flusso_gestione_reddituale,
            "var_imm_imm": var_imm_immateriali,
            "var_imm_mat": var_imm_materiali,
            "var_imm_fin": var_imm_finanziarie,
            "var_tfr": var_tfr,
            "var_pn": var_patrimonio_netto,
            "flusso_netto": flusso_netto,
            "liq_inizio": liquidita_precedente,
            "liq_fine": liquidita_finale
        }

        liquidita_precedente = liquidita_finale

    # ===============================
    # FUNZIONE EURO
    # ===============================

    def euro(x):
        if x < 0:
            return f"-€ {abs(x):,.0f}".replace(",", ".")
        return f"€ {x:,.0f}".replace(",", ".")

    # ===============================
    # COSTRUZIONE TABELLA HTML
    # ===============================

    def header():
        h = "<tr><th>VOCI</th>"
        for a in anni:
            h += f"<th>ANNO {a}</th>"
        h += "</tr>"
        return h

    def riga(label, key, bold=False):
        if bold:
            label = f"<b>{label}</b>"
        row = f"<tr><td>{label}</td>"
        for a in anni:
            row += f"<td style='text-align:right'>{euro(rf[a][key])}</td>"
        row += "</tr>"
        return row

    html = f"""
    <style>
    table.rf {{
        width: 100%;
        border-collapse: collapse;
        font-size: 14px;
    }}
    table.rf th {{
        background-color: #e1e8f7;
        padding: 6px;
        text-align: center;
    }}
    table.rf td {{
        padding: 6px;
        border-bottom: 1px solid #ddd;
    }}
    .section {{
        background-color: #f2f5fc;
        font-weight: bold;
    }}
    </style>

    <table class="rf">
    {header()}

    <tr class="section"><td colspan="{1+len(anni)}">GESTIONE CARATTERISTICA</td></tr>
    {riga("Risultato operativo", "risultato_operativo")}
    {riga("Ammortamenti e accantonamenti", "ammortamenti")}
    {riga("FLUSSO DI CASSA DELLA GESTIONE CARATTERISTICA", "flusso_gestione_caratt", True)}

    <tr class="section"><td colspan="{1+len(anni)}">GESTIONE REDDITUALE</td></tr>
    {riga("FLUSSO POTENZIALE DI CCN", "flusso_pot_ccn", True)}
    {riga("Variazione Rimanenze", "var_rimanenze")}
    {riga("Variazione Crediti commerciali", "var_crediti")}
    {riga("FLUSSO DI CASSA DELLA GESTIONE REDDITUALE", "flusso_gestione_redd", True)}

    <tr class="section"><td colspan="{1+len(anni)}">INVESTIMENTI</td></tr>
    {riga("Variazione Immobilizzazioni immateriali", "var_imm_imm")}
    {riga("Variazione Immobilizzazioni materiali", "var_imm_mat")}
    {riga("Variazione Immobilizzazioni finanziarie", "var_imm_fin")}

    <tr class="section"><td colspan="{1+len(anni)}">FINANZIAMENTI</td></tr>
    {riga("Variazione Fondo TFR", "var_tfr")}
    {riga("Variazione Patrimonio Netto", "var_pn")}

    <tr class="section"><td colspan="{1+len(anni)}">SINTESI</td></tr>
    {riga("FLUSSO DI CASSA NETTO AZIENDALE", "flusso_netto", True)}
    {riga("Liquidità netta di inizio anno", "liq_inizio")}
    {riga("LIQUIDITA' NETTA DI FINE ANNO", "liq_fine", True)}

    </table>
    """

    components.html(html, height=1300, scrolling=True)
