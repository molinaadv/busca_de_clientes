    export_df = out.drop(columns=["_NOME_NORM", "_CPF_NORM"], errors="ignore").copy()
    display_df = export_df.copy()

    # ===============================
    # SENHA DO INSS (resultado da busca)
    # ===============================
    col_senha_inss = "SENHA INSS"  # nome exato da coluna na planilha
    senha_inss_valor = "—"
    if col_senha_inss in export_df.columns and len(export_df) > 0:
        senha_inss_valor = str(export_df.iloc[0][col_senha_inss])

    # Mascara CPF na tela (independente de ter Senha INSS)
    if (not show_sensitive) and (cpf_col in display_df.columns):
        def mask(val):
            d = norm_cpf(val)
            if len(d) == 11:
                return f"{d[:3]}.***.***-{d[-2:]}"
            return "***"
        display_df[cpf_col] = display_df[cpf_col].apply(mask)

    st.markdown("<hr/>", unsafe_allow_html=True)

    # KPIs (ordem: base, senha INSS, resultados, filtros)
    k1, k2, k3, k4 = st.columns(4)

    with k1:
        kpi_card("Registros na base", f"{len(df):,}".replace(",", "."), "Total no Excel")

    with k2:
        kpi_card("Senha do INSS", senha_inss_valor, "Campo: SENHA INSS")

    with k3:
        kpi_card("Resultados", f"{len(display_df):,}".replace(",", "."), "Após filtros")

    with k4:
        kpi_card("Filtros usados", ", ".join(filters_used) if filters_used else "Nenhum", "Critérios de busca")

    st.markdown("<hr/>", unsafe_allow_html=True)
    st.markdown('<div class="mlp-section-title">Resultados</div>', unsafe_allow_html=True)
    st.dataframe(display_df.head(int(limit)), use_container_width=True, height=520)

    st.download_button(
        "⬇️ Baixar Excel (resultado filtrado)",
        data=to_excel_bytes(export_df),
        file_name="resultado_busca_clientes.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


except Exception as e:
    st.error(f"Erro ao ler a base do Excel: {e}")
