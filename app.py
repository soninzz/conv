import streamlit as st
import pandas as pd
from supabase import create_client, Client
from PIL import Image
import io
import base64

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Conveniência Hub", page_icon="🏪", layout="wide")

# --- CONEXÃO COM O SUPABASE ---
# Para rodar local, você pode substituir pelas suas strings direto.
# Quando for para o Streamlit Cloud, use o st.secrets para segurança!
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

# --- MENU LATERAL ---
st.sidebar.title("🏪 Conveniência")
menu = st.sidebar.radio("Navegação:", ["🛒 Frente de Caixa (PDV)", "📦 Estoque & Produtos", "📊 Relatórios de Vendas"])

# ---------------------------------------------------------
# MÓDULO 1: FRENTE DE CAIXA (PDV)
# ---------------------------------------------------------
if menu == "🛒 Frente de Caixa (PDV)":
    st.header("🛒 Frente de Caixa (PDV)")
    
    if "carrinho" not in st.session_state:
        st.session_state.carrinho = []

    # Buscar produtos do Supabase
    resposta = supabase.table("produtos").select("id, nome, preco, quantidade, foto").order("nome").execute()
    produtos_lista = resposta.data
    
    if not produtos_lista:
        st.warning("Nenhum produto cadastrado no estoque ainda.")
    else:
        df_produtos = pd.DataFrame(produtos_lista)
        
        # --- NOVO: BARRA DE PESQUISA REAL-TIME ---
        pesquisa = st.text_input("🔍 Pesquisar produto pelo nome:", "").strip().lower()
        
        # Filtrar a lista com base no que foi digitado
        if pesquisa:
            produtos_filtrados = [row for row in produtos_lista if pesquisa in row['nome'].lower()]
        else:
            produtos_filtrados = produtos_lista

        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("Adicionar Produto")
            
            # Montar as opções apenas com os produtos que passaram no filtro e têm estoque
            opcoes_produtos = {
                f"{row['nome']} (R$ {row['preco']:.2f}) - Estoque: {row['quantidade']}": row['id'] 
                for row in produtos_filtrados if row['quantidade'] > 0
            }
            
            if not opcoes_produtos:
                if pesquisa:
                    st.error("Nenhum produto encontrado com esse nome ou sem estoque!")
                else:
                    st.error("Todos os produtos cadastrados estão com estoque zerado!")
            else:
                selecionado = st.selectbox("Escolha o Item", list(opcoes_produtos.keys()))
                id_prod = opcoes_produtos[selecionado]
                
                prod_atual = df_produtos[df_produtos['id'] == id_prod].iloc[0]
                
                if prod_atual['foto']:
                    st.image(base64_to_image(prod_atual['foto']), width=130)
                    
                qtd_venda = st.number_input("Quantidade", min_value=1, max_value=int(prod_atual['quantidade']), value=1)
                
                if st.button("➕ Adicionar"):
                    st.session_state.carrinho.append({
                        "id": int(id_prod),
                        "nome": prod_atual['nome'],
                        "preco": float(prod_atual['preco']),
                        "quantidade": int(qtd_venda),
                        "subtotal": float(prod_atual['preco'] * qtd_venda)
                    })
                    st.success(f"{prod_atual['nome']} adicionado ao carrinho.")
                    st.rerun()

        with col2:
            st.subheader("Carrinho Atual")
            if st.session_state.carrinho:
                df_car = pd.DataFrame(st.session_state.carrinho)
                st.dataframe(df_car[["nome", "quantidade", "subtotal"]], use_container_width=True)
                
                total_geral = df_car["subtotal"].sum()
                st.markdown(f"### **Total: R$ {total_geral:.2f}**")
                
                c_btn1, c_btn2 = st.columns(2)
                with c_btn1:
                    if st.button("✅ Confirmar Venda", type="primary"):
                        for item in st.session_state.carrinho:
                            res_qtd = supabase.table("produtos").select("quantidade").eq("id", item['id']).execute()
                            qtd_atual_banco = res_qtd.data[0]['quantidade']
                            nova_qtd = qtd_atual_banco - item['quantidade']
                            
                            supabase.table("produtos").update({"quantidade": nova_qtd}).eq("id", item['id']).execute()
                            
                            supabase.table("vendas").insert({
                                "produto_id": item['id'],
                                "nome_produto": item['nome'],
                                "quantidade": item['quantidade'],
                                "total": item['subtotal']
                            }).execute()
                            
                        st.session_state.carrinho = []
                        st.success("Venda processada com sucesso!")
                        st.rerun()
                with c_btn2:
                    if st.button("🗑️ Cancelar"):
                        st.session_state.carrinho = []
                        st.rerun()
            else:
                st.info("Aguardando produtos.")
# ---------------------------------------------------------
# MÓDULO 2: ESTOQUE & PRODUTOS
# ---------------------------------------------------------
elif menu == "📦 Estoque & Produtos":
    st.header("📦 Gerenciamento de Estoque (Nuvem)")
    
    aba_cad, aba_edita = st.tabs(["🆕 Novo Produto", "✏️ Atualizar / Remover"])
    
    with aba_cad:
        with st.form("cadastro_supabase", clear_on_submit=True):
            nome = st.text_input("Nome do Produto")
            preco = st.number_input("Preço (R$)", min_value=0.0, format="%.2f", step=0.50)
            qtd = st.number_input("Estoque Inicial", min_value=0, step=1)
            foto = st.file_uploader("Enviar Foto", type=["jpg", "png", "jpeg"])
            
            if st.form_submit_button("Cadastrar no Banco"):
                if nome and preco > 0:
                    foto_b64 = image_to_base64(foto)
                    supabase.table("produtos").insert({
                        "nome": nome,
                        "preco": preco,
                        "quantidade": qtd,
                        "foto": foto_b64
                    }).execute()
                    st.success(f"'{nome}' salvo com sucesso!")
                else:
                    st.error("Preencha os campos obrigatórios.")
                    
    with aba_edita:
        resposta = supabase.table("produtos").select("id, nome, preco, quantidade").order("nome").execute()
        if resposta.data:
            df_est = pd.DataFrame(resposta.data)
            st.dataframe(df_est, use_container_width=True, hide_index=True)
            
            st.write("---")
            opcoes_edicao = {row['nome']: row['id'] for row in resposta.data}
            escolhido = st.selectbox("Selecione o produto para modificar", list(opcoes_edicao.keys()))
            id_edit = opcoes_edicao[escolhido]
            
            # Detalhes do item selecionado
            item_detalhe = df_est[df_est['id'] == id_edit].iloc[0]
            
            col_ed1, col_ed2 = st.columns(2)
            with col_ed1:
                n_qtd = st.number_input("Atualizar Estoque", min_value=0, value=int(item_detalhe['quantidade']))
                n_prc = st.number_input("Atualizar Preço", min_value=0.0, value=float(item_detalhe['preco']), format="%.2f")
                if st.button("💾 Confirmar Alterações"):
                    supabase.table("produtos").update({"quantidade": n_qtd, "preco": n_prc}).eq("id", id_edit).execute()
                    st.success("Dados atualizados!")
                    st.rerun()
            with col_ed2:
                st.write("Zona de Perigo")
                if st.button("❌ Apagar Produto Permanentemente", type="primary"):
                    supabase.table("produtos").delete().eq("id", id_edit).execute()
                    st.error("Produto deletado.")
                    st.rerun()

# ---------------------------------------------------------
# MÓDULO 3: RELATÓRIOS DE VENDAS
# ---------------------------------------------------------
elif menu == "📊 Relatórios de Vendas":
    st.header("📊 Histórico de Vendas Real-Time")
    
    res_vendas = supabase.table("vendas").select("id, nome_produto, quantidade, total, data").order("id", desc=True).execute()
    
    if not res_vendas.data:
        st.info("Nenhuma venda computada até o momento.")
    else:
        df_vendas = pd.DataFrame(res_vendas.data)
        
        # Formatando a coluna de data para melhor leitura
        df_vendas['data'] = pd.to_datetime(df_vendas['data']).dt.strftime('%d/%m/%Y %H:%M')
        
        faturamento = df_vendas["total"].sum()
        itens_saida = df_vendas["quantidade"].sum()
        
        c1, c2 = st.columns(2)
        c1.metric("💵 Faturamento Total", f"R$ {faturamento:.2f}")
        c2.metric("📦 Volume de Vendas (Itens)", int(itens_saida))
        
        st.write("---")
        st.subheader("Gráfico de Demanda")
        grafico_dados = df_vendas.groupby("nome_produto")["quantidade"].sum().reset_index()
        st.bar_chart(data=grafico_dados, x="nome_produto", y="quantidade")
        
        st.subheader("Fitas de Caixa Eletrônicas")
        st.dataframe(df_vendas, use_container_width=True, hide_index=True)
