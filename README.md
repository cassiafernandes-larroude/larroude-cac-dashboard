# Larroude — Dashboard CAC por Produto (BR)

Dashboard interativo de **CAC por produto por dia** para Larroude Brasil, com dois rankings paralelos: top 15 por volume e top 15 com menor CAC.

🔗 **Link público:** publicado via GitHub Pages — ver aba Pages do repo.

## Pipeline

| Passo | Script | O que faz |
|-------|--------|-----------|
| 1 | `1_fetch_shopify.py` | Pedidos Shopify BR, 28D, via Admin GraphQL |
| 2 | `2_fetch_meta_spend.py` | Spend diário das 3 contas Meta BR via Graph API |
| 3 | `3_compute_cac.py` | Top 15 volume + top 15 menor CAC, alocação proporcional |
| 4 | `4_build_dashboard.py` | Gera `dashboard_cac_br.html` self-contained |

Orquestrador: `run_daily.py` (executa os 4 em sequência).

## Metodologia

- **CAC** = (spend alocado ao produto) ÷ (novos clientes)
- **Spend alocado**: total diário Meta BR distribuído entre todos os produtos pela fatia de receita do dia (USD→BRL via taxa fixa 5,10).
- **Novo cliente**: pedido onde `customer.numberOfOrders == 1`.
- **Filtro tabela B**: produtos com ≥ 20 novos clientes em 28D (anti-ruído).

## Atualização

Local: scheduled task `cac-by-product-daily-refresh` (todo dia 09h BRT).

## Credenciais

Lidas de `C:/Projects/.env` (não commitado):
- `SHOPIFY_BR_ADMIN_API_TOKEN`
- `META_ACCESS_TOKEN`
