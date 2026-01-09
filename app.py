import streamlit as st
import json
from datetime import datetime
import base64
from io import BytesIO
from PIL import Image

# Configuration de la page
st.set_page_config(
    page_title="PhotoMarket - Photos Premium",
    page_icon="📸",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personnalisé
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
    h1, h2, h3, p {
        color: white !important;
    }
</style>
""", unsafe_allow_html=True)

# Initialisation de la session state
if 'photos' not in st.session_state:
    st.session_state.photos = []
if 'cart' not in st.session_state:
    st.session_state.cart = []
if 'purchased' not in st.session_state:
    st.session_state.purchased = []
if 'is_admin' not in st.session_state:
    st.session_state.is_admin = False

def add_to_cart(photo):
    if photo['id'] not in [p['id'] for p in st.session_state.cart]:
        if photo['id'] not in st.session_state.purchased:
            st.session_state.cart.append(photo)
            st.success(f"✓ {photo['title']} ajouté au panier!")

def remove_from_cart(photo_id):
    st.session_state.cart = [p for p in st.session_state.cart if p['id'] != photo_id]

def process_payment():
    total = sum(p['price'] for p in st.session_state.cart)
    st.session_state.purchased.extend([p['id'] for p in st.session_state.cart])
    st.session_state.cart = []
    st.success(f"✅ Paiement de {total:.2f}€ réussi! Vous pouvez maintenant télécharger vos photos.")

def image_to_base64(image):
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode()

# Sidebar
with st.sidebar:
    st.title("📸 PhotoMarket")
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
                    photo_data = {
                        'id': str(datetime.now().timestamp()),
                        'title': title,
                        'photographer': photographer,
                        'description': description,
                        'price': price,
                        'image': image_to_base64(image),
                        'upload_date': datetime.now().isoformat()
                    }
                    st.session_state.photos.append(photo_data)
                    st.success("✅ Photo publiée avec succès!")
                    st.rerun()
                else:
                    st.error("⚠️ Veuillez remplir tous les champs obligatoires")
    
    # Panier
    st.markdown("---")
    st.subheader(f"🛒 Panier ({len(st.session_state.cart)})")
    
    if st.session_state.cart:
        total = sum(p['price'] for p in st.session_state.cart)
        
        for photo in st.session_state.cart:
            with st.container():
                st.markdown(f"**{photo['title']}**")
                st.markdown(f"{photo['price']:.2f}€")
                if st.button("❌ Retirer", key=f"remove_{photo['id']}"):
                    remove_from_cart(photo['id'])
                    st.rerun()
                st.markdown("---")
        
        st.markdown(f"### Total: {total:.2f}€")
        
        if st.button("💳 Payer maintenant", type="primary"):
            process_payment()
            st.rerun()
    else:
        st.info("Votre panier est vide")
    
    # Statistiques
    st.markdown("---")
    st.metric("Photos disponibles", len(st.session_state.photos))
    st.metric("Photos achetées", len(st.session_state.purchased))

# Main content
st.title("🎨 Photos Premium de Haute Qualité")
st.markdown("### Téléchargement instantané après paiement")

if not st.session_state.photos:
    st.info("📷 Aucune photo disponible pour le moment. " + 
            ("Utilisez le panneau latéral pour ajouter des photos." if st.session_state.is_admin 
             else "Revenez bientôt!"))
else:
    # Affichage en grille
    cols = st.columns(3)
    
    for idx, photo in enumerate(st.session_state.photos):
        with cols[idx % 3]:
            with st.container():
                st.markdown('<div class="photo-card">', unsafe_allow_html=True)
                
                # Image
                img_data = base64.b64decode(photo['image'])
                st.image(img_data, use_container_width=True)
                
                # Titre et photographe
                st.markdown(f"### {photo['title']}")
                st.markdown(f"*Par {photo['photographer']}*")
                
                # Description
                if photo['description']:
                    st.markdown(photo['description'])
                
                # Prix et actions
                col1, col2 = st.columns([1, 1])
                with col1:
                    st.markdown(f'<div class="price-tag">{photo["price"]:.2f}€</div>', 
                              unsafe_allow_html=True)
                
                with col2:
                    if photo['id'] in st.session_state.purchased:
                        st.success("✅ Achetée")
                        # Bouton de téléchargement
                        img_bytes = base64.b64decode(photo['image'])
                        st.download_button(
                            label="⬇️ Télécharger",
                            data=img_bytes,
                            file_name=f"{photo['title']}.png",
                            mime="image/png",
                            key=f"download_{photo['id']}"
                        )
                    else:
                        if st.button("🛒 Ajouter", key=f"add_{photo['id']}"):
                            add_to_cart(photo)
                            st.rerun()
                
                st.markdown('</div>', unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #a78bfa;'>
    <p>📸 PhotoMarket - Plateforme de vente de photos premium</p>
    <p>Tous droits réservés © 2025</p>
</div>
""", unsafe_allow_html=True)
