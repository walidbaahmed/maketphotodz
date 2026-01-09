import streamlit as st
import sqlite3
from datetime import datetime
import base64
from io import BytesIO
from PIL import Image
import pandas as pd

# Configuration de la page
st.set_page_config(
    page_title="PixelMarket - Stock Photos & Graphics",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="collapsed"
)

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

# CSS personnalisé - Style Freepik
if st.session_state.dark_mode:
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        
        * { font-family: 'Inter', sans-serif; }
        .main { background: #0a0e27; }
        .stButton>button {
            border-radius: 8px;
            font-weight: 600;
            transition: all 0.3s;
        }
        .hero-section {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 60px 20px;
            border-radius: 20px;
            text-align: center;
            margin-bottom: 40px;
        }
        .hero-title {
            font-size: 48px;
            font-weight: 700;
            color: white;
            margin-bottom: 20px;
        }
        .hero-subtitle {
            font-size: 20px;
            color: rgba(255,255,255,0.9);
            margin-bottom: 30px;
        }
        .category-card {
            background: rgba(255,255,255,0.05);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 12px;
            padding: 20px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s;
        }
        .category-card:hover {
            transform: translateY(-5px);
            border-color: #667eea;
            background: rgba(102,126,234,0.1);
        }
        .photo-grid-item {
            background: rgba(255,255,255,0.05);
            border-radius: 12px;
            overflow: hidden;
            transition: all 0.3s;
            cursor: pointer;
            border: 1px solid rgba(255,255,255,0.1);
        }
        .photo-grid-item:hover {
            transform: translateY(-8px);
            box-shadow: 0 20px 40px rgba(102,126,234,0.3);
        }
        .premium-badge {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
        }
        .free-badge {
            background: #10b981;
            color: white;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
        }
        h1, h2, h3, p { color: white !important; }
        .search-bar {
            background: rgba(255,255,255,0.1);
            border: 2px solid rgba(255,255,255,0.2);
            border-radius: 50px;
            padding: 15px 30px;
            font-size: 16px;
            color: white;
        }
    </style>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        
        * { font-family: 'Inter', sans-serif; }
        .main { background: #f8f9fa; }
        .stButton>button {
            border-radius: 8px;
            font-weight: 600;
            transition: all 0.3s;
        }
        .hero-section {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 60px 20px;
            border-radius: 20px;
            text-align: center;
            margin-bottom: 40px;
        }
        .hero-title {
            font-size: 48px;
            font-weight: 700;
            color: white;
            margin-bottom: 20px;
        }
        .hero-subtitle {
            font-size: 20px;
            color: rgba(255,255,255,0.9);
            margin-bottom: 30px;
        }
        .category-card {
            background: white;
            border: 2px solid #e5e7eb;
            border-radius: 12px;
            padding: 20px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s;
        }
        .category-card:hover {
            transform: translateY(-5px);
            border-color: #667eea;
            box-shadow: 0 10px 30px rgba(102,126,234,0.2);
        }
        .photo-grid-item {
            background: white;
            border-radius: 12px;
            overflow: hidden;
            transition: all 0.3s;
            cursor: pointer;
            border: 1px solid #e5e7eb;
        }
        .photo-grid-item:hover {
            transform: translateY(-8px);
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        }
        .premium-badge {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
        }
        .free-badge {
            background: #10b981;
            color: white;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
        }
        h1, h2, h3 { color: #1f2937 !important; }
        p { color: #4b5563 !important; }
    </style>
    """, unsafe_allow_html=True)

# ==================== BASE DE DONNÉES ====================

def init_database():
    conn = sqlite3.connect('pixelmarket.db', check_same_thread=False)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS assets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            description TEXT,
            category TEXT,
            asset_type TEXT,
            is_premium BOOLEAN DEFAULT 0,
            price REAL DEFAULT 0,
            image_data TEXT NOT NULL,
            tags TEXT,
            upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            downloads INTEGER DEFAULT 0,
            likes INTEGER DEFAULT 0,
            views INTEGER DEFAULT 0
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT,
            is_premium BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS downloads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            asset_id INTEGER,
            download_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (asset_id) REFERENCES assets(id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS collections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    conn.commit()
    return conn

@st.cache_resource
def get_database_connection():
    return init_database()

conn = get_database_connection()

# ==================== FONCTIONS ====================

def get_user_id(username):
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
    result = cursor.fetchone()
    if result:
        return result[0]
    else:
        cursor.execute('INSERT INTO users (username) VALUES (?)', (username,))
        conn.commit()
        return cursor.lastrowid

def add_asset(title, author, description, category, asset_type, is_premium, price, image_base64, tags):
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO assets (title, author, description, category, asset_type, is_premium, price, image_data, tags)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (title, author, description, category, asset_type, is_premium, price, image_base64, tags))
    conn.commit()

def get_all_assets(search="", category="Tous", asset_type="Tous", premium_only=False):
    cursor = conn.cursor()
    query = 'SELECT * FROM assets WHERE 1=1'
    params = []
    
    if search:
        query += ' AND (title LIKE ? OR tags LIKE ? OR author LIKE ?)'
        search_param = f'%{search}%'
        params.extend([search_param, search_param, search_param])
    
    if category != "Tous":
        query += ' AND category = ?'
        params.append(category)
    
    if asset_type != "Tous":
        query += ' AND asset_type = ?'
        params.append(asset_type)
    
    if premium_only:
        query += ' AND is_premium = 1'
    
    query += ' ORDER BY upload_date DESC'
    
    cursor.execute(query, params)
    columns = [description[0] for description in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]

def download_asset(user_id, asset_id):
    cursor = conn.cursor()
    cursor.execute('INSERT INTO downloads (user_id, asset_id) VALUES (?, ?)', (user_id, asset_id))
    cursor.execute('UPDATE assets SET downloads = downloads + 1 WHERE id = ?', (asset_id,))
    conn.commit()

def increment_views(asset_id):
    cursor = conn.cursor()
    cursor.execute('UPDATE assets SET views = views + 1 WHERE id = ?', (asset_id,))
    conn.commit()

def get_stats():
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM assets')
    total_assets = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM assets WHERE is_premium = 0')
    free_assets = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM downloads')
    total_downloads = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(DISTINCT user_id) FROM downloads')
    active_users = cursor.fetchone()[0]
    
    return {
        'total_assets': total_assets,
        'free_assets': free_assets,
        'total_downloads': total_downloads,
        'active_users': active_users
    }

# Initialiser user_id
if 'user_id' not in st.session_state:
    st.session_state.user_id = get_user_id(st.session_state.username)

# ==================== INTERFACE ====================

# Header avec navigation
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
        <div class="hero-subtitle">Photos, Vecteurs, Icônes, PSD, IA - Tout ce dont vous avez besoin pour vos projets créatifs</div>
    </div>
    """, unsafe_allow_html=True)

# Filtres et Catégories
st.markdown("---")

# Barre de filtres
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
    if st.button("🔄 Réinitialiser filtres"):
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
            upload_file = st.file_uploader("📤 Télécharger une image", type=['jpg', 'jpeg', 'png', 'svg'])
            title = st.text_input("📝 Titre*")
            author = st.text_input("👤 Auteur*")
            description = st.text_area("📄 Description")
        
        with col2:
            category = st.selectbox("📁 Catégorie*", CATEGORIES[1:])
            asset_type = st.selectbox("🎨 Type*", TYPES[1:])
            tags = st.text_input("🏷️ Tags (séparés par des virgules)")
            is_premium = st.checkbox("⭐ Premium")
            price = st.number_input("💰 Prix (€)", min_value=0.0, value=0.0 if not is_premium else 10.0, step=0.5)
        
        if st.button("✅ Publier la ressource", type="primary"):
            if upload_file and title and author:
                image = Image.open(upload_file)
                buffered = BytesIO()
                image.save(buffered, format="PNG")
                img_base64 = base64.b64encode(buffered.getvalue()).decode()
                
                add_asset(title, author, description, category, asset_type, is_premium, price, img_base64, tags)
                st.success("✅ Ressource publiée avec succès!")
                st.rerun()
            else:
                st.error("⚠️ Veuillez remplir tous les champs obligatoires")

# Statistiques
stats = get_stats()
stat_cols = st.columns(4)
stat_cols[0].metric("📊 Ressources totales", f"{stats['total_assets']:,}")
stat_cols[1].metric("🆓 Gratuit", f"{stats['free_assets']:,}")
stat_cols[2].metric("📥 Téléchargements", f"{stats['total_downloads']:,}")
stat_cols[3].metric("👥 Utilisateurs actifs", f"{stats['active_users']:,}")

st.markdown("---")

# Grille de photos style Freepik
assets = get_all_assets(
    search=st.session_state.search_query,
    category=st.session_state.selected_category,
    asset_type=st.session_state.selected_type,
    premium_only=st.session_state.show_premium_only
)

if assets:
    st.markdown(f"### 🎨 {len(assets)} résultat(s) trouvé(s)")
    
    # Grille 4 colonnes
    cols = st.columns(4)
    
    for idx, asset in enumerate(assets):
        with cols[idx % 4]:
            with st.container():
                st.markdown('<div class="photo-grid-item">', unsafe_allow_html=True)
                
                # Image
                img_data = base64.b64decode(asset['image_data'])
                st.image(img_data, use_container_width=True)
                
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
                    st.markdown(f"<small>👁️ {asset['views']} • ⬇️ {asset['downloads']}</small>", unsafe_allow_html=True)
                
                # Bouton téléchargement
                if asset['is_premium']:
                    st.button(f"💰 {asset['price']:.2f}€", key=f"buy_{asset['id']}", use_container_width=True)
                else:
                    if st.button("⬇️ Télécharger", key=f"dl_{asset['id']}", use_container_width=True):
                        download_asset(st.session_state.user_id, asset['id'])
                        img_bytes = base64.b64decode(asset['image_data'])
                        st.download_button(
                            label="📥 Cliquez ici pour télécharger",
                            data=img_bytes,
                            file_name=f"{asset['title']}.png",
                            mime="image/png",
                            key=f"actual_dl_{asset['id']}"
                        )
                        st.success("✅ Téléchargement commencé!")
                
                st.markdown('</div>', unsafe_allow_html=True)
                st.markdown("<br>", unsafe_allow_html=True)
else:
    st.info("🔍 Aucun résultat trouvé. Essayez d'autres mots-clés ou ajustez les filtres.")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; padding: 40px 0;'>
    <h3>🎨 PixelMarket - La plateforme N°1 de ressources graphiques</h3>
    <p>Millions de photos, vecteurs, icônes et illustrations pour vos projets créatifs</p>
    <p style='margin-top: 20px; color: #9ca3af;'>© 2025 PixelMarket. Tous droits réservés.</p>
</div>
""", unsafe_allow_html=True)
