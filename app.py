import streamlit as st
import pandas as pd

st.set_page_config(page_title="Bolão da Copa 2026", layout="wide")

st.title("⚽ Bolão da Copa 2026")
st.subheader("Preencha seus palpites:")

# Carrega os jogos
df = pd.read_csv("jogos_copa.csv")

# O st.data_editor cria a tabela editável
# O usuário pode clicar nas colunas de palpite e digitar
df_editado = st.data_editor(df, use_container_width=True)

# Botão para salvar
if st.button("Salvar meus palpites"):
    # Aqui você pode salvar em um CSV ou enviar para um banco de dados
    df_editado.to_csv("meus_palpites.csv", index=False)
    st.success("Palpites salvos com sucesso!")