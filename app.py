import streamlit as st
import pandas as pd
from supabase import create_client, Client
from PIL import Image
import io
import base64

# --- CONFIGURAÇÃO DA PÁGINA (DESIGN SISTÊMICO) ---
st.set_page_config(
    page_title="Celestia Ops - Conveniência", 
    page_icon="🏪", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- INJEÇÃO DE UI/UX PREMIUM (CSS CUSTOMIZADO) ---
st.markdown("""
<style>
    /* Estilização Geral do Fundo e Cores Globais */
    .stApp {
        background-color: #0d1117;
        color: #c9d1d9;
    }
    
    /* Customização do Menu Lateral (Sidebar) */
    section[data-testid="stSidebar"] {
        background-color: #161b22 !important;
        border-right: 1px solid #30363d;
    }
    
    /* Títulos e Textos Grandes */
    h1, h2, h3 {
        color: #ffffff !important;
        font-family: 'Inter', sans-serif;
        font-weight: 700 !important;
        letter-spacing: -0.5px;
    }
    
    /* Estilização de Botões Principais */
    div.stButton > button:first-child {
        background: linear-gradient(135deg, #1f6feb 0%, #0d4ba1 100%);
        color: white;
        border: none;
        padding: 0.6rem 1.5rem;
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.2s ease-in-out;
        width: 100%;
        box-shadow: 0 4px 12px rgba(31, 111, 235, 0.2);
    }
    div.stButton > button:first-child:hover {
        background: linear-gradient(135deg, #388bfd 0%, #1f6feb 100%);
        transform: translateY(-1px);
        box-shadow: 0 6px 16px rgba(31, 111, 235, 0.3);
    }
    
    /* Estilização de Botões Críticos / Cancelar */
    div.stButton > button[data-testid="baseButton-primary"] {
        background: linear-gradient(135deg, #da3633 0%, #891a1c 100%) !important;
        box-shadow: 0 4px 12px rgba(218, 54, 51, 0.2) !important;
    }
    div.stButton > button[data-testid="baseButton-primary"]:hover {
        background: linear-gradient(135deg, #f85149 0%, #da3633 100%) !important;
    }

    /* Custom Cards para Faturamento e Métricas */
    .metric-card {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 1.5rem;
        text-align: center;
        box-shadow: 0 4px 20px rgba(0,0,0,0.15);
    }
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
        color: #58a6ff;
        margin-top: 0.5rem;
    }
    .metric-title {
        font-size: 0.9rem;
        color: #8b949e;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    /* Inputs e Tabelas */
    .stTextInput input, .stNumberInput input, .stSelectbox div {
        background-color: #21262d !important;
        color: white !important;
        border: 1px solid #30363d !important;
        border-radius: 8px !important;
    }
    
    /* Alinhamento de Linhas Divisórias */
    hr {
        border-color: #30363d !important;
    }
</style>
""", unsafe_allow_html=True)

# --- CONEXÃO COM O SUPABASE ---
SUPABASE_URL = st.secrets.get("SUPABASE_URL", "SUA_URL_DO_SUPABASE_AQUI")
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "SUA_ANON_KEY_DO_SUPABASE_AQUI")

@st.cache_resource
def init_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

supabase: Client = init_supabase()

# --- FUNÇÕES AUXILIARES ---
def image_to_base64(uploaded_file):
    if uploaded_file is not None:
        bytes_data = uploaded_file.getvalue()
        return base64.b64encode(bytes_data).decode("utf-8")
    return None

def base64_to_image(base64_string):
    if base64_string:
        img_data = base64.b64decode(base64_string)
        return Image.open(io.BytesIO(img_data))
    return None

# --- BRANDING DO MENU LATERAL ---
st.sidebar.markdown("<h2 style='text-align: center; color: #58a6ff !important;'>🏪 CONVENIÊNCIA HUB</h2>", unsafe_allow_html=True)
st.sidebar.markdown("<p style='text-align: center; color: #8b949e; margin-bottom: 2rem;'>Core Engine v2.0</p>", unsafe_allow_html=True)
menu = st.sidebar.radio("Navegação Estruturada:", ["🛒 Operação de Caixa (PDV)", "📦 Controle de Estoque", "📊 Inteligência de Negócio"])

# ---------------------------------------------------------
# MÓDULO 1: OPERAÇÃO DE CAIXA (PDV)
# ---------------------------------------------------------
if menu == "🛒 Operação de Caixa (PDV)":
    st.title("🛒 Frente de Caixa")
    st.markdown("Interface em tempo real para registro e fechamento de pedidos.")
    st.write("---")
    
    if "carrinho" not in st.session_state:
        st.session_state.carrinho = []

    # Buscar dados atualizados
    resposta = supabase.table("produtos").select("id, nome, preco, quantidade, foto").order("nome").execute()
    produtos_lista = resposta.data
    
    if not produtos_lista:
        st.warning("Aguardando inserção de dados no módulo de Estoque.")
    else:
        df_produtos = pd.DataFrame(produtos_lista)
        
        # Barra de Pesquisa Polida
        pesquisa = st.text_input("🔍 Filtrar Catálogo de Produtos:", placeholder="Digite o nome do produto...").strip().lower()
        
        if pesquisa:
            produtos_filtrados = [row for row in produtos_lista if pesquisa in row['nome'].lower()]
        else:
            produtos_filtrados = produtos_lista

        col1, col2 = st.columns([1.2, 1])
        
        with col1:
            st.markdown("### Seleção de Itens")
            opcoes_produtos = {
                f"📦 {row['nome']} — R$ {row['preco']:.2f} (Qtd Disp: {row['quantidade']})": row['id'] 
                for row in produtos_filtrados if row['quantidade'] > 0
            }
            
            if not opcoes_produtos:
                st.error("Nenhum item correspondente localizado no inventário.")
            else:
                selecionado = st.selectbox("Selecione o produto ativo:", list(opcoes_produtos.keys()))
                id_prod = opcoes_produtos[selecionado]
                
                prod_atual = df_produtos[df_produtos['id'] == id_prod].iloc[0]
                
                # Exibição elegante da foto do produto
                if prod_atual['foto']:
                    st.markdown("<br>", unsafe_allow_html=True)
                    st.image(base64_to_image(prod_atual['foto']), width=180, use_container_width=False)
                    st.markdown("<br>", unsafe_allow_html=True)
                    
                qtd_venda = st.number_input("Definir Quantidade para Checkout:", min_value=1, max_value=int(prod_atual['quantidade']), value=1)
                
                if st.button("➕ Adicionar ao Checkout"):
                    st.session_state.carrinho.append({
                        "id": int(id_prod),
                        "nome": prod_atual['nome'],
                        "preco": float(prod_atual['preco']),
                        "quantidade": int(qtd_venda),
                        "subtotal": float(prod_atual['preco'] * qtd_venda)
                    })
                    st.success(f"{prod_atual['nome']} acoplado ao lote.")
                    st.rerun()

        with col2:
            st.markdown("### Cupom / Resumo do Pedido")
            if st.session_state.carrinho:
                df_car = pd.DataFrame(st.session_state.carrinho)
                st.dataframe(df_car[["nome", "quantidade", "subtotal"]], use_container_width=True, hide_index=True)
                
                total_geral = df_car["subtotal"].sum()
                
                # Caixa de Faturamento Total Customizada
                st.markdown(f"""
                <div class='metric-card' style='margin-bottom: 1.5rem;'>
                    <div class='metric-title'>Valor Total do Pedido</div>
                    <div class='metric-value' style='color: #2ea043;'>R$ {total_geral:.2f}</div>
                </div>
                """, unsafe_allow_html=True)
                
                c_btn1, c_btn2 = st.columns(2)
                with c_btn1:
                    if st.button("✅ Concluir Transação", type="secondary"): # Usa estilo padrão (Azul via CSS)
                        for item in st.session_state.carrinho:
                            res_qtd = supabase.table("produtos").select("quantidade").eq("id", item['id']).execute()
                            qtd_atual_banco = res_qtd.data[0]['formatting_quantity'] if 'formatting_quantity' in res_qtd.data[0] else res_qtd.data[0]['quantidade']
                            nova_qtd = qtd_atual_banco - item['quantidade']
                            
                            supabase.table("produtos").update({"quantidade": nova_qtd}).eq("id", item['id']).execute()
                            
                            supabase.table("vendas").insert({
                                "produto_id": item['id'],
                                "nome_produto": item['nome'],
                                "quantidade": item['quantidade'],
                                "total": item['subtotal']
                            }).execute()
                            
                        st.session_state.carrinho = []
                        st.toast("Transação registrada com sucesso!", icon="⚡")
                        st.rerun()
                with c_btn2:
                    if st.button("🗑️ Estornar Tudo", type="primary"): # Fica vermelho via CSS
                        st.session_state.carrinho = []
                        st.rerun()
            else:
                st.info("Aguardando inserção de itens para iniciar a precificação.")

# ---------------------------------------------------------
# MÓDULO 2: CONTROLE DE ESTOQUE
# ---------------------------------------------------------
elif menu == "📦 Controle de Estoque":
    st.title("📦 Inventário e Cadastro Corporativo")
    st.markdown("Módulo central para gerenciamento de insumos, SKUs e controle de preços.")
    st.write("---")
    
    aba_cad, aba_edita = st.tabs(["🆕 Inserir Novo SKU", "✏️ Atualização de Lote / Remoção"])
    
    with aba_cad:
        st.markdown("### Cadastro de Insumo")
        with st.form("cadastro_premium", clear_on_submit=True):
            col_in1, col_in2 = st.columns(2)
            with col_in1:
                nome = st.text_input("Identificação / Nome do Produto", placeholder="Ex: Energético Monster 473ml")
                preco = st.number_input("Preço Unitário de Venda (R$)", min_value=0.0, format="%.2f", step=0.50)
            with col_in2:
                qtd = st.number_input("Volume Inicial em Estoque", min_value=0, step=1)
                foto = st.file_uploader("Upload de Ativo Visual (Foto)", type=["jpg", "png", "jpeg"])
            
            if st.form_submit_button("Submeter Dados ao Servidor"):
                if nome and preco > 0:
                    foto_b64 = image_to_base64(foto)
                    supabase.table("produtos").insert({
                        "nome": nome,
                        "preco": preco,
                        "quantidade": qtd,
                        "foto": foto_b64
                    }).execute()
                    st.success(f"'{nome}' indexado à nuvem com sucesso.")
                else:
                    st.error("Falha na validação. Certifique-se de preencher o nome e um preço nominal positivo.")
                    
    with aba_edita:
        resposta = supabase.table("produtos").select("id, nome, preco, quantidade").order("nome").execute()
        if resposta.data:
            df_est = pd.DataFrame(resposta.data)
            st.markdown("### Visão Geral do Inventário Ativo")
            st.dataframe(df_est, use_container_width=True, hide_index=True)
            
            st.write("---")
            st.markdown("### Modificação de Registro")
            opcoes_edicao = {row['nome']: row['id'] for row in resposta.data}
            escolhido = st.selectbox("Selecione o item para alteração de metadados:", list(opcoes_edicao.keys()))
            id_edit = opcoes_edicao[escolhido]
            
            item_detalhe = df_est[df_est['id'] == id_edit].iloc[0]
            
            col_ed1, col_ed2 = st.columns(2)
            with col_ed1:
                n_qtd = st.number_input("Ajustar Quantidade Física:", min_value=0, value=int(item_detalhe['quantidade']))
                n_prc = st.number_input("Ajustar Preço de Mercado (R$):", min_value=0.0, value=float(item_detalhe['preco']), format="%.2f")
                if st.button("💾 Persistir Alterações"):
                    supabase.table("produtos").update({"quantidade": n_qtd, "preco": n_prc}).eq("id", id_edit).execute()
                    st.success("Alterações salvas com sucesso.")
                    st.rerun()
            with col_ed2:
                st.markdown("<p style='color: #da3633; font-weight: bold;'>Remoção de Registro</p>", unsafe_allow_html=True)
                if st.button("❌ Expurgar Produto do Inventário", type="primary"):
                    supabase.table("produtos").delete().eq("id", id_edit).execute()
                    st.error("Registro removido da base de dados central.")
                    st.rerun()

# ---------------------------------------------------------
# MÓDULO 3: INTELIGÊNCIA DE NEGÓCIO
# ---------------------------------------------------------
elif menu == "📊 Inteligência de Negócio":
    st.title("📊 Painel Analítico & Auditoria")
    st.markdown("Faturamento consolidado e métricas analíticas de saída em tempo real.")
    st.write("---")
    
    res_vendas = supabase.table("vendas").select("id, nome_produto, quantidade, total, data").order("id", desc=True).execute()
    
    if not res_vendas.data:
        st.info("Aguardando computação de vendas para gerar volumetria gráfica.")
    else:
        df_vendas = pd.DataFrame(res_vendas.data)
        df_vendas['data'] = pd.to_datetime(df_vendas['data']).dt.strftime('%d/%m/%Y %H:%M')
        
        faturamento = df_vendas["total"].sum()
        itens_saida = df_vendas["quantidade"].sum()
        
        # Grid de Métricas Avançadas usando HTML/CSS Customizado
        st.markdown(f"""
        <div style="display: flex; gap: 20px; margin-bottom: 25px;">
            <div class="metric-card" style="flex: 1;">
                <div class="metric-title">Faturamento Bruto Consolidado</div>
                <div class="metric-value">R$ {faturamento:.2f}</div>
            </div>
            <div class="metric-card" style="flex: 1;">
                <div class="metric-title">Volume de Escoamento (Itens)</div>
                <div class="metric-value" style="color: #ffca28;">{int(itens_saida)} Unid.</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.write("---")
        
        col_graf1, col_graf2 = st.columns([1.5, 1])
        
        with col_graf1:
            st.markdown("### Performance de Escoamento por SKU")
            grafico_dados = df_vendas.groupby("nome_produto")["quantidade"].sum().reset_index()
            # Gráfico integrado nativo que respeita o tema dark implicitamente
            st.bar_chart(data=grafico_dados, x="nome_produto", y="quantidade", color="#58a6ff")
            
        with col_graf2:
            st.markdown("### Auditoria de Transações (Logs)")
            st.dataframe(df_vendas[["data", "nome_produto", "total"]], use_container_width=True, hide_index=True)
