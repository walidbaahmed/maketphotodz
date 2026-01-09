import streamlit as st
import sqlite3
from datetime import datetime
import base64
from io import BytesIO
from PIL import Image
import pandas as pd

# Configuration de la page
st.set_page_config(
    page_title="PhotoMarket - Photos Premium",
    page_icon="📸",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personnalisé
if st.session_state.dark_mode:
    # Mode Sombre
    st.markdown("""
    <style>
        .main {
            background: linear-gradient(to bottom right, #0f172a, #581c87, #0f172a);
        }
        .stButton>button {
            width: 100%;
            border-radius: 10px;
            font-weight: bold;
        }
        .photo-card {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 20px;
            border: 1px solid rgba(255, 255, 255, 0.2);
            margin-bottom: 20px;
        }
        .price-tag {
            font-size: 28px;
            font-weight: bold;
            color: #a78bfa;
        }
        h1, h2, h3, p, .stMarkdown {
            color: white !important;
        }
        .dataframe {
            background: rgba(255, 255, 255, 0.1);
            color: white;
        }
        [data-testid="stSidebar"] {
            background: linear-gradient(to bottom, #1e1b4b, #581c87);
        }
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
        }
        .stTabs [data-baseweb="tab"] {
            background-color: rgba(255, 255, 255, 0.1);
            color: white;
            border-radius: 8px;
        }
        .stTabs [aria-selected="true"] {
            background-color: #7c3aed;
        }
    </style>
    """, unsafe_allow_html=True)
else:
    # Mode Clair
    st.markdown("""
    <style>
        .main {
            background: linear-gradient(to bottom right, #f8fafc, #e0e7ff, #fce7f3);
        }
        .stButton>button {
            width: 100%;
            border-radius: 10px;
            font-weight: bold;
        }
        .photo-card {
            background: rgba(255, 255, 255, 0.9);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 20px;
            border: 1px solid rgba(139, 92, 246, 0.3);
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        .price-tag {
            font-size: 28px;
            font-weight: bold;
            color: #7c3aed;
        }
        h1, h2, h3, p, .stMarkdown {
            color: #1e293b !important;
        }
        .dataframe {
            background: white;
            color: #1e293b;
        }
        [data-testid="stSidebar"] {
            background: linear-gradient(to bottom, #f1f5f9, #e0e7ff);
        }
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
        }
        .stTabs [data-baseweb="tab"] {
            background-color: rgba(124, 58, 237, 0.1);
            color: #1e293b;
            border-radius: 8px;
        }
        .stTabs [aria-selected="true"] {
            background-color: #7c3aed;
            color: white;
        }
        .stTextInput input, .stTextArea textarea, .stNumberInput input {
            background-color: white;
            color: #1e293b;
        }
    </style>
    """, unsafe_allow_html=True)

# ==================== BASE DE DONNÉES ====================

def init_database():
    """Initialise la base de données SQLite"""
    conn = sqlite3.connect('photomarket.db', check_same_thread=False)
    cursor = conn.cursor()
    
    # Table des photos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS photos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            photographer TEXT NOT NULL,
            description TEXT,
            price REAL NOT NULL,
            image_data TEXT NOT NULL,
            upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            downloads INTEGER DEFAULT 0,
            revenue REAL DEFAULT 0
        )
    ''')
    
    # Table des utilisateurs
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Table des achats
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS purchases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            photo_id INTEGER,
            purchase_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            amount REAL NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (photo_id) REFERENCES photos(id)
        )
    ''')
    
    # Table du panier
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cart (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            photo_id INTEGER,
            added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (photo_id) REFERENCES photos(id)
        )
    ''')
    
    # Table des transactions
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            total_amount REAL NOT NULL,
            payment_method TEXT,
            transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'completed',
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    conn.commit()
    return conn

# Connexion à la base de données
@st.cache_resource
def get_database_connection():
    return init_database()

conn = get_database_connection()

# ==================== FONCTIONS CRUD ====================

def add_photo(title, photographer, description, price, image_base64):
    """Ajoute une photo à la base de données"""
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO photos (title, photographer, description, price, image_data)
        VALUES (?, ?, ?, ?, ?)
    ''', (title, photographer, description, price, image_base64))
    conn.commit()
    return cursor.lastrowid

def get_all_photos():
    """Récupère toutes les photos"""
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM photos ORDER BY upload_date DESC')
    columns = [description[0] for description in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]

def get_user_id(username):
    """Récupère ou crée un utilisateur"""
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
    result = cursor.fetchone()
    
    if result:
        return result[0]
    else:
        cursor.execute('INSERT INTO users (username) VALUES (?)', (username,))
        conn.commit()
        return cursor.lastrowid

def add_to_cart_db(user_id, photo_id):
    """Ajoute une photo au panier"""
    cursor = conn.cursor()
    # Vérifier si déjà dans le panier
    cursor.execute('SELECT id FROM cart WHERE user_id = ? AND photo_id = ?', (user_id, photo_id))
    if not cursor.fetchone():
        cursor.execute('INSERT INTO cart (user_id, photo_id) VALUES (?, ?)', (user_id, photo_id))
        conn.commit()
        return True
    return False

def get_cart_items(user_id):
    """Récupère les items du panier"""
    cursor = conn.cursor()
    cursor.execute('''
        SELECT p.* FROM photos p
        INNER JOIN cart c ON p.id = c.photo_id
        WHERE c.user_id = ?
    ''', (user_id,))
    columns = [description[0] for description in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]

def clear_cart(user_id):
    """Vide le panier"""
    cursor = conn.cursor()
    cursor.execute('DELETE FROM cart WHERE user_id = ?', (user_id,))
    conn.commit()

def process_purchase(user_id, cart_items):
    """Traite l'achat"""
    cursor = conn.cursor()
    total = sum(item['price'] for item in cart_items)
    
    # Créer la transaction
    cursor.execute('''
        INSERT INTO transactions (user_id, total_amount, payment_method)
        VALUES (?, ?, ?)
    ''', (user_id, total, 'Carte bancaire'))
    transaction_id = cursor.lastrowid
    
    # Enregistrer les achats individuels
    for item in cart_items:
        cursor.execute('''
            INSERT INTO purchases (user_id, photo_id, amount)
            VALUES (?, ?, ?)
        ''', (user_id, item['id'], item['price']))
        
        # Mettre à jour les statistiques de la photo
        cursor.execute('''
            UPDATE photos 
            SET downloads = downloads + 1, revenue = revenue + ?
            WHERE id = ?
        ''', (item['price'], item['id']))
    
    conn.commit()
    clear_cart(user_id)
    return transaction_id

def get_purchased_photos(user_id):
    """Récupère les photos achetées par l'utilisateur"""
    cursor = conn.cursor()
    cursor.execute('''
        SELECT DISTINCT p.* FROM photos p
        INNER JOIN purchases pur ON p.id = pur.photo_id
        WHERE pur.user_id = ?
    ''', (user_id,))
    columns = [description[0] for description in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]

def is_photo_purchased(user_id, photo_id):
    """Vérifie si une photo a été achetée"""
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id FROM purchases WHERE user_id = ? AND photo_id = ?
    ''', (user_id, photo_id))
    return cursor.fetchone() is not None

def get_sales_stats():
    """Récupère les statistiques de ventes"""
    cursor = conn.cursor()
    
    # Stats générales
    cursor.execute('SELECT COUNT(*) FROM photos')
    total_photos = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM purchases')
    total_sales = cursor.fetchone()[0]
    
    cursor.execute('SELECT SUM(amount) FROM purchases')
    total_revenue = cursor.fetchone()[0] or 0
    
    cursor.execute('SELECT COUNT(DISTINCT user_id) FROM purchases')
    total_customers = cursor.fetchone()[0]
    
    return {
        'total_photos': total_photos,
        'total_sales': total_sales,
        'total_revenue': total_revenue,
        'total_customers': total_customers
    }

def get_top_photos():
    """Récupère les photos les plus vendues"""
    cursor = conn.cursor()
    cursor.execute('''
        SELECT title, photographer, downloads, revenue, price
        FROM photos
        WHERE downloads > 0
        ORDER BY downloads DESC
        LIMIT 10
    ''')
    columns = ['Titre', 'Photographe', 'Téléchargements', 'Revenus (€)', 'Prix (€)']
    return pd.DataFrame(cursor.fetchall(), columns=columns)

# ==================== SESSION STATE ====================

if 'username' not in st.session_state:
    st.session_state.username = f"user_{datetime.now().timestamp()}"
if 'user_id' not in st.session_state:
    st.session_state.user_id = get_user_id(st.session_state.username)
if 'is_admin' not in st.session_state:
    st.session_state.is_admin = False
if 'dark_mode' not in st.session_state:
    st.session_state.dark_mode = True

# ==================== INTERFACE ====================

# Sidebar
with st.sidebar:
    st.title("📸 PhotoMarket")
    st.markdown(f"👤 **Utilisateur:** {st.session_state.username[:15]}...")
    st.markdown("---")
    
    # Toggle Admin Mode
    if st.button("🔄 " + ("Mode Client" if st.session_state.is_admin else "Mode Admin")):
        st.session_state.is_admin = not st.session_state.is_admin
        st.rerun()
    
    st.markdown("---")
    
    # Admin: Upload de photos
    if st.session_state.is_admin:
        st.subheader("➕ Ajouter une Photo")
        
        uploaded_file = st.file_uploader("Choisir une image", type=['jpg', 'jpeg', 'png'])
        
        if uploaded_file:
            image = Image.open(uploaded_file)
            st.image(image, caption="Aperçu", use_container_width=True)
            
            title = st.text_input("Titre de la photo*")
            photographer = st.text_input("Photographe*")
            description = st.text_area("Description")
            price = st.number_input("Prix (€)*", min_value=0.0, value=10.0, step=0.5)
            
            if st.button("📤 Publier la photo"):
                if title and photographer:
                    # Convertir l'image en base64
                    buffered = BytesIO()
                    image.save(buffered, format="PNG")
                    img_base64 = base64.b64encode(buffered.getvalue()).decode()
                    
                    add_photo(title, photographer, description, price, img_base64)
                    st.success("✅ Photo publiée avec succès!")
                    st.rerun()
                else:
                    st.error("⚠️ Veuillez remplir tous les champs obligatoires")
        
        st.markdown("---")
        st.subheader("📊 Statistiques Admin")
        stats = get_sales_stats()
        st.metric("Photos totales", stats['total_photos'])
        st.metric("Ventes totales", stats['total_sales'])
        st.metric("Revenus", f"{stats['total_revenue']:.2f}€")
        st.metric("Clients", stats['total_customers'])
    
    # Panier
    st.markdown("---")
    cart_items = get_cart_items(st.session_state.user_id)
    st.subheader(f"🛒 Panier ({len(cart_items)})")
    
    if cart_items:
        total = sum(p['price'] for p in cart_items)
        
        for photo in cart_items:
            with st.container():
                st.markdown(f"**{photo['title']}**")
                st.markdown(f"{photo['price']:.2f}€")
                st.markdown("---")
        
        st.markdown(f"### Total: {total:.2f}€")
        
        if st.button("💳 Payer maintenant", type="primary"):
            transaction_id = process_purchase(st.session_state.user_id, cart_items)
            st.success(f"✅ Paiement réussi! Transaction #{transaction_id}")
            st.rerun()
    else:
        st.info("Votre panier est vide")

# Main content
st.title("🎨 Photos Premium de Haute Qualité")
st.markdown("### Téléchargement instantané après paiement")

# Onglets
if st.session_state.is_admin:
    tab1, tab2, tab3 = st.tabs(["📷 Galerie", "📊 Statistiques", "💰 Transactions"])
else:
    tab1, tab2 = st.tabs(["📷 Galerie", "📥 Mes Achats"])

with tab1:
    photos = get_all_photos()
    
    if not photos:
        st.info("📷 Aucune photo disponible pour le moment. " + 
                ("Utilisez le panneau latéral pour ajouter des photos." if st.session_state.is_admin 
                 else "Revenez bientôt!"))
    else:
        # Affichage en grille
        cols = st.columns(3)
        
        for idx, photo in enumerate(photos):
            with cols[idx % 3]:
                with st.container():
                    st.markdown('<div class="photo-card">', unsafe_allow_html=True)
                    
                    # Image
                    img_data = base64.b64decode(photo['image_data'])
                    st.image(img_data, use_container_width=True)
                    
                    # Titre et photographe
                    st.markdown(f"### {photo['title']}")
                    st.markdown(f"*Par {photo['photographer']}*")
                    
                    # Description
                    if photo['description']:
                        st.markdown(photo['description'])
                    
                    # Statistiques pour admin
                    if st.session_state.is_admin:
                        st.markdown(f"📊 {photo['downloads']} ventes • {photo['revenue']:.2f}€ revenus")
                    
                    # Prix et actions
                    col1, col2 = st.columns([1, 1])
                    with col1:
                        st.markdown(f'<div class="price-tag">{photo["price"]:.2f}€</div>', 
                                  unsafe_allow_html=True)
                    
                    with col2:
                        if is_photo_purchased(st.session_state.user_id, photo['id']):
                            st.success("✅ Achetée")
                            # Bouton de téléchargement
                            img_bytes = base64.b64decode(photo['image_data'])
                            st.download_button(
                                label="⬇️ Télécharger",
                                data=img_bytes,
                                file_name=f"{photo['title']}.png",
                                mime="image/png",
                                key=f"download_{photo['id']}"
                            )
                        else:
                            if st.button("🛒 Ajouter", key=f"add_{photo['id']}"):
                                if add_to_cart_db(st.session_state.user_id, photo['id']):
                                    st.success("✓ Ajouté au panier!")
                                    st.rerun()
                                else:
                                    st.info("Déjà dans le panier")
                    
                    st.markdown('</div>', unsafe_allow_html=True)

if st.session_state.is_admin:
    with tab2:
        st.subheader("📈 Top 10 des photos les plus vendues")
        top_photos = get_top_photos()
        if not top_photos.empty:
            st.dataframe(top_photos, use_container_width=True, hide_index=True)
        else:
            st.info("Aucune vente enregistrée")
    
    with tab3:
        st.subheader("💰 Historique des transactions")
        cursor = conn.cursor()
        cursor.execute('''
            SELECT t.id, u.username, t.total_amount, t.payment_method, 
                   t.transaction_date, t.status
            FROM transactions t
            JOIN users u ON t.user_id = u.id
            ORDER BY t.transaction_date DESC
        ''')
        transactions = cursor.fetchall()
        
        if transactions:
            df = pd.DataFrame(transactions, 
                            columns=['ID', 'Utilisateur', 'Montant (€)', 'Paiement', 'Date', 'Statut'])
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("Aucune transaction")
else:
    with tab2:
        st.subheader("📥 Mes photos achetées")
        purchased = get_purchased_photos(st.session_state.user_id)
        
        if purchased:
            cols = st.columns(3)
            for idx, photo in enumerate(purchased):
                with cols[idx % 3]:
                    img_data = base64.b64decode(photo['image_data'])
                    st.image(img_data, use_container_width=True)
                    st.markdown(f"**{photo['title']}**")
                    img_bytes = base64.b64decode(photo['image_data'])
                    st.download_button(
                        label="⬇️ Télécharger",
                        data=img_bytes,
                        file_name=f"{photo['title']}.png",
                        mime="image/png",
                        key=f"my_download_{photo['id']}"
                    )
        else:
            st.info("Vous n'avez pas encore acheté de photos")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #a78bfa;'>
    <p>📸 PhotoMarket - Plateforme de vente de photos premium avec base de données SQLite</p>
    <p>Tous droits réservés © 2025</p>
</div>
""", unsafe_allow_html=True)
