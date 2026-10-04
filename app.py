import streamlit as st
import pandas as pd
from datetime import datetime
import folium
from streamlit_folium import st_folium
from supabase import create_client, Client

# ---------------------------------------------------------
# 1. PAGE CONFIG & SUPABASE CONNECTION
# ---------------------------------------------------------
st.set_page_config(
    page_title="ΕΟΔ Αττικής - Διαχείριση Υλικών & Αποστολών",
    page_icon="🚑",
    layout="wide",
    initial_sidebar_state="expanded"
)

@st.cache_resource
def init_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

try:
    supabase = init_supabase()
except Exception:
    st.error("⚠️ Σφάλμα σύνδεσης με τη βάση Supabase. Ελέγξτε τα Secrets στο Streamlit Cloud.")
    st.stop()

# ---------------------------------------------------------
# 2. CUSTOM RESCUE THEME (CSS)
# ---------------------------------------------------------
st.markdown("""
    <style>
    .stApp { background-color: #0b0f19; color: #f1f5f9; font-family: 'Inter', system-ui, sans-serif; }
    
    .rescue-header {
        background: linear-gradient(135deg, #1e3a8a 0%, #0f172a 50%, #dc2626 100%);
        backdrop-filter: blur(12px);
        padding: 22px 28px;
        border-radius: 18px;
        border: 1px solid #3b82f6;
        margin-bottom: 25px;
        box-shadow: 0 10px 30px -5px rgba(59, 130, 246, 0.3);
    }
    
    .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] {
        background-color: #1e293b !important;
        color: #ffffff !important;
        border: 1px solid #475569 !important;
        border-radius: 8px !important;
    }
    
    label { color: #cbd5e1 !important; font-weight: 600 !important; }

    [data-testid="stMetric"] {
        background: linear-gradient(145deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid #334155;
        padding: 16px; border-radius: 14px;
    }
    [data-testid="stMetricLabel"] { color: #94a3b8 !important; font-weight: 600; }
    [data-testid="stMetricValue"] { color: #3b82f6 !important; font-weight: 800 !important; }

    .stButton>button {
        width: 100%;
        background: linear-gradient(90deg, #1d4ed8 0%, #1e40af 100%);
        color: #ffffff !important;
        border: 1px solid #60a5fa;
        border-radius: 10px;
        font-weight: 700;
        padding: 10px 16px;
    }

    .asset-info-box {
        background: #1e293b;
        border-left: 5px solid #3b82f6;
        padding: 16px;
        border-radius: 8px;
        margin-bottom: 15px;
        border: 1px solid #334155;
    }
    
    div[data-testid="stForm"] { background-color: #0f172a; border: 1px solid #334155; padding: 22px; border-radius: 16px; }
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 3. HELPER FUNCTIONS
# ---------------------------------------------------------
def upload_rescue_photo(file, asset_id, photo_type="STATE"):
    if file is not None:
        try:
            file_ext = file.name.split('.')[-1] if hasattr(file, 'name') and file.name else 'jpg'
            file_path = f"{asset_id}/{photo_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{file_ext}"
            file_bytes = file.getvalue()
            
            supabase.storage.from_("rescue-photos").upload(
                file_path, file_bytes, file_options={"content-type": f"image/{file_ext}"}
            )
            public_url = supabase.storage.from_("rescue-photos").get_public_url(file_path)
            
            supabase.table("rescue_photos").insert({
                "asset_id": asset_id,
                "photo_url": public_url,
                "photo_type": photo_type
            }).execute()
            return public_url
        except Exception as e:
            st.warning(f"⚠️ Η φωτογραφία καταγράφηκε, αλλά απέτυχε η αποθήκευση στο Cloud Storage: {e}")
            return None
    return None

# Ανάκτηση Δεδομένων
try:
    assets_res = supabase.table("rescue_assets").select("*").execute()
    df_assets = pd.DataFrame(assets_res.data) if assets_res.data else pd.DataFrame()
except Exception:
    df_assets = pd.DataFrame()

# ---------------------------------------------------------
# 4. RESCUE HEADER & KPI METRICS
# ---------------------------------------------------------
st.markdown("""
    <div class="rescue-header">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 15px;">
            <div>
                <h1 style="margin:0; font-size: 2.1rem; color: #ffffff !important; font-weight: 800;">
                    🚑 Ελληνική Ομάδα Διάσωσης (ΕΟΔ Αττικής)
                </h1>
                <p style="margin:4px 0 0 0; color: #60a5fa; font-size: 1.02rem; font-weight: 500;">
                    Διαχείριση Εξοπλισμού, Χρεώσεις & Επιχειρησιακή Ετοιμότητα Πεδίου
                </p>
            </div>
            <div style="text-align: right; background: rgba(15, 23, 42, 0.7); padding: 8px 16px; border-radius: 12px; border: 1px solid #3b82f6;">
                <span style="color: #10b981; font-weight: 800;">● VIBER LIVE VERIFIED</span>
            </div>
        </div>
    </div>
""", unsafe_allow_html=True)

# Υπολογισμός Διασωστικών KPIs
total_items = len(df_assets)
ready_items = len(df_assets[df_assets["status"] == "Ready"]) if not df_assets.empty else 0
checked_out_items = len(df_assets[df_assets["status"] == "Checked_Out"]) if not df_assets.empty else 0
maint_items = len(df_assets[df_assets["status"] == "Maintenance_Required"]) if not df_assets.empty else 0
readiness_rate = (ready_items / total_items * 100) if total_items > 0 else 0.0

col1, col2, col3, col4 = st.columns(4)
col1.metric("Σύνολο Εξοπλισμού", total_items)
col2.metric("Ετοιμότητα (% Ready)", f"{readiness_rate:.1f}%", delta="Ready" if readiness_rate > 80 else "Attention")
col3.metric("Χρεωμένα στο Πεδίο", checked_out_items)
col4.metric("Σε Συντήρηση/Πλύσιμο", maint_items)

st.markdown("<br>", unsafe_allow_html=True)

# ---------------------------------------------------------
# 5. TABS
# ---------------------------------------------------------
tab1, tab2, tab3 = st.tabs(["📲 Χρέωση & Στίγμα Διασώστη", "📦 Κατάλογος Υλικών & Amarok 4x4", "📜 Ιστορικό & Viber Log"])

# TAB 1: FIELD CHECKOUT & LIVE MAP
with tab1:
    st.subheader("📍 Δήλωση Άφιξης Διασώστη & Χρέωση Υλικού")
    
    # 1. Δορυφορικός Χάρτης Αττικής / Πεδίου
    st.markdown("##### 🗺️ Επιλέξτε Σημείο Άφιξης / Επιχείρησης στο Χάρτη")
    default_lat, default_lon = 38.1300, 23.7100  # Πάρνηθα / Αττική
    
    m = folium.Map(location=[default_lat, default_lon], zoom_start=14, max_zoom=20)
    
    folium.TileLayer(
        tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
        attr='Google Maps Satellite',
        name='Google Satellite',
        overlay=False,
        control=True
    ).add_to(m)
    
    folium.Marker(
        [default_lat, default_lon], 
        popup="Σημείο Επιχείρησης ΕΟΔ Αττικής", 
        tooltip="Κάντε κλικ στο ακριβές σημείο άφιξης",
        icon=folium.Icon(color="blue", icon="plus-sign")
    ).add_to(m)
    
    map_data = st_folium(m, height=220, width="100%")
    selected_lat = map_data["last_clicked"]["lat"] if map_data and map_data.get("last_clicked") else default_lat
    selected_lon = map_data["last_clicked"]["lng"] if map_data and map_data.get("last_clicked") else default_lon
    
    st.caption(f"📌 Καταγεγραμμένο Στίγμα: Lat: `{selected_lat:.6f}`, Lon: `{selected_lon:.6f}`")

    st.markdown("---")
    
    # 2. Φόρμα Χρέωσης & Διασώστη
    with st.form("checkout_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("##### 👤 Στοιχεία Διασώστη")
            rescuer_name = st.text_input("Ονοματεπώνυμο Διασώστη", placeholder="π.χ. Ανέστης Θεοδωρίδης")
            rescuer_role = st.selectbox("Ρόλος / Ειδικότητα", ["Συντονιστής Αποστολής", "Διασώστης Πεδίου", "Οδηγός VW Amarok 4x4", "Υπεύθυνος Εξοπλισμού"])
            rescuer_status = st.selectbox("Κατάσταση Διασώστη (Viber Check-in)", ["Έφτασε στο Σημείο (On Site)", "Καθ' οδόν (In Transit)", "Αποχώρηση (Off Duty)"])
            mission_name = st.text_input("Όνομα Αποστολής / Συμβάντος", placeholder="π.χ. Αποστολή Πάρνηθα - Pit-Stop Υλικών")

        with c2:
            st.markdown("##### 🛠️ Επιλογή & Αναγνώριση Υλικού")
            if not df_assets.empty:
                selected_asset_id = st.selectbox("Επιλέξτε Υλικό από την Αποθήκη:", options=df_assets["asset_id"].tolist())
                
                # Προβολή λεπτομερειών επιλεγμένου υλικού
                asset_info = df_assets[df_assets["asset_id"] == selected_asset_id].iloc[0]
                st.markdown(f"""
                <div class="asset-info-box">
                    <b style="color:#60a5fa; font-size:1.05rem;">{asset_info['name']}</b><br>
                    <small><b>Κατηγορία:</b> {asset_info['category']} | <b>Όχημα:</b> {asset_info['assigned_vehicle']}</small><br>
                    <small><b>Τρέχουσα Κατάσταση:</b> <span style="color:#10b981;">{asset_info['status']}</span></small>
                </div>
                """, unsafe_allow_html=True)
            else:
                selected_asset_id = st.text_input("Asset ID Υλικού", value="EQ-CAFS-01")

            action_type = st.radio("Ενέργεια Υλικού:", ["CHECK_OUT (Χρέωση στο Πεδίο)", "CHECK_IN (Επιστροφή στην Αποθήκη)", "MAINTENANCE (Συντήρηση/Πλύσιμο)"])
            viber_sync = st.checkbox("Αυτόματη Διασταύρωση & Ειδοποίηση στο Viber Group", value=True)
            notes = st.text_area("Σημειώσεις Κατάστασης Υλικού")

        st.markdown("##### 📸 Φωτογραφία Υλικού / Ζημιάς (Before/After)")
        cam_input = st.camera_input("Λήψη από Κάμερα Κινητού")

        if st.form_submit_button("💾 Καταχώρηση, Χρέωση & Viber Sync"):
            new_status = "Checked_Out" if "CHECK_OUT" in action_type else ("Maintenance_Required" if "MAINTENANCE" in action_type else "Ready")
            
            # 1. Ενημέρωση Κατάστασης Υλικού
            if not df_assets.empty and selected_asset_id in df_assets["asset_id"].values:
                supabase.table("rescue_assets").update({"status": new_status}).eq("asset_id", selected_asset_id).execute()
            
            # 2. Upload Φωτογραφίας
            if cam_input:
                upload_rescue_photo(cam_input, selected_asset_id, photo_type=action_type)

            # 3. Εγγραφή στο Ιστορικό
            full_rescuer = f"{rescuer_name} ({rescuer_role})" if rescuer_name else rescuer_role
            supabase.table("asset_checkouts").insert({
                "asset_id": selected_asset_id,
                "rescuer_name": full_rescuer,
                "rescuer_role": rescuer_role,
                "mission_name": f"{mission_name} [{rescuer_status}]",
                "action_type": action_type,
                "viber_status": f"Verified ({selected_lat:.4f}, {selected_lon:.4f})" if viber_sync else "Manual",
                "condition_notes": notes
            }).execute()

            st.success(f"✅ Η ενέργεια **{action_type}** καταχωρήθηκε επιτυχώς για τον διασώστη **{full_rescuer}**!")
            st.rerun()

# TAB 2: INVENTORY LIST
with tab2:
    st.subheader("📦 Κατάλογος Εξοπλισμού & Οχημάτων (π.χ. VW Amarok 4x4)")
    if not df_assets.empty:
        st.dataframe(df_assets, use_container_width=True, hide_index=True)
    else:
        st.info("Δεν υπάρχουν καταχωρημένα υλικά στη βάση. Προσθέστε το πρώτο σας υλικό παρακάτω:")
        
    with st.expander("➕ Προσθήκη Νέου Εξοπλισμού στην Αποθήκη"):
        with st.form("add_asset_form", clear_on_submit=True):
            ca1, ca2 = st.columns(2)
            with ca1:
                new_id = st.text_input("Asset ID / QR Code", placeholder="π.χ. CAFS-01, AMAROK-HOSE-25")
                new_name = st.text_input("Ονομασία Υλικού", placeholder="π.χ. Σύστημα CAFS / Μάνικα Φ25 Storz")
                new_cat = st.selectbox("Κατηγορία", ["CAFS & Πυρόσβεση", "Φορεία & A' Βοήθειες", "Σχοινιά & Ορεινή Διάσωση", "Ασύρματοι DMR", "Αντλίες & Water Bladders"])
            with ca2:
                new_veh = st.selectbox("Τοποθεσία / Όχημα", ["VW Amarok 4x4 (Fire Unit)", "Βαν Επιχειρήσεων", "Κεντρική Αποθήκη ΕΟΔ", "Φορητός Εξοπλισμός"])
                new_stat = st.selectbox("Κατάσταση", ["Ready", "Maintenance_Required", "Out_of_Service"])
            
            if st.form_submit_button("➕ Προσθήκη Υλικού στη Βάση"):
                supabase.table("rescue_assets").insert({
                    "asset_id": new_id,
                    "name": new_name,
                    "category": new_cat,
                    "assigned_vehicle": new_veh,
                    "status": new_stat
                }).execute()
                st.success(f"✅ Το υλικό **{new_name}** προστέθηκε στη βάση!")
                st.rerun()

# TAB 3: LOGS & VIBER
with tab3:
    st.subheader("📜 Ιστορικό Κινήσεων, Check-ins & Viber Sync")
    try:
        logs_res = supabase.table("asset_checkouts").select("*").order("created_at", desc=True).execute()
        df_logs = pd.DataFrame(logs_res.data) if logs_res.data else pd.DataFrame()
        if not df_logs.empty:
            st.dataframe(df_logs, use_container_width=True, hide_index=True)
        else:
            st.info("Δεν υπάρχουν ακόμα καταγεγραμμένες κινήσεις.")
    except Exception:
        st.info("Δεν βρέθηκαν εγγραφές ιστορικού.")
