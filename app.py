import streamlit as st
from datetime import datetime
import base64
from io import BytesIO
from PIL import Image
import pandas as pd

try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    st.error("⚠️ Supabase n'est pas installé. Utilisez: pip install supabase")

# Configuration de la page
st.set_page_config(
    page_title="PixelMarket - Stock Photos & Graphics",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==================== CONFIGURATION SUPABASE ====================
# Vos clés Supabase

SUPABASE_URL = "https://majdvgokkvwjvtuqhncd.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1hamR2Z29ra3Z3anZ0dXFobmNkIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2NzkwNjk1NywiZXhwIjoyMDgzNDgyOTU3fQ.8f_lDQEnllRaCDJsoZrR0n6uoBS-AquRJxWwgHSW4Uw"

# Initialiser Supabase
@st.cache_resource
def init_supabase():
    if not SUPABASE_AVAILABLE:
        return None
    try:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        st.error(f"Erreur connexion Supabase: {e}")
        return None

supabase = init_supabase()

# ==================== SESSION STATE ====================

if 'username' not in st.session_state:
    st.session_state.username = f"user_{datetime.now().timestamp()}"
if 'is_admin' not in st.session_state:
    st.session_state.is_admin = False
if 'dark_mode' not in st.session_state:
    st.session_state.dark_mode = False
if 'search_query' not in st.session_state:
    st.session_state.search_query = ""
if 'selected_category' not in st.session_state:
    st.session_state.selected_category = "Tous"
if 'selected_type' not in st.session_state:
    st.session_state.selected_type = "Tous"
if 'show_premium_only' not in st.session_state:
    st.session_state.show_premium_only = False

# CSS personnalisé
if st.session_state.dark_mode:
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        * { font-family: 'Inter', sans-serif; }
        .main { background: #0a0e27; }
        .hero-section {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 60px 20px;
            border-radius: 20px;
            text-align: center;
            margin-bottom: 40px;
        }
        .hero-title { font-size: 48px; font-weight: 700; color: white; margin-bottom: 20px; }
        .hero-subtitle { font-size: 20px; color: rgba(255,255,255,0.9); margin-bottom: 30px; }
        .photo-grid-item {
            background: rgba(255,255,255,0.05);
            border-radius: 12px;
            overflow: hidden;
            transition: all 0.3s;
            cursor: pointer;
            border: 1px solid rgba(255,255,255,0.1);
        }
        .photo-grid-item:hover { transform: translateY(-8px); box-shadow: 0 20px 40px rgba(102,126,234,0.3); }
        .premium-badge {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600;
        }
        .free-badge { background: #10b981; color: white; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; }
        h1, h2, h3, p { color: white !important; }
    </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        * { font-family: 'Inter', sans-serif; }
        .main { background: #f8f9fa; }
        .hero-section {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 60px 20px;
            border-radius: 20px;
            text-align: center;
            margin-bottom: 40px;
        }
        .hero-title { font-size: 48px; font-weight: 700; color: white; margin-bottom: 20px; }
        .hero-subtitle { font-size: 20px; color: rgba(255,255,255,0.9); margin-bottom: 30px; }
        .photo-grid-item {
            background: white;
            border-radius: 12px;
            overflow: hidden;
            transition: all 0.3s;
            cursor: pointer;
            border: 1px solid #e5e7eb;
        }
        .photo-grid-item:hover { transform: translateY(-8px); box-shadow: 0 20px 40px rgba(0,0,0,0.1); }
        .premium-badge {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600;
        }
        .free-badge { background: #10b981; color: white; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; }
        h1, h2, h3 { color: #1f2937 !important; }
        p { color: #4b5563 !important; }
    </style>
    """, unsafe_allow_html=True)

# ==================== FONCTIONS SUPABASE ====================

def get_user_id(username):
    if not supabase:
        return 1
    try:
        # Vérifier si l'utilisateur existe
        result = supabase.table('users').select('id').eq('username', username).execute()
        
        if result.data:
            return result.data[0]['id']
        else:
            # Créer nouvel utilisateur
            new_user = supabase.table('users').insert({'username': username}).execute()
            return new_user.data[0]['id']
    except Exception as e:
        st.error(f"Erreur utilisateur: {e}")
        return 1

def add_asset(title, author, author_id, description, category, asset_type, is_premium, price, image_base64, tags):
    try:
        data = {
            'title': title,
            'author': author,
            'author_id': author_id,
            'description': description,
            'category': category,
            'asset_type': asset_type,
            'is_premium': is_premium,
            'price': float(price),
            'image_url': image_base64,  # En production, utilisez Supabase Storage
            'tags': tags
        }
        supabase.table('assets').insert(data).execute()
        return True
    except Exception as e:
        st.error(f"Erreur ajout asset: {e}")
        return False

def get_all_assets(search="", category="Tous", asset_type="Tous", premium_only=False):
    try:
        query = supabase.table('assets').select('*')
        
        # Filtres
        if category != "Tous":
            query = query.eq('category', category)
        
        if asset_type != "Tous":
            query = query.eq('asset_type', asset_type)
        
        if premium_only:
            query = query.eq('is_premium', True)
        
        # Recherche textuelle
        if search:
            query = query.or_(f'title.ilike.%{search}%,author.ilike.%{search}%,tags.ilike.%{search}%')
        
        # Trier par date
        query = query.order('upload_date', desc=True)
        
        result = query.execute()
        return result.data
    except Exception as e:
        st.error(f"Erreur chargement assets: {e}")
        return []

def download_asset(user_id, asset_id):
    try:
        # Enregistrer le téléchargement
        supabase.table('downloads').insert({
            'user_id': user_id,
            'asset_id': asset_id
        }).execute()
        
        # Le trigger SQL incrémente automatiquement le compteur
        return True
    except Exception as e:
        st.error(f"Erreur téléchargement: {e}")
        return False

def increment_views(asset_id):
    try:
        # Récupérer les vues actuelles
        result = supabase.table('assets').select('views').eq('id', asset_id).execute()
        current_views = result.data[0]['views'] if result.data else 0
        
        # Incrémenter
        supabase.table('assets').update({'views': current_views + 1}).eq('id', asset_id).execute()
    except Exception as e:
        pass

def get_stats():
    try:
        # Total assets
        total = supabase.table('assets').select('id', count='exact').execute()
        total_assets = total.count
        
        # Assets gratuits
        free = supabase.table('assets').select('id', count='exact').eq('is_premium', False).execute()
        free_assets = free.count
        
        # Total téléchargements
        downloads = supabase.table('downloads').select('id', count='exact').execute()
        total_downloads = downloads.count
        
        # Utilisateurs actifs
        users = supabase.table('users').select('id', count='exact').execute()
        active_users = users.count
        
        return {
            'total_assets': total_assets,
            'free_assets': free_assets,
            'total_downloads': total_downloads,
            'active_users': active_users
        }
    except Exception as e:
        return {
            'total_assets': 0,
            'free_assets': 0,
            'total_downloads': 0,
            'active_users': 0
        }

def like_asset(user_id, asset_id):
    try:
        # Vérifier si déjà liké
        existing = supabase.table('likes').select('id').eq('user_id', user_id).eq('asset_id', asset_id).execute()
        
        if existing.data:
            # Retirer le like
            supabase.table('likes').delete().eq('user_id', user_id).eq('asset_id', asset_id).execute()
            return False
        else:
            # Ajouter le like
            supabase.table('likes').insert({'user_id': user_id, 'asset_id': asset_id}).execute()
            return True
    except Exception as e:
        st.error(f"Erreur like: {e}")
        return False

def is_liked(user_id, asset_id):
    try:
        result = supabase.table('likes').select('id').eq('user_id', user_id).eq('asset_id', asset_id).execute()
        return len(result.data) > 0
    except:
        return False

# Initialiser user_id
if 'user_id' not in st.session_state:
    st.session_state.user_id = get_user_id(st.session_state.username)

# ==================== INTERFACE ====================

# Header
col1, col2, col3 = st.columns([2, 4, 2])

with col1:
    st.markdown("### 🎨 **PixelMarket**")

with col2:
    search_input = st.text_input("🔍 Rechercher des photos, vecteurs, icônes...", 
                                  value=st.session_state.search_query,
                                  key="search_main",
                                  label_visibility="collapsed")
    if search_input != st.session_state.search_query:
        st.session_state.search_query = search_input
        st.rerun()

with col3:
    col_btn1, col_btn2, col_btn3 = st.columns(3)
    with col_btn1:
        if st.button("🌓"):
            st.session_state.dark_mode = not st.session_state.dark_mode
            st.rerun()
    with col_btn2:
        if st.button("👤 Admin" if not st.session_state.is_admin else "👤 User"):
            st.session_state.is_admin = not st.session_state.is_admin
            st.rerun()
    with col_btn3:
        if st.button("⭐ Premium"):
            st.info("Passez à Premium pour télécharger sans limites !")

# Hero Section
if not st.session_state.search_query and st.session_state.selected_category == "Tous":
    st.markdown("""
    <div class="hero-section">
        <div class="hero-title">Millions de ressources graphiques gratuites</div>
        <div class="hero-subtitle">Photos, Vecteurs, Icônes, PSD - Tout ce dont vous avez besoin pour vos projets créatifs</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# Filtres
filter_cols = st.columns([2, 2, 2, 2, 2])

CATEGORIES = ["Tous", "Nature", "Business", "Technologie", "Art", "Nourriture", "Voyage", "Mode", "Sport", "Architecture"]
TYPES = ["Tous", "Photo", "Vecteur", "Icône", "Illustration", "PSD"]

with filter_cols[0]:
    selected_cat = st.selectbox("📁 Catégorie", CATEGORIES, index=CATEGORIES.index(st.session_state.selected_category))
    if selected_cat != st.session_state.selected_category:
        st.session_state.selected_category = selected_cat
        st.rerun()

with filter_cols[1]:
    selected_type = st.selectbox("🎨 Type", TYPES, index=TYPES.index(st.session_state.selected_type))
    if selected_type != st.session_state.selected_type:
        st.session_state.selected_type = selected_type
        st.rerun()

with filter_cols[2]:
    premium_filter = st.checkbox("⭐ Premium uniquement", value=st.session_state.show_premium_only)
    if premium_filter != st.session_state.show_premium_only:
        st.session_state.show_premium_only = premium_filter
        st.rerun()

with filter_cols[3]:
    sort_by = st.selectbox("🔽 Trier par", ["Plus récent", "Plus populaire", "Plus téléchargé"])

with filter_cols[4]:
    if st.button("🔄 Réinitialiser"):
        st.session_state.search_query = ""
        st.session_state.selected_category = "Tous"
        st.session_state.selected_type = "Tous"
        st.session_state.show_premium_only = False
        st.rerun()

st.markdown("---")

# Admin Upload
if st.session_state.is_admin:
    with st.expander("➕ Ajouter une nouvelle ressource"):
        col1, col2 = st.columns(2)
        
        with col1:
            upload_file = st.file_uploader("📤 Télécharger", type=['jpg', 'jpeg', 'png'])
            title = st.text_input("📝 Titre*")
            author = st.text_input("👤 Auteur*")
            description = st.text_area("📄 Description")
        
        with col2:
            category = st.selectbox("📁 Catégorie*", CATEGORIES[1:])
            asset_type = st.selectbox("🎨 Type*", TYPES[1:])
            tags = st.text_input("🏷️ Tags (séparés par virgules)")
            is_premium = st.checkbox("⭐ Premium")
            price = st.number_input("💰 Prix (€)", min_value=0.0, value=0.0 if not is_premium else 10.0)
        
        if st.button("✅ Publier", type="primary"):
            if upload_file and title and author:
                image = Image.open(upload_file)
                buffered = BytesIO()
                image.save(buffered, format="PNG")
                img_base64 = base64.b64encode(buffered.getvalue()).decode()
                
                if add_asset(title, author, st.session_state.user_id, description, category, asset_type, is_premium, price, img_base64, tags):
                    st.success("✅ Ressource publiée!")
                    st.rerun()
            else:
                st.error("⚠️ Remplissez tous les champs obligatoires")

# Statistiques
stats = get_stats()
stat_cols = st.columns(4)
stat_cols[0].metric("📊 Ressources", f"{stats['total_assets']:,}")
stat_cols[1].metric("🆓 Gratuit", f"{stats['free_assets']:,}")
stat_cols[2].metric("📥 Téléchargements", f"{stats['total_downloads']:,}")
stat_cols[3].metric("👥 Utilisateurs", f"{stats['active_users']:,}")

st.markdown("---")

# Grille de photos
assets = get_all_assets(
    search=st.session_state.search_query,
    category=st.session_state.selected_category,
    asset_type=st.session_state.selected_type,
    premium_only=st.session_state.show_premium_only
)

if assets:
    st.markdown(f"### 🎨 {len(assets)} résultat(s)")
    
    cols = st.columns(4)
    
    for idx, asset in enumerate(assets):
        with cols[idx % 4]:
            st.markdown('<div class="photo-grid-item">', unsafe_allow_html=True)
            
            # Image
            try:
                img_data = base64.b64decode(asset['image_url'])
                st.image(img_data, use_container_width=True)
            except:
                st.image("https://via.placeholder.com/400x300", use_container_width=True)
            
            # Info
            st.markdown(f"**{asset['title']}**")
            st.markdown(f"<small>Par {asset['author']}</small>", unsafe_allow_html=True)
            
            # Badges et stats
            badge_col1, badge_col2 = st.columns(2)
            with badge_col1:
                if asset['is_premium']:
                    st.markdown('<span class="premium-badge">⭐ PREMIUM</span>', unsafe_allow_html=True)
                else:
                    st.markdown('<span class="free-badge">🆓 GRATUIT</span>', unsafe_allow_html=True)
            
            with badge_col2:
                st.markdown(f"<small>👁️ {asset.get('views', 0)} • ⬇️ {asset.get('downloads', 0)}</small>", unsafe_allow_html=True)
            
            # Boutons
            btn_col1, btn_col2 = st.columns(2)
            
            with btn_col1:
                liked = is_liked(st.session_state.user_id, asset['id'])
                if st.button("❤️" if liked else "🤍", key=f"like_{asset['id']}"):
                    like_asset(st.session_state.user_id, asset['id'])
                    st.rerun()
            
            with btn_col2:
                if asset['is_premium']:
                    if st.button(f"💰 {asset['price']:.2f}€", key=f"buy_{asset['id']}"):
                        st.info("Paiement bientôt disponible!")
                else:
                    if st.button("⬇️ Download", key=f"dl_{asset['id']}"):
                        if download_asset(st.session_state.user_id, asset['id']):
                            try:
                                img_bytes = base64.b64decode(asset['image_url'])
                                st.download_button(
                                    label="📥 Cliquez ici",
                                    data=img_bytes,
                                    file_name=f"{asset['title']}.png",
                                    mime="image/png",
                                    key=f"actual_dl_{asset['id']}"
                                )
                                st.success("✅ Téléchargement!")
                            except:
                                st.error("Erreur téléchargement")
            
            st.markdown('</div>', unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)
else:
    st.info("🔍 Aucun résultat. Ajoutez des ressources en mode Admin!")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; padding: 40px 0;'>
    <h3>🎨 PixelMarket - Plateforme N°1 de ressources graphiques</h3>
    <p>Photos, vecteurs, icônes et illustrations pour vos projets créatifs</p>
    <p style='margin-top: 20px; color: #9ca3af;'>© 2025 PixelMarket. Tous droits réservés.</p>
</div>
""", unsafe_allow_html=True)
