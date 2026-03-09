        # Localiza os itens do grid de estatísticas
        itens = soup.select(".grid-item")
        
        for index, item in enumerate(itens):
            texto_total = item.get_text(separator=" ").upper()
            valor = limpar_porcentagem(texto_total)

            # 1ª Tentativa: Pelo texto direto
            if "OVER 1.5" in texto_total:
                res["o15"] = valor
            elif "OVER 2.5" in texto_total:
                res["o25"] = valor
            elif "BTTS" in texto_total:
                res["btts"] = valor
            
            # 2ª Tentativa (Backup): Se o texto falhou mas é a PRIMEIRA caixa do grid
            elif index == 0 and res["o15"] == "0%":
                res["o15"] = valor
            
            # Lógica das Clean Sheets (continua igual)
            elif "CLEAN SHEETS" in texto_total:
                sub_texto = item.select_one(".stat-text").get_text().upper() if item.select_one(".stat-text") else ""
                if "LAZIO" in sub_texto or "LAZIO" in texto_total:
                    res["cs_home"] = valor
                elif "SASSUOLO" in sub_texto or "SASSUOLO" in texto_total:
                    res["cs_away"] = valor
                    
